import os
import uuid

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

load_dotenv()

# Imported after load_dotenv() because these modules build Azure/Jira clients
# and read configuration from environment variables at import time.
from rag import retrieve_context  # noqa: E402
from db import conversations, config, get_settings  # noqa: E402
from prompts import build_system_prompt  # noqa: E402
from llm import get_agent_decision  # noqa: E402
from jira_client import create_jira_ticket  # noqa: E402
from storage import (  # noqa: E402
    upload_screenshot,
    download_blob_by_url,
    container_client,
    _guess_content_type,
)
from models import EnvironmentInfo  # noqa: E402
from azure.cosmos import exceptions as cosmos_exceptions  # noqa: E402
from azure.core.exceptions import ResourceNotFoundError  # noqa: E402

app = FastAPI(title="IT Support Assistant API")

# CORS: in production, ALLOWED_ORIGINS is set to the explicit Static Web App
# URLs (comma-separated). Locally it defaults to "*" for convenience.
_allowed = os.getenv("ALLOWED_ORIGINS", "*").strip()
_allow_origins = ["*"] if _allowed == "*" else [
    o.strip() for o in _allowed.split(",") if o.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/test-retrieval")
def test_retrieval(query: str):
    return retrieve_context(query)


@app.post("/upload-screenshot")
async def upload_screenshot_endpoint(file: UploadFile = File(...)):
    contents = await file.read()
    url = upload_screenshot(contents, file.filename or "screenshot.png")
    return {"screenshot_url": url}


class ChatRequest(BaseModel):
    conversation_id: str | None = None
    message: str
    environment: EnvironmentInfo | None = None
    screenshot_url: str | None = None


def _format_kb_context(chunks: list[dict]) -> str:
    """Turn retrieve_context() output into a labeled context string."""
    if not chunks:
        return "(no relevant knowledge base articles were found)"
    parts = []
    for c in chunks:
        source = c.get("source") or "Unknown source"
        content = c.get("content") or ""
        parts.append(f"[Source: {source}]\n{content}")
    return "\n\n".join(parts)


@app.post("/chat")
def chat(req: ChatRequest):
    # 1. Load or create the conversation.
    if req.conversation_id:
        try:
            convo = conversations.read_item(
                item=req.conversation_id, partition_key=req.conversation_id
            )
        except cosmos_exceptions.CosmosResourceNotFoundError:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation '{req.conversation_id}' not found",
            )
    else:
        settings = get_settings()
        convo = {
            "id": str(uuid.uuid4()),
            "depth": settings.get("depth", 3),
            "max_followups": settings.get("max_followups", 3),
            "followup_count": 0,
            "status": "open",
            "ticket_id": None,
            "messages": [],
        }

    # 1b. Store client-supplied environment / screenshot on the conversation.
    if req.environment is not None:
        convo["environment"] = req.environment.model_dump()
    if req.screenshot_url is not None:
        convo["screenshot_url"] = req.screenshot_url

    # 2. Append the user's message.
    convo["messages"].append({"role": "user", "content": req.message})

    # 3. Retrieve KB context for the user's message.
    kb_chunks = retrieve_context(req.message)
    kb_context = _format_kb_context(kb_chunks)

    # Track the KB sources seen across the conversation (deduped) for the ticket.
    existing_sources = convo.get("kb_sources", [])
    new_sources = [c.get("source") for c in kb_chunks if c.get("source")]
    convo["kb_sources"] = list(dict.fromkeys(existing_sources + new_sources))

    # 4. Build the system prompt for this conversation's depth.
    system_prompt = build_system_prompt(convo["depth"], convo["max_followups"])

    # 5. Ask the model for its decision.
    decision = get_agent_decision(system_prompt, convo["messages"], kb_context)
    action = decision.get("action", "escalate")
    message = decision.get("message", "")

    # 6. HARD BACKSTOP: never exceed the follow-up budget, regardless of the
    # model's decision. This is enforced in code, not just the prompt.
    if action == "ask_followup" and convo["followup_count"] >= convo["max_followups"]:
        action = "escalate"
        message = (
            "I've asked all the follow-up questions I can for this issue, so I'm "
            "escalating it to a human IT support agent."
        )

    # 7. Append the assistant's message.
    convo["messages"].append({"role": "assistant", "content": message})

    # 8. Apply action side effects.
    if action == "ask_followup":
        convo["followup_count"] += 1
    elif action == "answer":
        convo["status"] = "resolved"
    elif action == "escalate":
        convo["status"] = "escalated"
        # Capture the model's suggested priority (default Medium) before ticketing.
        convo["priority"] = decision.get("priority") or "Medium"
        ticket_key = create_jira_ticket(convo)
        convo["ticket_id"] = ticket_key
        message = f"{message}\n\nA support ticket has been created: {ticket_key}"

    # 9. Persist the conversation.
    conversations.upsert_item(convo)

    # 10. Respond.
    return {
        "conversation_id": convo["id"],
        "action": action,
        "message": message,
    }


# ---------------------------------------------------------------------------
# Admin backoffice endpoints
# ---------------------------------------------------------------------------


class ConfigUpdate(BaseModel):
    system_prompt: str | None = None
    depth: int | None = None
    max_followups: int | None = None


@app.get("/admin/config")
def admin_get_config():
    """Return the current 'settings' document from the config container."""
    return get_settings()


@app.put("/admin/config")
def admin_update_config(update: ConfigUpdate):
    """Merge provided fields into the settings document and persist it."""
    settings = get_settings()
    # Drop Cosmos system metadata (_rid/_self/_etag/_ts/...) before re-upserting.
    settings = {k: v for k, v in settings.items() if not k.startswith("_")}
    # Only fields the client actually sent are merged in.
    changes = update.model_dump(exclude_unset=True)
    settings.update(changes)
    settings["id"] = "settings"  # keep the fixed document id
    config.upsert_item(settings)
    return settings


@app.get("/admin/conversations")
def admin_list_conversations():
    """Lightweight list of all conversations (no full message history)."""
    query = (
        "SELECT c.id, c.status, ARRAY_LENGTH(c.messages) AS message_count, "
        "c.ticket_id, c.depth FROM c"
    )
    return list(
        conversations.query_items(query=query, enable_cross_partition_query=True)
    )


@app.get("/admin/conversations/{conversation_id}")
def admin_get_conversation(conversation_id: str):
    """Return the full conversation document for one conversation."""
    try:
        return conversations.read_item(
            item=conversation_id, partition_key=conversation_id
        )
    except cosmos_exceptions.CosmosResourceNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation '{conversation_id}' not found",
        )


@app.get("/admin/screenshot-proxy")
def admin_screenshot_proxy(url: str):
    """Stream a screenshot image from the (private) blob container.

    Lets the admin UI display screenshots without making the container public.
    Only URLs belonging to our own screenshots container are served.
    """
    if not url.startswith(container_client.url):
        raise HTTPException(
            status_code=400,
            detail="URL does not belong to the screenshots storage container",
        )
    try:
        data = download_blob_by_url(url)
    except ResourceNotFoundError:
        raise HTTPException(status_code=404, detail="Screenshot blob not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return Response(content=data, media_type=_guess_content_type(url))
