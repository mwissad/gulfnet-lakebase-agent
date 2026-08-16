"""Interactive architecture page: how the agent and its memory work."""

from agent_server.ui_common import BASE_CSS, header_html

_CSS = """
main { flex:1; width:100%; max-width:1120px; margin:0 auto; padding:22px 22px 40px; }
.hero { display:flex; align-items:flex-end; justify-content:space-between; gap:22px; flex-wrap:wrap; margin-bottom:20px; }
.hero h2 { margin:0 0 8px; font-size:27px; line-height:1.2; }
.hero h2 em { color:var(--mem); font-style:normal; }
.hero p { margin:0; max-width:620px; font-size:13.5px; color:var(--muted); line-height:1.6; }
.cta { display:flex; gap:10px; flex-wrap:wrap; }
.btn {
  border:0; border-radius:10px; padding:12px 20px; font-size:14px; font-weight:600;
  cursor:pointer; font-family:inherit; text-decoration:none; display:inline-block;
  background:var(--accent); color:#06241c;
}
.btn.ghost { background:transparent; color:var(--ink); border:1px solid #2a5c4c; }
.btn.ghost:hover { border-color:var(--mem); color:var(--mem); }

.stage { background:rgba(6,26,21,.5); border:1px solid var(--line); border-radius:14px; padding:8px 10px 4px; }
svg#arch { width:100%; height:auto; display:block; }

.nd rect { fill:var(--panel); stroke:var(--line); stroke-width:1.4; transition:all .25s ease; }
.nd .nt { fill:var(--ink); font-size:13px; font-weight:600; }
.nd .ns { fill:var(--muted); font-size:10.5px; }
.nd { cursor:pointer; }
.nd:hover rect { stroke:var(--accent); }
.nd.mem rect { fill:rgba(247,201,72,.09); stroke:rgba(247,201,72,.55); }
.nd.dat rect { fill:rgba(94,176,239,.08); stroke:rgba(94,176,239,.45); }
.nd.on rect { stroke:var(--accent); stroke-width:2.6; filter:drop-shadow(0 0 11px rgba(45,212,168,.6)); }
.nd.mem.on rect { stroke:var(--mem); filter:drop-shadow(0 0 12px rgba(247,201,72,.6)); }
.lbl { fill:var(--muted); font-size:10.5px; letter-spacing:.14em; }
.band { fill:rgba(247,201,72,.045); stroke:rgba(247,201,72,.4); stroke-width:1.2; stroke-dasharray:5 4; }
.bandlbl { fill:var(--mem); font-size:10.5px; letter-spacing:.16em; font-weight:600; }

path.edge { fill:none; stroke:#2f6a58; stroke-width:1.6; }
path.edge.memflow { stroke:rgba(247,201,72,.5); stroke-dasharray:6 5; }
path.edge.on { stroke:var(--accent); stroke-width:2.6; }
path.edge.memflow.on { stroke:var(--mem); stroke-width:2.6; animation:dash 1s linear infinite; }
@keyframes dash { to { stroke-dashoffset:-22; } }

.player { display:flex; align-items:center; gap:12px; flex-wrap:wrap; margin:16px 0 0; }
.player button {
  background:var(--panel); border:1px solid #2a5c4c; color:var(--ink); font-family:inherit;
  border-radius:8px; padding:8px 14px; font-size:12.5px; cursor:pointer;
}
.player button:hover { border-color:var(--accent); color:var(--accent); }
.dots { display:flex; gap:6px; }
.dot { width:8px; height:8px; border-radius:50%; background:#245647; cursor:pointer; border:0; padding:0; }
.dot.on { background:var(--mem); }
.step {
  margin-top:14px; background:var(--panel); border:1px solid var(--line); border-left:3px solid var(--mem);
  border-radius:10px; padding:13px 16px; min-height:66px;
}
.step h4 { margin:0 0 5px; font-size:13.5px; }
.step p { margin:0; font-size:12.5px; color:var(--muted); line-height:1.6; }

.detail { margin-top:16px; display:grid; grid-template-columns:1fr 260px; gap:14px; }
@media (max-width:820px) { .detail { grid-template-columns:1fr; } }
.card { background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:14px 16px; }
.card h4 { margin:0 0 7px; font-size:13.5px; }
.card p { margin:0; font-size:12.5px; color:var(--muted); line-height:1.6; }
.card code { background:#0a2620; border:1px solid var(--line); border-radius:5px; padding:1px 5px; font-size:11.5px; color:var(--accent); }
.meta div { font-size:11.5px; color:var(--muted); margin-bottom:9px; }
.meta div:last-child { margin-bottom:0; }
.meta span { display:block; color:#557f72; font-size:10px; letter-spacing:.1em; margin-bottom:2px; }
footer { text-align:center; font-size:11.5px; color:var(--muted); padding:0 22px 18px; }
"""

_SVG = """
<svg id="arch" viewBox="0 0 1060 610" role="img" aria-label="GulfNet Care Copilot architecture">
  <defs>
    <marker id="arw" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="#2f6a58"/>
    </marker>
    <marker id="arwm" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
      <path d="M0,0 L10,5 L0,10 z" fill="rgba(247,201,72,.75)"/>
    </marker>
  </defs>

  <rect class="band" x="30" y="44" width="1000" height="134" rx="14"/>
  <text class="bandlbl" x="48" y="66">MEMORY IN LAKEBASE POSTGRES</text>

  <g class="nd mem" data-id="m1">
    <rect x="58" y="82" width="452" height="76" rx="10"/>
    <text class="nt" x="76" y="110">Short-term &mdash; LangGraph checkpointer</text>
    <text class="ns" x="76" y="130">One row set per thread_id. Replays the conversation so</text>
    <text class="ns" x="76" y="146">follow-ups keep context without resending history.</text>
  </g>
  <g class="nd mem" data-id="m2">
    <rect x="550" y="82" width="452" height="76" rx="10"/>
    <text class="nt" x="568" y="110">Long-term &mdash; store + gte-large embeddings</text>
    <text class="ns" x="568" y="130">user_memories namespace per user. Preferences and travel</text>
    <text class="ns" x="568" y="146">notes survive across separate conversations.</text>
  </g>

  <text class="lbl" x="30" y="240">CARE CONSOLE</text>
  <text class="lbl" x="300" y="240">AGENT RUNTIME</text>
  <text class="lbl" x="560" y="240">AGENT TOOLS</text>
  <text class="lbl" x="820" y="240">LAKEBASE DATA</text>

  <path id="p_a1_b1" class="edge" d="M240,335 C270,335 270,307 300,307" marker-end="url(#arw)"/>
  <path id="p_b1_b2" class="edge" d="M405,342 V372" marker-end="url(#arw)"/>
  <path id="p_b2_c1" class="edge" d="M510,407 C540,407 540,286 560,286" marker-end="url(#arw)"/>
  <path id="p_b2_c2" class="edge" d="M510,407 C540,407 540,354 560,354" marker-end="url(#arw)"/>
  <path id="p_b2_c3" class="edge" d="M510,407 C540,407 540,422 560,422" marker-end="url(#arw)"/>
  <path id="p_b2_c4" class="edge" d="M510,407 C540,407 540,490 560,490" marker-end="url(#arw)"/>
  <path id="p_c1_d1" class="edge" d="M760,286 H820" marker-end="url(#arw)"/>
  <path id="p_c2_d2" class="edge" d="M760,354 H820" marker-end="url(#arw)"/>
  <path id="p_c4_d3" class="edge" d="M760,490 H820" marker-end="url(#arw)"/>
  <path id="p_w1_d3" class="edge" d="M925,536 V520" marker-end="url(#arw)"/>
  <path id="p_b1_m1" class="edge memflow" d="M370,272 V158" marker-end="url(#arwm)" marker-start="url(#arwm)"/>
  <path id="p_b1_m2" class="edge memflow" d="M440,272 V210 H870 V158" marker-end="url(#arwm)"/>
  <path id="p_c3_m2" class="edge memflow" d="M760,422 H790 V158" marker-end="url(#arwm)"/>

  <g class="nd" data-id="a1">
    <rect x="30" y="300" width="210" height="70" rx="10"/>
    <text class="nt" x="48" y="330">Care console</text>
    <text class="ns" x="48" y="350">Chat + live agent flow</text>
  </g>
  <g class="nd" data-id="b1">
    <rect x="300" y="272" width="210" height="70" rx="10"/>
    <text class="nt" x="318" y="302">Agent server</text>
    <text class="ns" x="318" y="322">FastAPI, streams SSE</text>
  </g>
  <g class="nd" data-id="b2">
    <rect x="300" y="372" width="210" height="70" rx="10"/>
    <text class="nt" x="318" y="402">LangGraph + Claude 4.5</text>
    <text class="ns" x="318" y="422">Reasons, picks tools</text>
  </g>

  <g class="nd" data-id="c1">
    <rect x="560" y="258" width="200" height="56" rx="9"/>
    <text class="nt" x="576" y="282">Care tools</text>
    <text class="ns" x="576" y="300">subscriber, usage, plans</text>
  </g>
  <g class="nd" data-id="c2">
    <rect x="560" y="326" width="200" height="56" rx="9"/>
    <text class="nt" x="576" y="350">search_knowledge</text>
    <text class="ns" x="576" y="368">hybrid retrieval</text>
  </g>
  <g class="nd" data-id="c3">
    <rect x="560" y="394" width="200" height="56" rx="9"/>
    <text class="nt" x="576" y="418">Memory tools</text>
    <text class="ns" x="576" y="436">get / save / delete</text>
  </g>
  <g class="nd" data-id="c4">
    <rect x="560" y="462" width="200" height="56" rx="9"/>
    <text class="nt" x="576" y="486">Ops queue tools</text>
    <text class="ns" x="576" y="504">enqueue / status</text>
  </g>

  <g class="nd dat" data-id="d1">
    <rect x="820" y="258" width="210" height="56" rx="9"/>
    <text class="nt" x="836" y="282">gulfnet OLTP</text>
    <text class="ns" x="836" y="300">subscribers, usage, tickets</text>
  </g>
  <g class="nd dat" data-id="d2">
    <rect x="820" y="326" width="210" height="56" rx="9"/>
    <text class="nt" x="836" y="350">kb_chunks</text>
    <text class="ns" x="836" y="368">tsvector + embedding</text>
  </g>
  <g class="nd dat" data-id="d3">
    <rect x="820" y="462" width="210" height="56" rx="9"/>
    <text class="nt" x="836" y="486">tasks queue</text>
    <text class="ns" x="836" y="504">FOR UPDATE SKIP LOCKED</text>
  </g>
  <g class="nd" data-id="w1">
    <rect x="560" y="536" width="470" height="48" rx="9"/>
    <text class="nt" x="578" y="558">Queue worker / Lakeflow job</text>
    <text class="ns" x="578" y="574">Leases, retries, expired-lease recovery</text>
  </g>
</svg>
"""

_JS = """
const DETAIL = {
  m1: {t:"Short-term memory: the LangGraph checkpointer",
       b:"Every turn is checkpointed against the conversation's <code>thread_id</code>. The browser only ever sends the newest message; LangGraph replays the stored turns, so the agent keeps context inside a conversation.",
       f:"agent_server/utils_memory.py", o:"checkpointer tables in the memory schema"},
  m2: {t:"Long-term memory: the Databricks store",
       b:"Durable facts are written to a <code>user_memories</code> namespace keyed by user, embedded with gte-large for semantic lookup. This is what survives when a conversation ends. Recall does not depend on the model choosing a tool: the server reads the store itself and injects what it finds into the first turn.",
       f:"agent_server/utils_memory.py", o:"store tables + embeddings"},
  a1: {t:"Care console",
       b:"The page a care agent actually uses. It streams the reply token by token and renders every tool call live in the left rail, so you can watch which Lakebase objects the agent touches.",
       f:"agent_server/ui_chat.py", o:"browser only"},
  b1: {t:"Agent server",
       b:"FastAPI behind Databricks Apps SSO. It resolves the thread, loads memory, runs the graph, and streams <code>response.*</code> events over SSE. It also hosts the ops dashboard and the queue worker.",
       f:"agent_server/start_server.py", o:"n/a"},
  b2: {t:"LangGraph agent + Claude Sonnet 4.5",
       b:"The reasoning loop, wired to the checkpointer and the store. The model needs dependable multi-step tool calling: a weaker model wrote tool calls as plain text instead of invoking them, which silently dropped memory writes.",
       f:"agent_server/agent.py", o:"n/a"},
  c1: {t:"Care tools",
       b:"<code>lookup_subscriber</code>, <code>get_usage_summary</code>, <code>recommend_plan</code> and <code>create_support_ticket</code> read and write the operational tables directly in Postgres. No warehouse hop.",
       f:"agent_server/tools_gulfnet.py", o:"subscribers, plans, usage_daily, tickets"},
  c2: {t:"Hybrid knowledge search",
       b:"Tariff, roaming and SLA questions are grounded in the knowledge base rather than guessed. Full-text ranking today, with a Lakebase Search hook behind <code>USE_LAKEBASE_SEARCH</code>.",
       f:"agent_server/search.py", o:"kb_documents, kb_chunks"},
  c3: {t:"Memory tools",
       b:"<code>save_user_memory</code> is the write path the model drives when a care agent states something durable, such as a language preference or upcoming travel. <code>get_user_memory</code> covers targeted lookups beyond the auto-injected set.",
       f:"agent_server/utils_memory.py", o:"store: user_memories"},
  c4: {t:"Ops queue tools",
       b:"Work too slow for a chat turn is handed to Postgres instead of blocking the reply. The agent enqueues a task and can report status later.",
       f:"agent_server/orchestration.py", o:"tasks, task_attempts"},
  d1: {t:"Operational tables",
       b:"The synthetic GulfNet business data: subscribers, plans, daily usage, tickets and network events. Same Postgres instance as the agent's memory, so a tool call is just a query.",
       f:"sql/01_schema.sql", o:"gulfnet schema"},
  d2: {t:"Knowledge chunks",
       b:"Policy documents chunked with a generated <code>tsvector</code> column plus an embedding column, giving lexical and semantic retrieval from one table.",
       f:"sql/01_schema.sql", o:"kb_chunks"},
  d3: {t:"Postgres-native task queue",
       b:"Dequeue uses <code>FOR UPDATE SKIP LOCKED</code> with leases and priority, so several workers can share the queue without double-processing. A trigger emits NOTIFY for the dashboard's live stream.",
       f:"agent_server/orchestration.py", o:"tasks, task_attempts"},
  w1: {t:"Queue worker",
       b:"Runs in-app on a poll loop and as a Lakeflow job for heavier batches. Claims a task, renews its lease, then completes or fails it; expired leases are recovered so nothing gets stuck.",
       f:"jobs/process_queue.py", o:"tasks"}
};

const STEPS = [
  {t:"A care agent asks a question",
   d:"The browser posts only the newest message to the agent server and opens an SSE stream for the reply.",
   n:["a1","b1"], p:["p_a1_b1"]},
  {t:"The thread checkpoint is loaded",
   d:"Short-term memory. If this thread already has turns, LangGraph replays them, so the agent remembers what was said a moment ago.",
   n:["b1","m1"], p:["p_b1_m1"]},
  {t:"Long-term memory is injected",
   d:"On the first turn of a conversation the server reads user_memories itself and puts what it finds into context. Recall never depends on the model deciding to call a tool.",
   n:["b1","m2"], p:["p_b1_m2"]},
  {t:"The model reasons with memory already in context",
   d:"Known preferences are present before the first token is generated, so the agent does not ask the care agent to repeat themselves.",
   n:["b2","m2"], p:["p_b1_b2"]},
  {t:"Business questions hit the operational tables",
   d:"Subscriber, usage and plan tools query Postgres directly. Memory and business data live in the same instance.",
   n:["b2","c1","d1"], p:["p_b2_c1","p_c1_d1"]},
  {t:"Policy questions are grounded in hybrid search",
   d:"Roaming rules, tariffs and SLA answers come from kb_chunks rather than from the model's imagination.",
   n:["b2","c2","d2"], p:["p_b2_c2","p_c2_d2"]},
  {t:"Durable facts are written back",
   d:"When the care agent states a preference or a travel plan, save_user_memory persists it to the long-term store, ready for every future conversation.",
   n:["b2","c3","m2"], p:["p_b2_c3","p_c3_m2"]},
  {t:"Slow work goes to the Postgres queue",
   d:"A VIP outage impact report is enqueued instead of stalling the chat. Workers claim tasks with SKIP LOCKED and leases.",
   n:["b2","c4","d3","w1"], p:["p_b2_c4","p_c4_d3","p_w1_d3"]},
  {t:"The answer streams back and the turn is checkpointed",
   d:"Tokens reach the console as they are produced, and the completed turn is appended to short-term memory for the next question.",
   n:["b1","a1","m1"], p:["p_a1_b1","p_b1_m1"]}
];

const svg = document.getElementById("arch");
const stepBox = document.getElementById("stepbox");
const dots = document.getElementById("dots");
const dTitle = document.getElementById("d-title");
const dBody = document.getElementById("d-body");
const dFile = document.getElementById("d-file");
const dObj = document.getElementById("d-obj");

function clearHl() {
  svg.querySelectorAll(".nd.on").forEach(e => e.classList.remove("on"));
  svg.querySelectorAll("path.edge.on").forEach(e => e.classList.remove("on"));
}

function showDetail(id) {
  const d = DETAIL[id];
  if (!d) return;
  dTitle.textContent = d.t;
  dBody.innerHTML = d.b;
  dFile.textContent = d.f;
  dObj.textContent = d.o;
}

svg.querySelectorAll(".nd").forEach(g => {
  const id = g.getAttribute("data-id");
  g.addEventListener("click", () => { pause(); clearHl(); g.classList.add("on"); showDetail(id); });
  g.addEventListener("mouseenter", () => showDetail(id));
});

let idx = 0, timer = null;

STEPS.forEach((s, i) => {
  const b = document.createElement("button");
  b.className = "dot";
  b.title = s.t;
  b.onclick = () => { pause(); render(i); };
  dots.appendChild(b);
});

function render(i) {
  idx = ((i % STEPS.length) + STEPS.length) % STEPS.length;
  const s = STEPS[idx];
  clearHl();
  s.n.forEach(n => { const el = svg.querySelector('[data-id="' + n + '"]'); if (el) el.classList.add("on"); });
  s.p.forEach(p => { const el = document.getElementById(p); if (el) el.classList.add("on"); });
  stepBox.innerHTML = "";
  const h = document.createElement("h4");
  h.textContent = (idx + 1) + ". " + s.t;
  const p = document.createElement("p");
  p.textContent = s.d;
  stepBox.appendChild(h); stepBox.appendChild(p);
  [...dots.children].forEach((d, j) => d.classList.toggle("on", j === idx));
  const first = s.n[0];
  if (DETAIL[first]) showDetail(first);
}

const playBtn = document.getElementById("play");
function play() {
  if (timer) return;
  playBtn.textContent = "Pause";
  timer = setInterval(() => render(idx + 1), 3200);
}
function pause() {
  if (!timer) return;
  clearInterval(timer); timer = null;
  playBtn.textContent = "Play flow";
}
playBtn.onclick = () => (timer ? pause() : play());
document.getElementById("prev").onclick = () => { pause(); render(idx - 1); };
document.getElementById("next").onclick = () => { pause(); render(idx + 1); };
document.getElementById("replay").onclick = () => { pause(); render(0); play(); };

render(0);
play();
"""

LANDING_HTML = (
    """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>GulfNet Care Copilot &mdash; architecture</title>
<style>"""
    + BASE_CSS
    + _CSS
    + """</style>
</head>
<body>
__HEADER__
<main>
  <section class="hero">
    <div>
      <h2>One Postgres behind the agent &mdash; including <em>its memory</em></h2>
      <p>GulfNet is a fictional UAE operator. Its care copilot keeps conversation state,
      long-term customer preferences, knowledge retrieval and background task orchestration
      in a single Lakebase Postgres instance. Click any block to see what it does, or play
      the flow to watch a question travel through memory and back.</p>
    </div>
    <div class="cta">
      <a class="btn" href="/chat">Get started &rarr;</a>
      <a class="btn ghost" href="/ops/dashboard">Ops dashboard</a>
    </div>
  </section>

  <div class="stage">"""
    + _SVG
    + """</div>

  <div class="player">
    <button id="play">Play flow</button>
    <button id="prev">Prev</button>
    <button id="next">Next</button>
    <button id="replay">Replay</button>
    <div class="dots" id="dots"></div>
  </div>

  <div class="step" id="stepbox"></div>

  <div class="detail">
    <div class="card">
      <h4 id="d-title">Pick a block</h4>
      <p id="d-body">Hover or click any block in the diagram to see what it does and where it is implemented.</p>
    </div>
    <div class="card meta">
      <div><span>IMPLEMENTED IN</span><code id="d-file">&mdash;</code></div>
      <div><span>LAKEBASE OBJECT</span><code id="d-obj">&mdash;</code></div>
    </div>
  </div>
</main>
<footer>Fictional operator &middot; synthetic data only</footer>
<script>"""
    + _JS
    + """</script>
</body>
</html>
"""
).replace("__HEADER__", header_html("home"))
