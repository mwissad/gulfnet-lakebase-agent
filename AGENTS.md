# GulfNet Care Copilot — agent notes

This repo is a Databricks Apps + Lakebase demo for a fictional UAE telco (**GulfNet**).

## Pillars

- **Memory:** `agent_server/utils_memory.py` — LangGraph checkpointer + long-term store
- **Tools:** `agent_server/tools_gulfnet.py` — subscriber / usage / KB / network / tickets / queue
- **Search:** `agent_server/search.py` — FTS hybrid; Lakebase Search hook via `USE_LAKEBASE_SEARCH`
- **Orchestration:** `agent_server/orchestration.py` + `/ops/*` routes
- **UI:** `agent_server/ui_landing.py` (interactive architecture at `/`),
  `agent_server/ui_chat.py` (chat + live flow rail at `/chat`), wired in `ui_routes.py`

Long-term recall does not rely on the model calling `get_user_memory`: the server reads the
store and injects memories on the first turn of a thread. Keep `LLM_ENDPOINT_NAME` on a model
with dependable multi-step tool calling — weaker ones emit tool calls as plain text and
silently drop memory writes.

## Local commands

```bash
PROFILE=fe-vm-mw-aws-demo ./scripts/setup_lakebase.sh
uv sync && uv run python scripts/smoke_test_tools.py
uv run start-app
```

Ops dashboard: `http://localhost:8000/ops/dashboard`

## Golden MSISDN

`+971501234567` — Layla Al Mansoori (VIP, Dubai, Arabic, WhatsApp)
