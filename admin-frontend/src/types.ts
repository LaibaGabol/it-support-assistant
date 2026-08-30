// Interfaces mirror the backend admin endpoints (backend/app/main.py):
//   GET /admin/config, PUT /admin/config, GET /admin/conversations,
//   GET /admin/conversations/{id}

export interface Config {
  id: string;
  system_prompt: string;
  depth: 1 | 3 | 5;
  max_followups: number;
}

export type ConversationStatus = "open" | "resolved" | "escalated";

export interface ConversationSummary {
  id: string;
  status: ConversationStatus;
  message_count: number;
  ticket_id: string | null;
  depth: number;
}

export interface ConversationMessage {
  role: "user" | "assistant";
  content: string;
}

export interface ConversationDetail extends ConversationSummary {
  messages: ConversationMessage[];
  followup_count: number;
  environment?: Record<string, string>;
  screenshot_url?: string;
}
