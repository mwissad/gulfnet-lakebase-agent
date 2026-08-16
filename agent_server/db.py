"""Lakebase connection helpers for GulfNet OLTP / search / orchestration.

Works both locally (CLI OAuth) and in Databricks Apps (SDK + injected PG* env).
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from contextlib import contextmanager
from typing import Any, Iterator, Optional
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)


def _is_databricks_app() -> bool:
    return bool(os.getenv("DATABRICKS_APP_NAME"))


def _run_json(cmd: list[str]) -> Any:
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def _endpoint_path() -> str:
    explicit = os.getenv("LAKEBASE_AUTOSCALING_ENDPOINT") or os.getenv("ENDPOINT_NAME")
    if explicit and explicit.startswith("projects/"):
        return explicit
    project = os.getenv("LAKEBASE_AUTOSCALING_PROJECT", "gulfnet-agent")
    branch = os.getenv("LAKEBASE_AUTOSCALING_BRANCH", "production")
    endpoint = os.getenv("LAKEBASE_ENDPOINT_ID", "primary")
    if explicit and not explicit.startswith("projects/"):
        # Short endpoint id / uid from value_from postgres
        return f"projects/{project}/branches/{branch}/endpoints/{explicit}"
    return f"projects/{project}/branches/{branch}/endpoints/{endpoint}"


def get_connection_params(
    profile: Optional[str] = None,
    project: Optional[str] = None,
    branch: Optional[str] = None,
    endpoint: Optional[str] = None,
    database: Optional[str] = None,
) -> dict[str, str]:
    """Resolve host/user/password for Lakebase Autoscaling."""
    database = database or os.getenv("GULFNET_DATABASE", "gulfnet")

    # --- Databricks Apps path (preferred when deployed) ---
    if _is_databricks_app() or os.getenv("PGHOST"):
        host = os.getenv("LAKEBASE_HOST") or os.getenv("PGHOST")
        user = os.getenv("LAKEBASE_USER") or os.getenv("PGUSER")
        port = os.getenv("PGPORT", "5432")
        if not host or not user:
            raise RuntimeError(
                "PGHOST/PGUSER (or LAKEBASE_HOST/LAKEBASE_USER) required in Apps environment"
            )
        token = os.getenv("LAKEBASE_TOKEN")
        if not token:
            from databricks.sdk import WorkspaceClient

            w = WorkspaceClient()
            ep = _endpoint_path()
            # SDK postgres credential API (autoscaling)
            try:
                cred = w.postgres.generate_database_credential(endpoint=ep)
                token = cred.token
            except Exception:
                # Fallback for older SDK shapes
                cred = w.database.generate_database_credential(instance_names=[ep])
                token = cred.token
        return {
            "host": host,
            "port": port,
            "dbname": database,
            "user": user,
            "password": token,
            "sslmode": os.getenv("PGSSLMODE", "require"),
        }

    # --- Local CLI path ---
    profile = profile or os.getenv("DATABRICKS_CONFIG_PROFILE", "fe-vm-mw-aws-demo")
    project = project or os.getenv("LAKEBASE_AUTOSCALING_PROJECT", "gulfnet-agent")
    branch = branch or os.getenv("LAKEBASE_AUTOSCALING_BRANCH", "production")
    endpoint = endpoint or os.getenv("LAKEBASE_ENDPOINT_ID", "primary")
    dbx = os.getenv("DATABRICKS_CLI_PATH", "databricks")
    branch_path = f"projects/{project}/branches/{branch}"
    endpoint_path = _endpoint_path()

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
