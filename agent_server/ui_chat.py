"""Chat console with a live agent-flow rail."""

from agent_server.ui_common import BASE_CSS, FAVICON, LAKEBASE_ICON, header_html

_CSS = """
main {
  flex:1; width:100%; max-width:1340px; margin:0 auto; padding:16px 20px 0;
  display:grid; grid-template-columns:352px 1fr; gap:18px; min-height:0;
}
@media (max-width:960px) { main { grid-template-columns:1fr; } aside { max-height:320px; } }

aside { display:flex; flex-direction:column; min-height:0; }
aside > h3 {
  margin:0 0 10px; font-size:11px; letter-spacing:.16em; color:var(--muted); font-weight:600;
  display:flex; align-items:center; gap:7px;
}
aside > h3 .liveled {
  width:7px; height:7px; border-radius:50%; background:var(--lava);
  animation:pulse 1.6s ease-in-out infinite;
}
.rail { flex:1; overflow-y:auto; min-height:0; padding-right:4px; }

.memcard {
  background:rgba(255,171,0,.08); border:1px solid rgba(255,171,0,.38);
  border-radius:8px; padding:11px 13px; margin-bottom:12px;
}
.memcard h4 {
  margin:0 0 4px; font-size:12.5px; color:var(--maize);
  display:flex; align-items:center; gap:6px;
}
.memcard h4 svg { width:12px; height:13px; flex:0 0 auto; }
.memcard p { margin:0; font-size:11.5px; color:var(--muted); line-height:1.5; }
.memcard ul { margin:8px 0 0; padding-left:16px; }
.memcard li { font-size:11px; color:var(--oat); margin-bottom:3px; word-break:break-word; }
.memcard .delta { color:var(--maize); font-weight:600; }

.fnode {
  position:relative; padding:0 0 12px 20px; border-left:1px solid var(--line); margin-left:5px;
}
.fnode:last-child { border-left-color:transparent; }
.fnode::before {
  content:""; position:absolute; left:-5px; top:3px; width:9px; height:9px;
  border-radius:50%; background:var(--navy-600); border:2px solid var(--navy-900);
}
.fnode.run::before { background:var(--lava); animation:pulse 1.1s ease-in-out infinite; }
.fnode.done::before { background:var(--green); }
.fnode.mem::before { background:var(--maize); }
.fnode.bad::before { background:var(--err); }
@keyframes pulse { 0%,100% { transform:scale(1); opacity:1; } 50% { transform:scale(1.5); opacity:.55; } }

.fnode .fh { display:flex; align-items:baseline; justify-content:space-between; gap:8px; }
.fnode .fn { font-size:12.5px; font-weight:600; }
.fnode.mem .fn { color:var(--maize); }
.fnode .ms { font-size:10px; color:var(--muted); white-space:nowrap; }
.fnode .tgt { font-size:10.5px; color:var(--blue); margin-top:2px; }
.fnode .args { font-size:10.5px; color:var(--muted); margin-top:3px; word-break:break-word; font-family:ui-monospace,Menlo,monospace; }
.fnode details { margin-top:5px; }
.fnode summary { font-size:10.5px; color:var(--lava); cursor:pointer; }
.fnode pre {
  margin:5px 0 0; padding:8px; background:var(--navy-900); border:1px solid var(--line);
  border-radius:5px; font-size:10.5px; max-height:170px; overflow:auto; white-space:pre-wrap; word-break:break-word;
}
.turnsep { font-size:10px; letter-spacing:.14em; color:#6E8B95; margin:4px 0 10px; }

section.chat { display:flex; flex-direction:column; min-height:0; }
.chips { display:flex; gap:7px; flex-wrap:wrap; margin-bottom:12px; }
.chip {
  background:rgba(27,49,57,.6); border:1px solid var(--line); color:var(--oat);
  border-radius:999px; padding:6px 12px; font-size:12px; cursor:pointer; font-family:inherit;
}
.chip:hover { border-color:var(--lava); color:var(--lava); }
#log { flex:1; overflow-y:auto; display:flex; flex-direction:column; gap:11px; padding-bottom:14px; min-height:0; }
.msg { max-width:88%; padding:11px 14px; border-radius:9px; font-size:14px; line-height:1.55; white-space:pre-wrap; }
.user { align-self:flex-end; background:var(--lava); color:#fff; font-weight:500; }
.bot { align-self:flex-start; background:var(--navy-800); border:1px solid var(--line); }
.err { align-self:flex-start; background:#3A1E1B; border:1px solid #7A3A30; }
form { flex:0 0 auto; display:flex; gap:10px; padding:11px 0 18px; }
input[type=text] {
  flex:1; background:var(--navy-800); border:1px solid var(--line); color:var(--oat);
  border-radius:7px; padding:12px 14px; font-size:14px; font-family:inherit;
}
input[type=text]:focus { outline:none; border-color:var(--lava); }
button.send {
  background:var(--lava); color:#fff; border:0; border-radius:7px;
  padding:12px 22px; font-weight:600; font-size:14px; cursor:pointer; font-family:inherit;
}
button.send:hover:not(:disabled) { background:var(--lava-dim); }
button.send:disabled { opacity:.5; cursor:not-allowed; }
"""

_JS = """
const TOOL_TARGET = {
  lookup_subscriber:      "gulfnet.subscribers + plans",
  get_usage_summary:      "gulfnet.usage_daily",
  recommend_plan:         "gulfnet.plans",
  create_support_ticket:  "gulfnet.tickets (write)",
  check_network_status:   "gulfnet.network_events",
  search_knowledge:       "gulfnet.kb_chunks (FTS + vector)",
  get_user_memory:        "long-term store: user_memories",
  save_user_memory:       "long-term store: user_memories (write)",
  delete_user_memory:     "long-term store: user_memories (delete)",
  enqueue_ops_task:       "gulfnet.tasks (enqueue)",
  get_task_status:        "gulfnet.tasks",
  get_current_time:       "agent runtime"
};
const MEM_TOOLS = ["get_user_memory","save_user_memory","delete_user_memory"];

const PROMPTS = [
  "Look up +971501234567. What plan and recent roaming?",
  "They travel to Riyadh monthly - remember that and advise on roaming.",
  "Always contact them on WhatsApp in Arabic.",
  "Dubai Marina degradation - impact on VIP accounts?",
  "Find high churn-risk prepaid customers and draft offers."
];

const USER_ID = "care-console-user";
const THREAD_ID = "ui-" + Math.random().toString(36).slice(2, 10);

const log = document.getElementById("log");
const rail = document.getElementById("rail");
const form = document.getElementById("form");
const input = document.getElementById("q");
const sendBtn = document.getElementById("send");
let turn = 0;
let lastMemCount = null;

const chips = document.getElementById("chips");
PROMPTS.forEach(p => {
  const b = document.createElement("button");
  b.type = "button"; b.className = "chip"; b.title = p;
  b.textContent = p.length > 46 ? p.slice(0, 46) + "..." : p;
  b.onclick = () => { input.value = p; input.focus(); };
  chips.appendChild(b);
});

function addMsg(text, cls) {
  const d = document.createElement("div");
  d.className = "msg " + cls;
  d.textContent = text;
  log.appendChild(d);
  log.scrollTop = log.scrollHeight;
  return d;
}

function railScroll() { rail.scrollTop = rail.scrollHeight; }

function addFlow(label, opts) {
  opts = opts || {};
  const d = document.createElement("div");
  d.className = "fnode " + (opts.state || "run") + (opts.mem ? " mem" : "");
  const h = document.createElement("div");
  h.className = "fh";
  const n = document.createElement("span");
  n.className = "fn"; n.textContent = label;
  const ms = document.createElement("span");
  ms.className = "ms"; ms.textContent = opts.ms || "";
  h.appendChild(n); h.appendChild(ms);
  d.appendChild(h);
  if (opts.target) {
    const t = document.createElement("div");
    t.className = "tgt"; t.textContent = opts.target;
    d.appendChild(t);
  }
  rail.appendChild(d);
  railScroll();
  return { el: d, ms: ms };
}

function setArgs(node, text) {
  let a = node.el.querySelector(".args");
  if (!a) {
    a = document.createElement("div");
    a.className = "args";
    node.el.appendChild(a);
  }
  a.textContent = text;
}

function setResult(node, text) {
  const det = document.createElement("details");
  const s = document.createElement("summary");
  s.textContent = "result";
  const pre = document.createElement("pre");
  pre.textContent = text;
  det.appendChild(s); det.appendChild(pre);
  node.el.appendChild(det);
  railScroll();
}

async function refreshMemory(phase) {
  const body = document.getElementById("membody");
  try {
    const res = await fetch("/ui/memory?user_id=" + encodeURIComponent(USER_ID), { credentials: "same-origin" });
    const d = await res.json();
    const n = d.count || 0;
    const grew = lastMemCount !== null && n > lastMemCount;
    const delta = grew ? ' <span class="delta">+' + (n - lastMemCount) + " new</span>" : "";
    let html = "<p>" + n + " item(s) stored for this user" + delta + "</p>";
    if (d.items && d.items.length) {
      html += "<ul>" + d.items.map(i =>
        "<li><b>" + i.key + "</b>: " + JSON.stringify(i.value) + "</li>").join("") + "</ul>";
    } else if (!d.error) {
      html += "<p>Nothing yet. Tell the agent a preference and watch it persist.</p>";
    }
    if (d.error) html += "<p>" + d.error + "</p>";
    body.innerHTML = html;
    if (grew && phase === "after") {
      addFlow("memory written to Lakebase", {
        state: "done", mem: true, target: (n - lastMemCount) + " new item(s) in user_memories"
      });
    }
    lastMemCount = n;
    return n;
  } catch (e) {
    body.innerHTML = "<p>Unavailable: " + e.message + "</p>";
    return 0;
  }
}

form.onsubmit = async (e) => {
  e.preventDefault();
  const text = input.value.trim();
  if (!text) return;

  turn += 1;
  input.value = "";
  sendBtn.disabled = true;
  addMsg(text, "user");

  const sep = document.createElement("div");
  sep.className = "turnsep";
  sep.textContent = "TURN " + turn;
  rail.appendChild(sep);

  const n = await refreshMemory("before");
  if (turn === 1) {
    addFlow("long-term memory recalled", {
      state: "done", mem: true,
      target: n ? n + " item(s) injected into context" : "no stored memories yet"
    });
  } else {
    addFlow("thread checkpoint replayed", {
      state: "done", mem: true, target: "short-term memory for this thread"
    });
  }

  const modelNode = addFlow("model reasoning", { target: "Claude Sonnet 4.5" });
  const t0 = performance.now();
  const byItem = {};   // function_call item id -> node
  const byCall = {};   // call_id -> {node, t}
  const bubbles = {};  // message item id -> element
  let sawError = false;

  function handle(ev) {
    const it = ev.item || {};
    if (ev.type === "response.output_item.added" && it.type === "function_call") {
      const mem = MEM_TOOLS.indexOf(it.name) >= 0;
      const node = addFlow(it.name, { target: TOOL_TARGET[it.name] || "Lakebase", mem: mem });
      byItem[it.id] = node;
      if (it.call_id) byCall[it.call_id] = { node: node, t: performance.now() };
    } else if (ev.type === "response.function_call_arguments.delta") {
      const node = byItem[ev.item_id];
      if (node) {
        node._args = (node._args || "") + (ev.delta || "");
        setArgs(node, node._args);
      }
    } else if (ev.type === "response.output_item.done" && it.type === "function_call") {
      const node = byItem[it.id];
      if (node) {
        if (it.arguments) setArgs(node, it.arguments);
        if (it.call_id && !byCall[it.call_id]) byCall[it.call_id] = { node: node, t: performance.now() };
      }
    } else if (ev.type === "response.output_item.done" && it.type === "function_call_output") {
      const rec = byCall[it.call_id];
      if (rec) {
        rec.node.el.classList.remove("run");
        rec.node.el.classList.add("done");
        rec.node.ms.textContent = Math.round(performance.now() - rec.t) + " ms";
        setResult(rec.node, String(it.output || ""));
      }
    } else if (ev.type === "response.output_text.delta") {
      let b = bubbles[ev.item_id];
      if (!b) {
        b = addMsg("", "bot");
        bubbles[ev.item_id] = b;
        modelNode.el.classList.remove("run");
        modelNode.el.classList.add("done");
        modelNode.ms.textContent = Math.round(performance.now() - t0) + " ms";
        addFlow("streaming answer", { state: "done", target: "SSE to browser" });
      }
      b.textContent += ev.delta || "";
      log.scrollTop = log.scrollHeight;
    } else if (ev.type === "response.output_item.done" && it.type === "message") {
      const txt = (it.content || []).map(c => c.text || "").join("");
      if (bubbles[it.id]) bubbles[it.id].textContent = txt;
      else if (txt.trim()) bubbles[it.id] = addMsg(txt, "bot");
    }
  }

  try {
    const res = await fetch("/invocations", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        input: [{ role: "user", content: text }],
        stream: true,
        custom_inputs: { user_id: USER_ID, thread_id: THREAD_ID }
      })
    });

    if (!res.ok) {
      sawError = true;
      addMsg("Request failed (" + res.status + "): " + (await res.text()).slice(0, 400), "err");
    } else {
      const reader = res.body.getReader();
      const dec = new TextDecoder();
      let buf = "";
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        const parts = buf.split("\\n\\n");
        buf = parts.pop();
        for (const p of parts) {
          const line = p.split("\\n").find(l => l.startsWith("data:"));
          if (!line) continue;
          const payload = line.slice(5).trim();
          if (!payload || payload === "[DONE]") continue;
          try { handle(JSON.parse(payload)); }
          catch (err) { console.warn("bad event", payload.slice(0, 120)); }
        }
      }
    }
  } catch (err) {
    sawError = true;
    addMsg("Error: " + err.message, "err");
  } finally {
    if (modelNode.el.classList.contains("run")) {
      modelNode.el.classList.remove("run");
      modelNode.el.classList.add(sawError ? "bad" : "done");
      modelNode.ms.textContent = Math.round(performance.now() - t0) + " ms";
    }
    Object.keys(byCall).forEach(k => {
      const el = byCall[k].node.el;
      if (el.classList.contains("run")) { el.classList.remove("run"); el.classList.add("bad"); }
    });
    await refreshMemory("after");
    sendBtn.disabled = false;
    input.focus();
  }
};

refreshMemory("init");
"""

CHAT_HTML = (
    """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>GulfNet Care Copilot &mdash; chat</title>
__FAVICON__
<style>"""
    + BASE_CSS
    + _CSS
    + """</style>
</head>
<body>
__HEADER__
<main>
  <aside>
    <h3><span class="liveled"></span>AGENT FLOW &mdash; LIVE</h3>
    <div class="rail" id="rail">
      <div class="memcard" id="memcard">
        <h4>__LBICON__Lakebase long-term memory</h4>
        <div id="membody"><p>Loading&hellip;</p></div>
      </div>
    </div>
  </aside>

  <section class="chat">
    <div class="chips" id="chips"></div>
    <div id="log">
      <div class="msg bot">Hello. I am the GulfNet Care Copilot for UAE customer care agents.

Watch the left rail as I work: every tool call shows the Lakebase Postgres object it touches, its arguments and its result. Memory steps are marked in amber, completed steps in green.

Seeded VIP: +971501234567 (Layla Al Mansoori, Dubai).</div>
    </div>
    <form id="form">
      <input id="q" type="text" autocomplete="off"
             placeholder="Look up +971501234567. What is their plan?" />
      <button id="send" class="send" type="submit">Send</button>
    </form>
  </section>
</main>
<script>"""
    + _JS
    + """</script>
</body>
</html>
"""
)
CHAT_HTML = (
    CHAT_HTML.replace("__HEADER__", header_html("chat"))
    .replace("__FAVICON__", FAVICON)
    .replace("__LBICON__", LAKEBASE_ICON)
)
