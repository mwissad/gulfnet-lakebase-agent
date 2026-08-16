"""Lakeflow / Jobs entrypoint: drain one GulfNet queue task.

Deployed via databricks.yml (paused schedule by default).
Can also be run locally:

  DATABRICKS_CONFIG_PROFILE=fe-vm-mw-aws-demo \\
  DATABRICKS_CLI_PATH=/tmp/databricks_cli_new/databricks \\
  python jobs/process_queue.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def main() -> None:
    # Ensure CLI path for OAuth credential generation
    os.environ.setdefault("DATABRICKS_CLI_PATH", os.getenv("DATABRICKS_CLI_PATH", "databricks"))
    from agent_server.orchestration import process_one_task, task_counts

    result = process_one_task()
    print(json.dumps({"result": result, "counts": task_counts()}, default=str))


if __name__ == "__main__":
    main()
