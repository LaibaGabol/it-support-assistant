import type { ChatResponse, EnvironmentInfo } from "./types";

const BASE = import.meta.env.VITE_API_BASE_URL;

export async function sendMessage(
  message: string,
  conversationId: string | null,
  environment?: EnvironmentInfo,
  screenshotUrl?: string,
): Promise<ChatResponse> {
  const res = await fetch(`${BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      conversation_id: conversationId,
      message,
      environment: environment ?? null,
      screenshot_url: screenshotUrl ?? null,
    }),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Chat request failed (${res.status}): ${detail || res.statusText}`);
  }

  return (await res.json()) as ChatResponse;
}

export async function uploadScreenshot(file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch(`${BASE}/upload-screenshot`, {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(`Screenshot upload failed (${res.status}): ${detail || res.statusText}`);
  }

  const data = (await res.json()) as { screenshot_url: string };
  return data.screenshot_url;
}
