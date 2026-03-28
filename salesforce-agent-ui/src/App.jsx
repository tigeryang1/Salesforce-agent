import { useEffect, useState } from "react";

const DEFAULT_AGENT_URL = "http://127.0.0.1:8080";
const DEFAULT_MCP_URL = "http://127.0.0.1:8000/mcp";

function pretty(value) {
  return JSON.stringify(value, null, 2);
}

export default function App() {
  const [agentUrl, setAgentUrl] = useState(DEFAULT_AGENT_URL);
  const [apiToken, setApiToken] = useState("test-api-token");
  const [health, setHealth] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(false);

  const [runForm, setRunForm] = useState({
    user_input: "Analyze Nike account and suggest optimizations",
    thread_id: "demo-1",
    mcp_url: DEFAULT_MCP_URL,
    model: "openai:gpt-5.3-codex",
    session_token: "tok_alice_us",
    user_id: "alice",
    org_id: "US",
    region: "US",
    account_scope: "acct_us_001",
    approved_tools:
      "search_advertiser,search_global,create_support_case,update_campaign_budget,optimize_campaign"
  });
  const [runResult, setRunResult] = useState(null);
  const [runError, setRunError] = useState("");
  const [running, setRunning] = useState(false);

  const [resumeForm, setResumeForm] = useState({
    thread_id: "demo-1",
    decision: "approve",
    approval_token: "apv_test_123"
  });
  const [resumeResult, setResumeResult] = useState(null);
  const [resumeError, setResumeError] = useState("");
  const [resuming, setResuming] = useState(false);

  async function fetchHealth() {
    setLoadingHealth(true);
    try {
      const response = await fetch(`${agentUrl}/healthz`);
      const data = await response.json();
      setHealth(data);
    } catch (error) {
      setHealth({ ok: false, error: String(error) });
    } finally {
      setLoadingHealth(false);
    }
  }

  useEffect(() => {
    fetchHealth();
  }, []);

  async function handleRun(event) {
    event.preventDefault();
    setRunning(true);
    setRunError("");
    setRunResult(null);
    try {
      const response = await fetch(`${agentUrl}/run`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiToken}`
        },
        body: JSON.stringify({
          ...runForm,
          approved_tools: runForm.approved_tools
            .split(",")
            .map((item) => item.trim())
            .filter(Boolean)
        })
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Run request failed");
      }
      setRunResult(data);
      setResumeForm((current) => ({
        ...current,
        thread_id: runForm.thread_id
      }));
    } catch (error) {
      setRunError(String(error));
    } finally {
      setRunning(false);
    }
  }

  async function handleResume(event) {
    event.preventDefault();
    setResuming(true);
    setResumeError("");
    setResumeResult(null);
    try {
      const response = await fetch(`${agentUrl}/resume-approval`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiToken}`
        },
        body: JSON.stringify(resumeForm)
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || "Resume request failed");
      }
      setResumeResult(data);
    } catch (error) {
      setResumeError(String(error));
    } finally {
      setResuming(false);
    }
  }

  return (
    <div className="shell">
      <aside className="rail">
        <div className="brand">
          <span className="brand-mark">SA</span>
          <div>
            <h1>Salesforce Agent</h1>
            <p>React console for the FastAPI LangGraph backend</p>
          </div>
        </div>
        <div className="status-card">
          <div className="status-row">
            <span>Agent API</span>
            <code>{agentUrl}</code>
          </div>
          <button className="ghost-button" onClick={fetchHealth} disabled={loadingHealth}>
            {loadingHealth ? "Checking..." : "Refresh health"}
          </button>
          <pre>{health ? pretty(health) : "No health data yet."}</pre>
        </div>
      </aside>

      <main className="content">
        <section className="panel hero">
          <div>
            <p className="eyebrow">Backend-driven workflow</p>
            <h2>Run the agent, inspect the graph state, and resume approval in one UI.</h2>
          </div>
          <label className="field">
            <span>Agent backend URL</span>
            <input value={agentUrl} onChange={(e) => setAgentUrl(e.target.value)} />
          </label>
          <label className="field">
            <span>API bearer token</span>
            <input value={apiToken} onChange={(e) => setApiToken(e.target.value)} />
          </label>
        </section>

        <div className="grid">
          <section className="panel">
            <div className="panel-head">
              <h3>Run workflow</h3>
              <span>POST /run</span>
            </div>
            <form onSubmit={handleRun} className="form-grid">
              <label className="field field-wide">
                <span>User input</span>
                <textarea
                  rows="4"
                  value={runForm.user_input}
                  onChange={(e) => setRunForm({ ...runForm, user_input: e.target.value })}
                />
              </label>
              <label className="field">
                <span>Thread ID</span>
                <input
                  value={runForm.thread_id}
                  onChange={(e) => setRunForm({ ...runForm, thread_id: e.target.value })}
                />
              </label>
              <label className="field">
                <span>MCP URL</span>
                <input
                  value={runForm.mcp_url}
                  onChange={(e) => setRunForm({ ...runForm, mcp_url: e.target.value })}
                />
              </label>
              <label className="field">
                <span>Model</span>
                <input
                  value={runForm.model}
                  onChange={(e) => setRunForm({ ...runForm, model: e.target.value })}
                />
              </label>
              <label className="field">
                <span>Session token</span>
                <input
                  value={runForm.session_token}
                  onChange={(e) => setRunForm({ ...runForm, session_token: e.target.value })}
                />
              </label>
              <label className="field">
                <span>User ID</span>
                <input
                  value={runForm.user_id}
                  onChange={(e) => setRunForm({ ...runForm, user_id: e.target.value })}
                />
              </label>
              <label className="field">
                <span>Org ID</span>
                <input
                  value={runForm.org_id}
                  onChange={(e) => setRunForm({ ...runForm, org_id: e.target.value })}
                />
              </label>
              <label className="field">
                <span>Region</span>
                <input
                  value={runForm.region}
                  onChange={(e) => setRunForm({ ...runForm, region: e.target.value })}
                />
              </label>
              <label className="field">
                <span>Account scope</span>
                <input
                  value={runForm.account_scope}
                  onChange={(e) => setRunForm({ ...runForm, account_scope: e.target.value })}
                />
              </label>
              <label className="field field-wide">
                <span>Approved tools</span>
                <input
                  value={runForm.approved_tools}
                  onChange={(e) => setRunForm({ ...runForm, approved_tools: e.target.value })}
                />
              </label>
              <button className="primary-button" type="submit" disabled={running}>
                {running ? "Running..." : "Run agent"}
              </button>
            </form>
            {runError ? <p className="error-box">{runError}</p> : null}
            <pre>{runResult ? pretty(runResult) : "Run result will appear here."}</pre>
          </section>

          <section className="panel">
            <div className="panel-head">
              <h3>Resume approval</h3>
              <span>POST /resume-approval</span>
            </div>
            <form onSubmit={handleResume} className="form-grid">
              <label className="field">
                <span>Thread ID</span>
                <input
                  value={resumeForm.thread_id}
                  onChange={(e) => setResumeForm({ ...resumeForm, thread_id: e.target.value })}
                />
              </label>
              <label className="field">
                <span>Decision</span>
                <select
                  value={resumeForm.decision}
                  onChange={(e) => setResumeForm({ ...resumeForm, decision: e.target.value })}
                >
                  <option value="approve">approve</option>
                  <option value="reject">reject</option>
                </select>
              </label>
              <label className="field field-wide">
                <span>Approval token</span>
                <input
                  value={resumeForm.approval_token}
                  onChange={(e) =>
                    setResumeForm({ ...resumeForm, approval_token: e.target.value })
                  }
                />
              </label>
              <button className="primary-button alt" type="submit" disabled={resuming}>
                {resuming ? "Resuming..." : "Resume approval"}
              </button>
            </form>
            {resumeError ? <p className="error-box">{resumeError}</p> : null}
            <pre>{resumeResult ? pretty(resumeResult) : "Approval response will appear here."}</pre>
          </section>
        </div>
      </main>
    </div>
  );
}
