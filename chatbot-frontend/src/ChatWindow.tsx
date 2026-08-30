import { useEffect, useRef, useState } from "react";
import type { ChatMessage } from "./types";
import { sendMessage, uploadScreenshot } from "./api";
import { captureEnvironment } from "./environment";

type Status = "open" | "resolved" | "escalated";

// The backend appends the ticket to the reply as:
//   "A support ticket has been created: SCRUM-123"
// so we extract a Jira issue key (PROJECT-number) from the message text.
const TICKET_RE = /\b([A-Z][A-Z0-9]+-\d+)\b/;

export default function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [status, setStatus] = useState<Status>("open");
  const [ticketInfo, setTicketInfo] = useState<string | null>(null);
  const [pendingScreenshot, setPendingScreenshot] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);

  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const listEndRef = useRef<HTMLDivElement | null>(null);

  const closed = status === "resolved" || status === "escalated";
  const disabled = loading || closed;

  useEffect(() => {
    listEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend() {
    const text = input.trim();
    if (!text || disabled) return;

    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);

    try {
      // Upload the pending screenshot first (if any) to get a URL.
      let screenshotUrl: string | undefined;
      if (pendingScreenshot) {
        screenshotUrl = await uploadScreenshot(pendingScreenshot);
      }

      const environment = captureEnvironment();
      const resp = await sendMessage(text, conversationId, environment, screenshotUrl);

      setConversationId(resp.conversation_id);
      setMessages((prev) => [...prev, { role: "assistant", content: resp.message }]);

      if (resp.action === "answer") {
        setStatus("resolved");
      } else if (resp.action === "escalate") {
        setStatus("escalated");
        const match = resp.message.match(TICKET_RE);
        setTicketInfo(match ? match[1] : null);
      }

      // Screenshot has been sent; clear it either way.
      setPendingScreenshot(null);
    } catch (err) {
      const detail = err instanceof Error ? err.message : String(err);
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `⚠️ Sorry, something went wrong contacting the support service. Please try again.\n\n(${detail})`,
        },
      ]);
      // Keep the conversation open so the user can retry.
    } finally {
      setLoading(false);
    }
  }

  function onKeyDown(e: React.KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  function onFilePicked(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    setPendingScreenshot(file);
    // Reset the input value so re-selecting the same file still fires onChange.
    e.target.value = "";
  }

  return (
    <div className="chat-window">
      <div className="message-list">
        {messages.length === 0 && (
          <div className="empty-hint">
            Describe your IT issue to get started (e.g. “my printer isn’t showing up on the network”).
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`message ${m.role}`}>
            <div className="bubble">{m.content}</div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <div className="bubble typing">…</div>
          </div>
        )}
        <div ref={listEndRef} />
      </div>

      {status === "escalated" && (
        <div className="ticket-banner">
          🎫 This conversation has been escalated to IT support.
          {ticketInfo ? (
            <>
              {" "}
              Ticket created: <strong>{ticketInfo}</strong>
            </>
          ) : (
            " A support ticket has been created."
          )}
        </div>
      )}

      {status === "resolved" && (
        <div className="resolved-banner">✅ This issue has been resolved.</div>
      )}

      <div className="input-row">
        <input
          type="file"
          accept="image/*"
          ref={fileInputRef}
          onChange={onFilePicked}
          style={{ display: "none" }}
        />
        <button
          type="button"
          className="attach-btn"
          onClick={() => fileInputRef.current?.click()}
          disabled={disabled}
          title="Attach a screenshot"
        >
          📎 Attach{pendingScreenshot ? " ✓" : ""}
        </button>
        <input
          type="text"
          className="text-input"
          placeholder={closed ? "Conversation closed" : "Type your message…"}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          disabled={disabled}
        />
        <button
          type="button"
          className="send-btn"
          onClick={handleSend}
          disabled={disabled || !input.trim()}
        >
          {loading ? "…" : "Send"}
        </button>
      </div>

      {pendingScreenshot && !closed && (
        <div className="attach-note">
          Screenshot ready to send: <em>{pendingScreenshot.name}</em>
        </div>
      )}
    </div>
  );
}
