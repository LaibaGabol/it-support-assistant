"""Azure Cosmos DB setup: database, containers, and one-time config seed."""
import os

from azure.cosmos import CosmosClient, PartitionKey
from dotenv import load_dotenv

load_dotenv()
#cosmos db for db history in chat
_client = CosmosClient(
    url=os.getenv("COSMOS_ENDPOINT"),
    credential=os.getenv("COSMOS_KEY"),
)

# Database + containers (created if they don't already exist). The account is
# serverless, so no throughput is provisioned on the containers.
database = _client.create_database_if_not_exists(id="it_support")

conversations = database.create_container_if_not_exists(
    id="conversations",
    partition_key=PartitionKey(path="/id"),
)

config = database.create_container_if_not_exists(
    id="config",
    partition_key=PartitionKey(path="/id"),
)
#settings in the cosmos db so that the admin can change the settings for depth.. without changing the python code
# Default settings document seeded on first run.
DEFAULT_SETTINGS = {
    "id": "settings",
    "system_prompt": "You are an IT support assistant helping employees troubleshoot IT issues.",
    "depth": 3,
    "max_followups": 3,
}


def seed_settings() -> None:
    """Seed the 'settings' config document once, if it doesn't already exist."""
    try:
        config.read_item(item="settings", partition_key="settings")
    except Exception:
        # Not found (or unreadable) -> create it.
        config.upsert_item(DEFAULT_SETTINGS)


def get_settings() -> dict:
    """Return the settings document, seeding defaults if absent."""
    try:
        return config.read_item(item="settings", partition_key="settings")
    except Exception:
        config.upsert_item(DEFAULT_SETTINGS)
        return dict(DEFAULT_SETTINGS)


# Seed on import so the app always has a settings document available.
seed_settings()
