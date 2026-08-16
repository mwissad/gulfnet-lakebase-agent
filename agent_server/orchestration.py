"""Postgres-native task queue for GulfNet ops agents.

Patterns from:
https://www.databricks.com/blog/simplify-ai-agent-orchestration-lakebase-postgres
- FOR UPDATE SKIP LOCKED
- lease-based crash recovery
- priority dequeue
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from agent_server.db import execute, fetch_all, get_connection

logger = logging.getLogger(__name__)

LEASE_SECONDS = 300
WORKER_ID = "gulfnet-worker-1"


def enqueue_task(task_type: str, payload: dict[str, Any], priority: int = 50) -> dict[str, Any]:
    rows = fetch_all(
        """
        INSERT INTO gulfnet.tasks (task_type, status, priority, payload)
        VALUES (%s, 'enqueued', %s, %s::jsonb)
        RETURNING task_id, task_type, status, priority, payload, created_at
        """,
        (task_type, priority, json.dumps(payload)),
    )
    return rows[0]


def get_task(task_id: str) -> Optional[dict[str, Any]]:
    rows = fetch_all(
        """
        SELECT task_id, task_type, status, priority, payload, result,
               locked_by, lease_expires_at, created_at, updated_at, completed_at, error_message
        FROM gulfnet.tasks WHERE task_id = %s::uuid
        """,
        (task_id,),
    )
    return rows[0] if rows else None


def list_tasks(limit: int = 50) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT task_id, task_type, status, priority, created_at, updated_at, completed_at
        FROM gulfnet.tasks
        ORDER BY created_at DESC
        LIMIT %s
        """,
        (limit,),
    )


def task_counts() -> dict[str, int]:
    rows = fetch_all(
        """
        SELECT status, COUNT(*)::int AS n
        FROM gulfnet.tasks
        GROUP BY status
        """
    )
    return {r["status"]: r["n"] for r in rows}


def recover_expired_leases() -> int:
    rows = fetch_all(
        """
        UPDATE gulfnet.tasks
        SET status = 'enqueued',
            locked_by = NULL,
            lease_expires_at = NULL,
            updated_at = NOW()
        WHERE status = 'processing'
          AND lease_expires_at IS NOT NULL
          AND lease_expires_at < NOW()
        RETURNING task_id
        """
    )
    return len(rows)


def dequeue_task(max_concurrent: int = 3, worker_id: str = WORKER_ID) -> Optional[dict[str, Any]]:
    recover_expired_leases()
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT COUNT(*) FROM gulfnet.tasks WHERE status = 'processing'
                """
            )
            in_flight = cur.fetchone()[0]
            if in_flight >= max_concurrent:
                return None

            lease_until = datetime.now(timezone.utc) + timedelta(seconds=LEASE_SECONDS)
            cur.execute(
                """
                WITH next_task AS (
                    SELECT task_id
                    FROM gulfnet.tasks
                    WHERE status = 'enqueued'
                    ORDER BY priority DESC, created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE gulfnet.tasks t
                SET status = 'processing',
                    locked_by = %s,
                    lease_expires_at = %s,
                    updated_at = NOW()
                FROM next_task
                WHERE t.task_id = next_task.task_id
                RETURNING t.task_id, t.task_type, t.payload, t.priority
                """,
                (worker_id, lease_until),
            )
            row = cur.fetchone()
            if not row:
                return None
            cols = [d.name for d in cur.description]
            task = dict(zip(cols, row))

            cur.execute(
                """
                INSERT INTO gulfnet.task_attempts (task_id, attempt_number, status)
                SELECT %s::uuid,
                       COALESCE((SELECT MAX(attempt_number) FROM gulfnet.task_attempts WHERE task_id = %s::uuid), 0) + 1,
                       'started'
                """,
                (str(task["task_id"]), str(task["task_id"])),
            )
            return task


def _json_dumps(obj: Any) -> str:
    def _default(o: Any) -> Any:
        if hasattr(o, "isoformat"):
            return o.isoformat()
        return str(o)

    return json.dumps(obj, default=_default)


def complete_task(task_id: str, result: dict[str, Any]) -> None:
    execute(
        """
        UPDATE gulfnet.tasks
        SET status = 'completed',
            result = %s::jsonb,
            completed_at = NOW(),
            updated_at = NOW(),
            lease_expires_at = NULL
        WHERE task_id = %s::uuid
        """,
        (_json_dumps(result), task_id),
    )
    execute(
        """
        UPDATE gulfnet.task_attempts
        SET status = 'completed', finished_at = NOW()
        WHERE attempt_id = (
            SELECT attempt_id FROM gulfnet.task_attempts
            WHERE task_id = %s::uuid ORDER BY attempt_number DESC LIMIT 1
        )
        """,
        (task_id,),
    )


def fail_task(task_id: str, error_message: str) -> None:
    execute(
        """
        UPDATE gulfnet.tasks
        SET status = 'failed',
            error_message = %s,
            updated_at = NOW(),
            lease_expires_at = NULL
        WHERE task_id = %s::uuid
        """,
        (error_message, task_id),
    )


def run_vip_outage_impact(payload: dict[str, Any]) -> dict[str, Any]:
    emirate = payload.get("emirate", "Dubai")
    cell_area = payload.get("cell_area", "Dubai Marina")
    events = fetch_all(
        """
        SELECT event_id, emirate, cell_area, severity, started_at, description
        FROM gulfnet.network_events
        WHERE emirate ILIKE %s AND cell_area ILIKE %s
          AND ended_at IS NULL
        ORDER BY started_at DESC
        """,
        (emirate, f"%{cell_area}%"),
    )
    vips = fetch_all(
        """
        SELECT account_id, msisdn, full_name, language_pref, channel_pref, plan_id
        FROM gulfnet.subscribers
        WHERE segment = 'VIP' AND emirate ILIKE %s AND status = 'active'
        """,
        (emirate,),
    )
    return {
        "report_type": "vip_outage_impact",
        "emirate": emirate,
        "cell_area": cell_area,
        "active_events": events,
        "impacted_vip_count": len(vips),
        "impacted_vips": vips,
        "recommended_actions": [
            "Notify VIP customers via preferred channel (WhatsApp/Arabic SMS when language_pref=ar)",
            "Open priority tickets for each VIP if severity is outage or degraded",
            "Offer temporary data booster if degradation lasts > 2 hours",
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def run_churn_offer_batch(payload: dict[str, Any]) -> dict[str, Any]:
    segment = payload.get("segment", "prepaid")
    min_risk = payload.get("min_risk", "high")
    rows = fetch_all(
        """
        SELECT account_id, msisdn, full_name, churn_risk, plan_id, language_pref, channel_pref
        FROM gulfnet.subscribers
        WHERE segment = %s AND churn_risk = %s AND status = 'active'
        """,
        (segment, min_risk),
    )
    offers = [
        {
            **r,
            "offer": "GulfMax 99 first month AED 49" if segment == "prepaid" else "+20GB booster AED 20",
        }
        for r in rows
    ]
    return {
        "report_type": "churn_offer_batch",
        "segment": segment,
        "min_risk": min_risk,
        "offer_count": len(offers),
        "offers": offers,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def process_one_task() -> Optional[dict[str, Any]]:
    task = dequeue_task()
    if not task:
        return None
    task_id = str(task["task_id"])
    payload = task["payload"]
    if isinstance(payload, str):
        payload = json.loads(payload)
    try:
        if task["task_type"] == "vip_outage_impact":
            result = run_vip_outage_impact(payload)
        elif task["task_type"] == "churn_offer_batch":
            result = run_churn_offer_batch(payload)
        else:
            raise ValueError(f"Unknown task_type: {task['task_type']}")
        complete_task(task_id, result)
        return {"task_id": task_id, "status": "completed", "result": result}
    except Exception as e:
        logger.exception("Task %s failed", task_id)
        fail_task(task_id, str(e))
        return {"task_id": task_id, "status": "failed", "error": str(e)}
