import type { Config, ConversationSummary, ConversationDetail } from "./types";

export const BASE = import.meta.env.VITE_API_BASE_URL;

async function getJson<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Request failed (${res.status}): ${detail || res.statusText}`);
  }
  return (await res.json()) as T;
}

export async function getConfig(): Promise<Config> {
  return getJson<Config>(await fetch(`${BASE}/admin/config`));
}

export async function updateConfig(update: Partial<Config>): Promise<Config> {
  const res = await fetch(`${BASE}/admin/config`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  });
  return getJson<Config>(res);
}

export async function listConversations(): Promise<ConversationSummary[]> {
  return getJson<ConversationSummary[]>(await fetch(`${BASE}/admin/conversations`));
}

export async function getConversation(id: string): Promise<ConversationDetail> {
  return getJson<ConversationDetail>(
    await fetch(`${BASE}/admin/conversations/${encodeURIComponent(id)}`),
  );
}
