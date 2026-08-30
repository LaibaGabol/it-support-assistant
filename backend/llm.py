"""Azure OpenAI client and the agent decision call."""
import json
import os

from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

_client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2024-08-01-preview",
)

_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# Returned when the model produces something that isn't usable JSON, so the
# /chat endpoint degrades to escalation rather than crashing.
_FALLBACK = {
    "action": "escalate",
    "message": (
        "I'm having trouble processing this request right now, so I'm escalating "
        "it to a human IT support agent who can help you further."
    ),
    "reasoning": "LLM returned invalid JSON; falling back to escalation.",
    "kb_sources": [],
}


def get_agent_decision(system_prompt: str, history: list[dict], kb_context: str) -> dict:
    """Ask the model for its next decision and return it as a dict.

    Builds: [system prompt] + [system message with KB context] + conversation history.
    Always returns a dict; on invalid JSON it returns a safe escalation fallback.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "system",
            "content": (
                "KNOWLEDGE BASE CONTEXT (use ONLY this to answer; if it is empty "
                "or irrelevant, ask a follow-up or escalate):\n\n" + kb_context
            ),
        },
    ]
    messages.extend(history)

    response = _client.chat.completions.create(
        model=_DEPLOYMENT,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=0.3,
    )

    content = response.choices[0].message.content

    try:
        decision = json.loads(content)
        if not isinstance(decision, dict):
            raise ValueError("Parsed JSON is not an object")
        return decision
    except (json.JSONDecodeError, ValueError, TypeError):
        return dict(_FALLBACK)
