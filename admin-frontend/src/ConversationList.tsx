import { useEffect, useState } from "react";
import type { ConversationSummary, ConversationDetail } from "./types";
import { listConversations, getConversation, BASE } from "./api";

function StatusBadge({ status }: { status: string }) {
  return <span className={`badge badge-${status}`}>{status}</span>;
}

export default function ConversationList() {
  const [rows, setRows] = useState<ConversationSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<ConversationDetail | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [envOpen, setEnvOpen] = useState(false);

  useEffect(() => {
    listConversations()
      .then(setRows)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function openConversation(id: string) {
    setSelectedId(id);
    setDetailLoading(true);
    setEnvOpen(false);
    setError(null);
    try {
      setSelected(await getConversation(id));
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
      setSelected(null);
    } finally {
      setDetailLoading(false);
    }
  }

  return (
    <div className="panel conversations">
      {error && <div className="error-box">{error}</div>}
      <div className="conv-layout">
        {/* Left: list */}
        <div className="conv-list">
          <div className="conv-list-header">
            {loading ? "Loading…" : `${rows.length} conversations`}
          </div>
          {rows.map((r) => (
            <button
              key={r.id}
              className={`conv-row ${selectedId === r.id ? "active" : ""}`}
              onClick={() => openConversation(r.id)}
            >
              <div className="conv-row-top">
                <span className="conv-id">{r.id.slice(0, 8)}</span>
                <StatusBadge status={r.status} />
              </div>
              <div className="conv-row-meta">
                <span>{r.message_count} msgs</span>
                {r.ticket_id && <span className="conv-ticket">{r.ticket_id}</span>}
              </div>
            </button>
          ))}
        </div>

        {/* Right: detail */}
        <div className="conv-detail">
          {!selectedId && <div className="empty-hint">Select a conversation to view details.</div>}
          {detailLoading && <div>Loading conversation…</div>}
          {selected && !detailLoading && (
            <>
              <div className="detail-head">
                <StatusBadge status={selected.status} />
                {selected.ticket_id && (
                  <span className="detail-ticket">Ticket: {selected.ticket_id}</span>
                )}
                <span className="detail-followups">
                  Follow-ups: {selected.followup_count}
                </span>
              </div>

              <h3 className="detail-subhead">Transcript</h3>
              <div className="transcript">
                {selected.messages.map((m, i) => (
                  <div key={i} className={`t-msg ${m.role}`}>
                    <span className="t-role">{m.role}</span>
                    <span className="t-content">{m.content}</span>
                  </div>
                ))}
              </div>

              {selected.environment && (
                <div className="env-section">
                  <button className="collapse-btn" onClick={() => setEnvOpen((o) => !o)}>
                    {envOpen ? "▼" : "▶"} Environment info
                  </button>
                  {envOpen && (
                    <pre className="env-json">
                      {JSON.stringify(selected.environment, null, 2)}
                    </pre>
                  )}
                </div>
              )}

              {selected.screenshot_url && (
                <div className="screenshot-section">
                  <h3 className="detail-subhead">Screenshot</h3>
                  <img
                    className="screenshot-img"
                    src={`${BASE}/admin/screenshot-proxy?url=${encodeURIComponent(selected.screenshot_url)}`}
                    alt="screenshot"
                  />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
