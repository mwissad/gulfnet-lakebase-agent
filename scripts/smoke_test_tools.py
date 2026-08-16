"""Smoke-test GulfNet tools against Lakebase (no LLM required)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")
os.environ.setdefault("DATABRICKS_CLI_PATH", os.getenv("DATABRICKS_CLI_PATH", "databricks"))


def main() -> None:
    from agent_server.orchestration import enqueue_task, process_one_task
    from agent_server.search import hybrid_search
    from agent_server.tools_gulfnet import lookup_subscriber

    print("== lookup ==")
    print(lookup_subscriber.invoke({"msisdn_or_account": "+971501234567"}))

    print("== search ==")
    print(json.dumps(hybrid_search("Riyadh roaming Saudi", limit=3), default=str, indent=2))

    print("== enqueue + process ==")
    task = enqueue_task(
        "vip_outage_impact",
        {"emirate": "Dubai", "cell_area": "Dubai Marina"},
        priority=95,
    )
    print(task)
    print(process_one_task())


if __name__ == "__main__":
    main()
