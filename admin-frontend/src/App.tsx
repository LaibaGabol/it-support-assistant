import { useState } from "react";
import ConfigPanel from "./ConfigPanel";
import ConversationList from "./ConversationList";

type Tab = "config" | "history";

export default function App() {
  const [tab, setTab] = useState<Tab>("config");

  return (
    <div className="admin-app">
      <header className="admin-header">
        <h1>IT Support — Admin</h1>
        <nav className="tabs">
          <button
            className={`tab ${tab === "config" ? "active" : ""}`}
            onClick={() => setTab("config")}
          >
            Configuration
          </button>
          <button
            className={`tab ${tab === "history" ? "active" : ""}`}
            onClick={() => setTab("history")}
          >
            Conversation History
          </button>
        </nav>
      </header>

      <main>{tab === "config" ? <ConfigPanel /> : <ConversationList />}</main>
    </div>
  );
}
