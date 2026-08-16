# GulfNet Care Copilot

Reusable end-to-end demo: a **UAE telco Care Copilot** on Databricks Apps + **Lakebase Postgres**, showcasing three pillars in one backend:

1. **Self-managed agent memory** (short-term threads + long-term preferences)  
2. **Hybrid knowledge retrieval** (tariffs / roaming / SLA — Lakebase Search-ready)  
3. **Postgres task orchestration** (VIP outage impact queue + ops SSE dashboard)

Fictional operator **GulfNet** — synthetic data only. Built for Medium / customer demos and easy reuse under [github.com/mwissad](https://github.com/mwissad).

## Architecture

```
Chat UI + /ops/dashboard  →  LangGraph agent (Databricks App)
                                │
                     Lakebase Autoscaling Postgres
                     ├─ gulfnet_agent_memory (checkpoints / store)
                     ├─ gulfnet.* OLTP + kb_chunks
                     └─ gulfnet.tasks / task_attempts
                                │
                     In-app worker or Lakeflow Job
```

Workspace used in development: `https://fevm-mw-aws-demo.cloud.databricks.com`  
Lakebase project: `gulfnet-agent` (branch `production`, database `gulfnet`).

## Quickstart (≈10 minutes)

### Prerequisites

- Databricks CLI **≥ 0.285** with `databricks postgres` (this repo was validated with 0.295)
- `psql` client
- Python 3.11+ and [uv](https://github.com/astral-sh/uv)
- FE-VM / serverless workspace with Lakebase + Foundation Model endpoints

### 1. Clone and configure

```bash
git clone https://github.com/mwissad/gulfnet-lakebase-agent.git
cd gulfnet-lakebase-agent
cp .env.example .env
# Edit DATABRICKS_CONFIG_PROFILE and paths as needed
```

### 2. Authenticate

```bash
databricks auth login https://<your-workspace> --profile <profile>
```

### 3. Create Lakebase + seed

```bash
# Create project (once)
databricks postgres create-project gulfnet-agent \
  --json '{"spec": {"display_name": "GulfNet Care Agent"}}' \
  -p <profile> --no-wait

# Wait until endpoint ACTIVE, then:
PROFILE=<profile> ./scripts/setup_lakebase.sh
```

### 4. Install and smoke-test tools (no LLM)

```bash
uv sync
uv run python scripts/smoke_test_tools.py
```

### 5. Run the app locally

```bash
uv run start-app
# Chat UI (if bundled) + API on :8000
# Ops dashboard: http://localhost:8000/ops/dashboard
```

### 6. Deploy with Asset Bundle

```bash
databricks bundle validate -t dev -p <profile>
databricks bundle deploy -t dev -p <profile>
# Grant App SP permissions (see scripts/grant_lakebase_permissions.py)
```

## Agent tools

| Tool | Purpose |
|------|---------|
| `lookup_subscriber` | MSISDN / account profile + plan |
| `get_usage_summary` | Data / voice / roaming usage |
| `search_knowledge` | Hybrid KB retrieval |
| `check_network_status` | Synthetic outages by emirate / cell |
| `recommend_plan` | Intent-based plan suggestions |
| `create_support_ticket` | Write ticket row |
| `enqueue_ops_task` | Postgres queue (`vip_outage_impact`, `churn_offer_batch`) |
| `get_task_status` | Poll task result |
| Memory tools | `get/save/delete_user_memory` |

## Golden demos

See [`demos/GOLDEN_SCRIPTS.md`](demos/GOLDEN_SCRIPTS.md). Seed VIP: **+971501234567** (Layla Al Mansoori).

## Medium article

Draft: [`article/medium-draft.md`](article/medium-draft.md)

References:

- [Simplify AI agent orchestration with Lakebase Postgres](https://www.databricks.com/blog/simplify-ai-agent-orchestration-lakebase-postgres)
- [Self-managed agent memory](https://docs.databricks.com/aws/en/agents/agent-memory/self-managed-memory)
- [Lakebase Search](https://www.databricks.com/blog/announcing-lakebase-search-agent-native-retrieval-built-lakebase-postgres)

## Reusing for another industry

1. Replace `sql/02_seed.sql` and KB chunks  
2. Keep the tool surface area (lookup → search → enqueue)  
3. Point `databricks.yml` at your Lakebase branch/database  
4. Do not commit `.env` or workspace tokens  

## License

Demo code provided as-is for field engineering / educational reuse.
