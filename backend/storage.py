"""Azure Blob Storage helper for screenshot uploads."""
import os
import uuid
from urllib.parse import unquote

from azure.storage.blob import BlobServiceClient, ContentSettings
from dotenv import load_dotenv

load_dotenv()

CONTAINER_NAME = "screenshots"

_service = BlobServiceClient.from_connection_string(os.getenv("BLOB_CONNECTION_STRING"))
container_client = _service.get_container_client(CONTAINER_NAME)


def _guess_content_type(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith(".png"):
        return "image/png"
    if lower.endswith((".jpg", ".jpeg")):
        return "image/jpeg"
    if lower.endswith(".gif"):
        return "image/gif"
    if lower.endswith(".webp"):
        return "image/webp"
    return "application/octet-stream"


def upload_screenshot(file_bytes: bytes, filename: str) -> str:
    """Upload screenshot bytes under a unique blob name; return the blob URL."""
    safe_name = filename or "screenshot"
    blob_name = f"{uuid.uuid4()}-{safe_name}"
    blob_client = container_client.get_blob_client(blob_name)
    blob_client.upload_blob(
        file_bytes,
        overwrite=True,
        content_settings=ContentSettings(content_type=_guess_content_type(safe_name)),
    )
    return blob_client.url


def download_blob_by_url(url: str) -> bytes:
    """Download a blob's bytes given its full URL.

    The 'screenshots' container is private (no anonymous access), so this uses
    the authenticated SDK client rather than a plain HTTP GET. The blob name is
    parsed from the URL (everything after the container path).
    """
    marker = f"/{CONTAINER_NAME}/"
    idx = url.find(marker)
    if idx == -1:
        raise ValueError(f"URL does not point to the '{CONTAINER_NAME}' container: {url}")
    blob_name = unquote(url[idx + len(marker):].split("?", 1)[0])
    return container_client.get_blob_client(blob_name).download_blob().readall()
