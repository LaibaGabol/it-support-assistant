"""Jira ticket creation and screenshot attachment for escalated conversations."""
import logging
import os

import requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from config_constants import TEST_USER

load_dotenv()

logger = logging.getLogger(__name__)


def _jira_auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(os.getenv("JIRA_EMAIL"), os.getenv("JIRA_API_TOKEN"))


def _para(text: str) -> dict:
    """An ADF paragraph. ADF text nodes cannot be empty or contain raw newlines."""
    return {"type": "paragraph", "content": [{"type": "text", "text": text or " "}]}


def _heading(text: str, level: int = 3) -> dict:
    return {
        "type": "heading",
        "attrs": {"level": level},
        "content": [{"type": "text", "text": text}],
    }


def _build_description(convo: dict) -> dict:
    """Build the full Atlassian Document Format description for the ticket."""
    priority = convo.get("priority") or "Medium"
    followup_count = convo.get("followup_count", 0)
    env = convo.get("environment") or {}
    screenshot_url = convo.get("screenshot_url")
    # Deduplicate KB sources, preserving order; omit the section gracefully if none.
    kb_sources = list(dict.fromkeys(convo.get("kb_sources", []) or []))

    content: list[dict] = []

    # Reporting user (placeholder identity; real auth is out of scope).
    content.append(_heading("Reported By"))
    content.append(_para(f"Name: {TEST_USER['name']}"))
    content.append(_para(f"Email: {TEST_USER['email']}"))
    content.append(_para(f"Department: {TEST_USER['department']}"))

    # Escalation summary.
    content.append(_heading("Escalation Details"))
    content.append(_para(f"Suggested Priority: {priority}"))
    content.append(_para(f"Troubleshooting steps attempted (follow-ups): {followup_count}"))

    # KB references (only if we tracked any).
    if kb_sources:
        content.append(_heading("Knowledge Base References"))
        for src in kb_sources:
            content.append(_para(f"- {src}"))

    # Browser / environment info; "N/A" for anything missing.
    content.append(_heading("Environment"))
    content.append(_para(f"User Agent: {env.get('user_agent') or 'N/A'}"))
    content.append(_para(f"OS: {env.get('os') or 'N/A'}"))
    content.append(_para(f"Screen Resolution: {env.get('screen_resolution') or 'N/A'}"))
    content.append(_para(f"Viewport: {env.get('viewport') or 'N/A'}"))
    content.append(_para(f"Language: {env.get('language') or 'N/A'}"))
    content.append(_para(f"Timestamp: {env.get('timestamp') or 'N/A'}"))

    # Screenshot reference (the actual file is also attached when available).
    content.append(_heading("Screenshot"))
    content.append(_para(screenshot_url if screenshot_url else "Not provided"))

    # Full conversation transcript.
    content.append(_heading("Conversation Transcript"))
    messages = convo.get("messages", [])
    if not messages:
        content.append(_para("(no messages)"))
    for m in messages:
        role = m.get("role", "unknown").upper()
        content.append(_para(f"{role}: {m.get('content', '')}"))

    return {"type": "doc", "version": 1, "content": content}


def create_jira_ticket(convo: dict) -> str:
    """Create a Jira issue for an escalated conversation and return its key.

    Builds a full description (transcript, follow-up count, KB refs, user info,
    priority, environment, screenshot reference), sets the priority field, and
    attaches the screenshot image when one is present. Raises on any HTTP/
    credential failure during issue creation so the caller knows it failed.
    """
    base_url = os.getenv("JIRA_BASE_URL")
    email = os.getenv("JIRA_EMAIL")
    token = os.getenv("JIRA_API_TOKEN")
    project_key = os.getenv("JIRA_PROJECT_KEY")

    missing = [
        name
        for name, val in [
            ("JIRA_BASE_URL", base_url),
            ("JIRA_EMAIL", email),
            ("JIRA_API_TOKEN", token),
            ("JIRA_PROJECT_KEY", project_key),
        ]
        if not val
    ]
    if missing:
        msg = f"Cannot create Jira ticket, missing credentials: {', '.join(missing)}"
        logger.error(msg)
        raise RuntimeError(msg)

    convo_id = convo.get("id", "")
    priority = convo.get("priority") or "Medium"
    auth = _jira_auth()

    url = f"{base_url.rstrip('/')}/rest/api/3/issue"
    payload = {
        "fields": {
            "project": {"key": project_key},
            "summary": f"IT Support Escalation - {convo_id[:8]}",
            "description": _build_description(convo),
            "issuetype": {"name": "Task"},
            "priority": {"name": priority},
        }
    }

    try:
        resp = requests.post(
            url,
            json=payload,
            auth=auth,
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            timeout=30,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        body = getattr(exc.response, "text", "") if getattr(exc, "response", None) is not None else ""
        logger.error("Jira ticket creation failed: %s | response body: %s", exc, body)
        raise

    issue_key = resp.json()["key"]

    # Attach the actual screenshot image if one was provided. Never let an
    # attachment problem undo the (already created) ticket.
    if convo.get("screenshot_url"):
        try:
            attach_screenshot_link(issue_key, convo["screenshot_url"], auth)
        except Exception as exc:  # defensive: attachment must not crash ticket creation
            logger.warning("attach_screenshot_link raised, continuing: %s", exc)

    return issue_key


def attach_screenshot_link(issue_key: str, screenshot_url: str, auth: HTTPBasicAuth):
    """Download the screenshot from blob storage and attach it to the issue.

    The 'screenshots' container is private, so the bytes are pulled via the
    authenticated storage SDK (not an anonymous HTTP GET). If the download fails,
    attaching is skipped silently — the URL still appears in the description as a
    fallback — rather than crashing ticket creation.
    """
    # Import here so a storage/credential problem degrades to "skip attachment"
    # instead of breaking module import.
    try:
        from storage import download_blob_by_url

        image_bytes = download_blob_by_url(screenshot_url)
    except Exception as exc:
        logger.warning(
            "Could not download screenshot from blob storage (%s); skipping "
            "attachment. URL remains in the ticket description.",
            exc,
        )
        return None

    filename = screenshot_url.rstrip("/").split("/")[-1].split("?", 1)[0] or "screenshot.png"
    base_url = os.getenv("JIRA_BASE_URL").rstrip("/")
    url = f"{base_url}/rest/api/3/issue/{issue_key}/attachments"

    try:
        resp = requests.post(
            url,
            auth=auth,
            # "no-check" is required by Jira to bypass XSRF protection on uploads;
            # omitting it causes a silent failure.
            headers={"X-Atlassian-Token": "no-check"},
            files={"file": (filename, image_bytes, "application/octet-stream")},
            timeout=60,
        )
        resp.raise_for_status()
    except requests.RequestException as exc:
        body = getattr(exc.response, "text", "") if getattr(exc, "response", None) is not None else ""
        logger.warning("Screenshot attachment upload failed: %s | response body: %s", exc, body)
        return None

    return resp.json()
