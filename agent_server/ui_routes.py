"""Landing page + chat UI for GulfNet Care Copilot."""

from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])

CHAT_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GulfNet Care Copilot</title>
  <style>
    :root {
      --bg: #0b1f1a;
      --panel: #12352c;
      --panel-2: #164034;
      --ink: #e8f5f0;
      --muted: #8fb3a8;
      --accent: #2dd4a8;
      --warn: #f0b429;
      --line: #1f4a3d;
    }
    * { box-sizing: border-box; }
    html, body { height: 100%; }
    body {
      margin: 0;
      font-family: "IBM Plex Sans", -apple-system, "Segoe UI", sans-serif;
      background: radial-gradient(1200px 620px at 8% -12%, #1a4d3f 0%, var(--bg) 58%);
      color: var(--ink);
      display: flex;
      flex-direction: column;
      min-height: 100vh;
    }
    header {
      padding: 16px 24px;
      border-bottom: 1px solid var(--line);
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      flex-wrap: wrap;
    }
    .brand h1 { margin: 0; font-size: 18px; letter-spacing: .02em; }
    .brand h1 span { color: var(--accent); }
    .brand p { margin: 3px 0 0; font-size: 12px; color: var(--muted); }
    .links { display: flex; gap: 8px; flex-wrap: wrap; }
    .links a {
      color: var(--ink); text-decoration: none; font-size: 12px;
      border: 1px solid #2a5c4c; border-radius: 8px; padding: 6px 11px;
    }
    .links a:hover { border-color: var(--accent); color: var(--accent); }

    main {
      flex: 1; width: 100%; max-width: 900px; margin: 0 auto;
      padding: 18px 24px 0; display: flex; flex-direction: column; min-height: 0;
    }
    .chips { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }
    .chip {
      background: var(--panel); border: 1px solid var(--line); color: var(--ink);
      border-radius: 999px; padding: 7px 13px; font-size: 12.5px; cursor: pointer;
    }
    .chip:hover { border-color: var(--accent); }

    #log {
      flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px;
      padding-bottom: 16px; min-height: 0;
    }
    .msg { max-width: 88%; padding: 11px 14px; border-radius: 12px; font-size: 14px; line-height: 1.5; white-space: pre-wrap; }
    .user { align-self: flex-end; background: var(--accent); color: #06241c; font-weight: 500; }
    .bot { align-self: flex-start; background: var(--panel); border: 1px solid var(--line); }
    .tool {
      align-self: flex-start; max-width: 88%; background: #0e2a23;
      border: 1px dashed #2a5c4c; border-radius: 10px; font-size: 12px; color: var(--muted);
    }
    .tool summary { cursor: pointer; padding: 8px 12px; color: var(--accent); }
    .tool pre { margin: 0; padding: 0 12px 12px; overflow-x: auto; font-size: 11.5px; color: var(--ink); }
    .thinking { align-self: flex-start; color: var(--muted); font-size: 13px; font-style: italic; }
    .err { align-self: flex-start; background: #3d1f22; border: 1px solid #7a3b40; }

    form {
      position: sticky; bottom: 0; background: linear-gradient(180deg, transparent, var(--bg) 40%);
      padding: 12px 0 20px; display: flex; gap: 10px;
    }
    input[type=text] {
      flex: 1; background: var(--panel); border: 1px solid var(--line); color: var(--ink);
      border-radius: 10px; padding: 12px 14px; font-size: 14px; font-family: inherit;
    }
    input[type=text]:focus { outline: none; border-color: var(--accent); }
    button {
      background: var(--accent); color: #06241c; border: 0; border-radius: 10px;
      padding: 12px 20px; font-weight: 600; font-size: 14px; cursor: pointer; font-family: inherit;
    }
    button:disabled { opacity: .55; cursor: not-allowed; }
    footer { text-align: center; font-size: 11.5px; color: var(--muted); padding: 0 24px 14px; }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <h1><span>GulfNet</span> Care Copilot</h1>
      <p>UAE telco agent on Lakebase Postgres &middot; memory &middot; hybrid search &middot; task orchestration</p>
    </div>
    <div class="links">
      <a href="/ops/dashboard">Ops dashboard</a>
      <a href="/docs">API docs</a>
      <a href="/health">Health</a>
    </div>
  </header>

  <main>
    <div class="chips" id="chips"></div>
    <div id="log">
      <div class="msg bot">Hello. I am the GulfNet Care Copilot for UAE customer care agents.

Try a golden demo prompt below, or ask me about a subscriber, roaming rules, network status, or a VIP outage impact report.

Seeded VIP: +971501234567 (Layla Al Mansoori, Dubai).</div>
    </div>
    <form id="form">
      <input id="q" type="text" autocomplete="off"
             placeholder="Look up +971501234567. What is their plan?" />
      <button id="send" type="submit">Send</button>
    </form>
  </main>

  <footer>Fictional operator &middot; synthetic data only &middot; thread and memory persisted in Lakebase</footer>

  <script>
    const PROMPTS = [
      "Look up +971501234567. What is their plan and recent roaming?",
      "They will visit Riyadh next week - what roaming options apply?",
      "Remember they prefer WhatsApp updates in Arabic.",
      "There is a Dubai Marina degradation - impact on VIP accounts?",
      "Find high churn-risk prepaid customers and draft offers."
    ];

    const THREAD_ID = "ui-" + Math.random().toString(36).slice(2, 10);
    const USER_ID = "care-console-user";

    const log = document.getElementById("log");
    const form = document.getElementById("form");
    const input = document.getElementById("q");
    const sendBtn = document.getElementById("send");

    const chips = document.getElementById("chips");
    PROMPTS.forEach(p => {
      const b = document.createElement("button");
      b.type = "button";
      b.className = "chip";
      b.textContent = p.length > 52 ? p.slice(0, 52) + "..." : p;
      b.title = p;
      b.onclick = () => { input.value = p; input.focus(); };
      chips.appendChild(b);
    });

    function addNode(node) {
      log.appendChild(node);
      log.scrollTop = log.scrollHeight;
      return node;
    }

    function addMsg(text, cls) {
      const d = document.createElement("div");
      d.className = "msg " + cls;
      d.textContent = text;
      return addNode(d);
    }

    function addTool(name, args, output) {
      const d = document.createElement("details");
      d.className = "tool";
      const s = document.createElement("summary");
      s.textContent = "tool: " + name;
      const pre = document.createElement("pre");
      let body = "arguments: " + (args || "{}");
      if (output) body += "\\n\\nresult:\\n" + output;
      pre.textContent = body;
      d.appendChild(s);
      d.appendChild(pre);
      return addNode(d);
    }

    function renderOutput(output) {
      const calls = {};
      (output || []).forEach(item => {
        if (item.type === "function_call") {
          calls[item.call_id] = { name: item.name, args: item.arguments };
        } else if (item.type === "function_call_output") {
          const c = calls[item.call_id] || { name: "tool" };
          addTool(c.name, c.args, item.output);
        } else if (item.type === "message") {
          const text = (item.content || [])
            .map(c => c.text || "")
            .join("")
            .trim();
          if (text) addMsg(text, "bot");
        }
      });
    }

    form.onsubmit = async (e) => {
      e.preventDefault();
      const text = input.value.trim();
      if (!text) return;

      addMsg(text, "user");
      input.value = "";
      sendBtn.disabled = true;

      const pending = addNode(Object.assign(document.createElement("div"), {
        className: "thinking",
        textContent: "Care Copilot is working (querying Lakebase)..."
      }));

      try {
        const res = await fetch("/invocations", {
          method: "POST",
          credentials: "same-origin",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            input: [{ role: "user", content: text }],
            custom_inputs: { user_id: USER_ID, thread_id: THREAD_ID }
          })
        });

        pending.remove();

        if (!res.ok) {
          addMsg("Request failed (" + res.status + "): " + (await res.text()).slice(0, 400), "err");
        } else {
          const data = await res.json();
          renderOutput(data.output);
        }
      } catch (err) {
        pending.remove();
        addMsg("Error: " + err.message, "err");
      } finally {
        sendBtn.disabled = false;
        input.focus();
      }
    };
  </script>
</body>
</html>
"""


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> HTMLResponse:
    return HTMLResponse(CHAT_HTML)
