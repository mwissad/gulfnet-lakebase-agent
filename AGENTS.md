# GulfNet Care Copilot — agent notes

This repo is a Databricks Apps + Lakebase demo for a fictional UAE telco (**GulfNet**).

## Pillars

- **Memory:** `agent_server/utils_memory.py` — LangGraph checkpointer + long-term store
- **Tools:** `agent_server/tools_gulfnet.py` — subscriber / usage / KB / network / tickets / queue
- **Search:** `agent_server/search.py` — FTS hybrid; Lakebase Search hook via `USE_LAKEBASE_SEARCH`
- **Orchestration:** `agent_server/orchestration.py` + `/ops/*` routes

## Local commands

```bash
PROFILE=fe-vm-mw-aws-demo ./scripts/setup_lakebase.sh
uv sync && uv run python scripts/smoke_test_tools.py
uv run start-app
```

Ops dashboard: `http://localhost:8000/ops/dashboard`

## Golden MSISDN

`+971501234567` — Layla Al Mansoori (VIP, Dubai, Arabic, WhatsApp)
