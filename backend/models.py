from typing import Literal
from pydantic import BaseModel


class EnvironmentInfo(BaseModel):
    user_agent: str | None = None
    screen_resolution: str | None = None
    viewport: str | None = None
    language: str | None = None
    timestamp: str | None = None
    os: str | None = None


class AgentDecision(BaseModel):
    action: Literal["answer", "ask_followup", "escalate"]
    message: str
    reasoning: str
    kb_sources: list[str] = []
    # Priority values must match the Jira project's actual scheme exactly
    # (SCRUM project uses Highest/High/Medium/Low/Lowest).
    priority: Literal["Lowest", "Low", "Medium", "High", "Highest"] | None = None


#ai agent decided weather to answer,.. here
