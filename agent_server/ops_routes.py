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


DASHBOARD_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>GulfNet Ops — Lakebase Queue</title>
  <style>
    :root {
      --bg: #0b1f1a;
      --panel: #12352c;
      --ink: #e8f5f0;
      --muted: #8fb3a8;
      --accent: #2dd4a8;
      --warn: #f0b429;
      --bad: #f07178;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      background: radial-gradient(1200px 600px at 10% -10%, #1a4d3f 0%, var(--bg) 55%);
      color: var(--ink); min-height: 100vh;
    }
    header {
      padding: 1.5rem 2rem; border-bottom: 1px solid #1f4a3d;
      display: flex; justify-content: space-between; align-items: baseline; gap: 1rem;
    }
    h1 { margin: 0; font-size: 1.35rem; letter-spacing: 0.02em; }
    h1 span { color: var(--accent); }
    .sub { color: var(--muted); font-size: 0.9rem; }
    main { padding: 1.5rem 2rem; display: grid; gap: 1.25rem; }
    .counts { display: flex; flex-wrap: wrap; gap: 0.75rem; }
    .pill {
      background: var(--panel); border: 1px solid #1f4a3d; border-radius: 999px;
      padding: 0.45rem 0.9rem; font-size: 0.85rem;
    }
    .pill strong { color: var(--accent); }
    table { width: 100%; border-collapse: collapse; background: var(--panel);
      border-radius: 12px; overflow: hidden; border: 1px solid #1f4a3d; }
    th, td { text-align: left; padding: 0.7rem 0.9rem; border-bottom: 1px solid #1a3d33;
      font-size: 0.88rem; }
    th { color: var(--muted); font-weight: 600; }
    .status-enqueued { color: var(--warn); }
    .status-processing { color: var(--accent); }
    .status-completed { color: #7dcea0; }
    .status-failed { color: var(--bad); }
    .actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }
    button {
      background: var(--accent); color: #06241c; border: 0; border-radius: 8px;
      padding: 0.55rem 0.9rem; font-weight: 600; cursor: pointer;
    }
    button.secondary { background: transparent; color: var(--ink); border: 1px solid #2a5c4c; }
    #live { font-size: 0.8rem; color: var(--muted); }
  </style>
</head>
<body>
  <header>
    <div>
      <h1><span>GulfNet</span> Ops Dashboard</h1>
      <div class="sub">Lakebase Postgres task queue · VIP impact · churn batches</div>
    </div>
    <div id="live">connecting…</div>
  </header>
  <main>
    <div class="actions">
      <button onclick="enqueueVip()">Enqueue VIP Marina impact</button>
      <button class="secondary" onclick="tick()">Run worker tick</button>
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
      document.getElementById('live').textContent = 'live · ' + new Date().toLocaleTimeString();
      render(JSON.parse(ev.data));
    };
    es.onerror = () => { document.getElementById('live').textContent = 'reconnecting…'; };
  </script>
</body>
</html>
"""


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    return HTMLResponse(DASHBOARD_HTML)
