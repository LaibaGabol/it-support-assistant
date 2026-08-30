import { useEffect, useState } from "react";
import { getConfig, updateConfig } from "./api";

const DEPTH_LABELS: Record<number, string> = {
  1: "1 – Quick",
  3: "3 – Balanced",
  5: "5 – Thorough",
};

export default function ConfigPanel() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [systemPrompt, setSystemPrompt] = useState("");
  const [depth, setDepth] = useState<number>(3);
  const [maxFollowups, setMaxFollowups] = useState<number>(3);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    let cancelled = false;
    getConfig()
      .then((cfg) => {
        if (cancelled) return;
        setSystemPrompt(cfg.system_prompt);
        setDepth(cfg.depth);
        setMaxFollowups(cfg.max_followups);
      })
      .catch((e) => !cancelled && setError(e.message))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSave() {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await updateConfig({
        system_prompt: systemPrompt,
        depth: depth as 1 | 3 | 5,
        max_followups: maxFollowups,
      });
      // Reflect the persisted values that came back from the server.
      setSystemPrompt(updated.system_prompt);
      setDepth(updated.depth);
      setMaxFollowups(updated.max_followups);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <div className="panel">Loading configuration…</div>;

  return (
    <div className="panel config-panel">
      {error && <div className="error-box">{error}</div>}

      <label className="field">
        <span className="field-label">System prompt</span>
        <textarea
          className="prompt-textarea"
          rows={6}
          value={systemPrompt}
          onChange={(e) => setSystemPrompt(e.target.value)}
        />
      </label>

      <div className="field">
        <span className="field-label">Troubleshooting depth</span>
        <input
          type="range"
          min={1}
          max={5}
          step={2}
          value={depth}
          onChange={(e) => setDepth(Number(e.target.value))}
        />
        <div className="depth-scale">
          <span>1 – Quick</span>
          <span>3 – Balanced</span>
          <span>5 – Thorough</span>
        </div>
        <div className="depth-current">
          Current: <strong>{DEPTH_LABELS[depth] ?? depth}</strong>
        </div>
      </div>

      <label className="field">
        <span className="field-label">Max follow-ups</span>
        <input
          type="number"
          min={0}
          className="number-input"
          value={maxFollowups}
          onChange={(e) => setMaxFollowups(Number(e.target.value))}
        />
      </label>

      <div className="save-row">
        <button className="save-btn" onClick={handleSave} disabled={saving}>
          {saving ? "Saving…" : "Save"}
        </button>
        {saved && <span className="saved-msg">Saved ✓</span>}
      </div>
    </div>
  );
}
