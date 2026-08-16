"""Lakebase connection helpers for GulfNet OLTP / search / orchestration."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from contextlib import contextmanager
from typing import Any, Iterator, Optional
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


def _run_json(cmd: list[str]) -> Any:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def get_connection_params(
    profile: Optional[str] = None,
    project: Optional[str] = None,
    branch: Optional[str] = None,
    endpoint: Optional[str] = None,
    database: Optional[str] = None,
) -> dict[str, str]:
    """Resolve host/user/password for Lakebase Autoscaling via CLI OAuth."""
    profile = profile or os.getenv("DATABRICKS_CONFIG_PROFILE", "fe-vm-mw-aws-demo")
    project = project or os.getenv("LAKEBASE_AUTOSCALING_PROJECT", "gulfnet-agent")
    branch = branch or os.getenv("LAKEBASE_AUTOSCALING_BRANCH", "production")
    endpoint = endpoint or os.getenv("LAKEBASE_ENDPOINT_ID", "primary")
    database = database or os.getenv("GULFNET_DATABASE", "gulfnet")

    dbx = os.getenv("DATABRICKS_CLI_PATH", "databricks")
    branch_path = f"projects/{project}/branches/{branch}"
    endpoint_path = f"{branch_path}/endpoints/{endpoint}"

    # Prefer explicit host override (useful in Apps)
    host = os.getenv("LAKEBASE_HOST")
    if not host:
        endpoints = _run_json(
            [dbx, "postgres", "list-endpoints", branch_path, "--profile", profile, "--output", "json"]
        )
        host = endpoints[0]["status"]["hosts"]["host"]

    token = os.getenv("LAKEBASE_TOKEN")
    if not token:
        cred = _run_json(
            [
                dbx,
                "postgres",
                "generate-database-credential",
                endpoint_path,
                "--profile",
                profile,
                "--output",
                "json",
            ]
        )
        token = cred["token"]

    user = os.getenv("LAKEBASE_USER")
    if not user:
        me = _run_json([dbx, "current-user", "me", "--profile", profile, "--output", "json"])
        user = me["userName"]

    return {
        "host": host,
        "port": "5432",
        "dbname": database,
        "user": user,
        "password": token,
        "sslmode": "require",
    }


def sqlalchemy_url(params: Optional[dict[str, str]] = None) -> str:
    p = params or get_connection_params()
    return (
        f"postgresql+psycopg://{quote_plus(p['user'])}:{quote_plus(p['password'])}"
        f"@{p['host']}:{p['port']}/{p['dbname']}?sslmode={p['sslmode']}"
    )


@contextmanager
def get_connection() -> Iterator[Any]:
    """Yield a psycopg connection (sync)."""
    import psycopg

    params = get_connection_params()
    conn = psycopg.connect(
        host=params["host"],
        port=int(params["port"]),
        dbname=params["dbname"],
        user=params["user"],
        password=params["password"],
        sslmode=params["sslmode"],
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(sql: str, args: tuple | dict | None = None) -> list[dict[str, Any]]:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            if cur.description is None:
                return []
            cols = [d.name for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]


def execute(sql: str, args: tuple | dict | None = None) -> None:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, args)
