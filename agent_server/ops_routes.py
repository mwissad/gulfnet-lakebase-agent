"""Ops dashboard API + SSE for GulfNet task queue."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel, Field

from agent_server import orchestration as orch
from agent_server.ui_common import BASE_CSS, FAVICON, header_html

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ops", tags=["ops"])


class EnqueueRequest(BaseModel):
    task_type: str = Field(..., examples=["vip_outage_impact"])
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = 80


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "gulfnet-ops"}


@router.get("/tasks")
def list_tasks(limit: int = 50) -> dict[str, Any]:
    return {"tasks": orch.list_tasks(limit=limit), "counts": orch.task_counts()}


@router.get("/tasks/{task_id}")
def get_task(task_id: str) -> dict[str, Any]:
    task = orch.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="task not found")
    return task


@router.post("/tasks")
def enqueue(req: EnqueueRequest) -> dict[str, Any]:
    return orch.enqueue_task(req.task_type, req.payload, req.priority)


@router.post("/worker/tick")
def worker_tick() -> dict[str, Any]:
    """Process at most one queued task (also used by Jobs / cron)."""
    result = orch.process_one_task()
    return result or {"status": "idle"}


@router.get("/events")
async def task_events():
    """SSE stream of task queue snapshots (poll fallback; LISTEN/NOTIFY optional)."""

    async def gen():
        while True:
            try:
                payload = {
                    "counts": orch.task_counts(),
                    "tasks": orch.list_tasks(limit=20),
                }
                yield f"data: {json.dumps(payload, default=str)}\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(gen(), media_type="text/event-stream")


DASHBOARD_HTML = ("""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GulfNet Ops &mdash; Lakebase queue</title>
__FAVICON__
  <style>""" + BASE_CSS + """
    main { padding:20px 22px; display:grid; gap:16px; }
    .actions { display:flex; gap:9px; flex-wrap:wrap; align-items:center; }
    button {
      background:var(--lava); color:#fff; border:0; border-radius:7px;
      padding:10px 18px; font-weight:600; font-size:13px; cursor:pointer; font-family:inherit;
    }
    button:hover { background:var(--lava-dim); }
    button.secondary { background:rgba(27,49,57,.6); color:var(--oat); border:1px solid var(--line); }
    button.secondary:hover { border-color:var(--lava); color:var(--lava); background:rgba(255,54,33,.08); }
    #live { font-size:12px; color:var(--muted); margin-left:auto; display:flex; align-items:center; gap:7px; }
    #live .led { width:7px; height:7px; border-radius:50%; background:var(--green); }
    .counts { display:flex; flex-wrap:wrap; gap:9px; }
    .pill {
      background:var(--navy-800); border:1px solid var(--line); border-radius:999px;
      padding:7px 14px; font-size:12.5px;
    }
    .pill strong { color:var(--lava); }
    table {
      width:100%; border-collapse:collapse; background:var(--navy-800);
      border-radius:8px; overflow:hidden; border:1px solid var(--line);
    }
    th, td { text-align:left; padding:11px 14px; border-bottom:1px solid var(--line); font-size:12.5px; }
    th { color:var(--muted); font-weight:600; letter-spacing:.06em; font-size:11px; text-transform:uppercase; }
    tr:last-child td { border-bottom:0; }
    .status-enqueued { color:var(--maize); }
    .status-processing { color:var(--blue); }
    .status-completed { color:var(--green); }
    .status-failed { color:var(--err); }
  </style>
</head>
<body>
__HEADER__
  <main>
    <div class="actions">
      <button onclick="enqueueVip()">Enqueue VIP Marina impact</button>
      <button class="secondary" onclick="tick()">Run worker tick</button>
      <div id="live"><span class="led"></span><span id="livetext">connecting&hellip;</span></div>
    </div>
    <div class="counts" id="counts"></div>
    <table>
      <thead>
        <tr><th>Task</th><th>Type</th><th>Status</th><th>Priority</th><th>Updated</th></tr>
      </thead>
      <tbody id="rows"></tbody>
    </table>
  </main>
  <script>
    function render(data) {
      const counts = data.counts || {};
      document.getElementById('counts').innerHTML = Object.entries(counts)
        .map(([k,v]) => `<div class="pill"><strong>${v}</strong> ${k}</div>`).join('') || '<div class="pill">no tasks</div>';
      const rows = (data.tasks || []).map(t => `
        <tr>
          <td>${t.task_id}</td>
          <td>${t.task_type}</td>
          <td class="status-${t.status}">${t.status}</td>
          <td>${t.priority}</td>
          <td>${t.updated_at || t.created_at || ''}</td>
        </tr>`).join('');
      document.getElementById('rows').innerHTML = rows || '<tr><td colspan="5">Queue empty</td></tr>';
    }
    async function enqueueVip() {
      await fetch('/ops/tasks', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          task_type: 'vip_outage_impact',
          payload: {emirate: 'Dubai', cell_area: 'Dubai Marina'},
          priority: 90
        })
      });
    }
    async function tick() { await fetch('/ops/worker/tick', {method: 'POST'}); }
    const es = new EventSource('/ops/events');
    es.onmessage = (ev) => {
      document.getElementById('livetext').textContent = 'live · ' + new Date().toLocaleTimeString();
      render(JSON.parse(ev.data));
    };
    es.onerror = () => { document.getElementById('livetext').textContent = 'reconnecting…'; };
  </script>
</body>
</html>
""").replace("__HEADER__", header_html("ops")).replace("__FAVICON__", FAVICON)


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    return HTMLResponse(DASHBOARD_HTML)
