// Interfaces mirror the backend Pydantic models (backend/models.py,
// backend/app/main.py). Field names must match the JSON the backend expects.

export interface EnvironmentInfo {
  user_agent: string;
  screen_resolution: string;
  viewport: string;
  language: string;
  timestamp: string;
  os: string;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
}

// Shape returned by POST /chat.
export interface ChatResponse {
  conversation_id: string;
  action: "answer" | "ask_followup" | "escalate";
  message: string;
}
