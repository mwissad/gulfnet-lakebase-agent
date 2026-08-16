"""GulfNet Care Copilot tools — OLTP, search, orchestration."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any, Optional

from langchain_core.tools import tool

from agent_server.db import execute, fetch_all

logger = logging.getLogger(__name__)


def _json_default(obj: Any) -> Any:
    if isinstance(obj, (date,)):
        return obj.isoformat()
    return str(obj)


def _dumps(rows: Any) -> str:
    return json.dumps(rows, default=_json_default, indent=2)


@tool
def lookup_subscriber(msisdn_or_account: str) -> str:
    """Look up a GulfNet subscriber by MSISDN (+971...) or account_id (ACC-...).

    Returns profile, plan, ARPU, segment, language/channel preferences.
    """
    key = msisdn_or_account.strip()
    rows = fetch_all(
        """
        SELECT s.account_id, s.msisdn, s.full_name, s.segment, s.emirate,
               s.language_pref, s.channel_pref, s.arpu_aed, s.churn_risk, s.status,
               p.plan_id, p.name_en, p.name_ar, p.monthly_fee_aed, p.data_gb,
               p.roaming_gcc, p.roaming_intl, p.description_en
        FROM gulfnet.subscribers s
        LEFT JOIN gulfnet.plans p ON p.plan_id = s.plan_id
        WHERE s.msisdn = %s OR s.account_id = %s
        LIMIT 1
        """,
        (key, key),
    )
    if not rows:
        return f"No subscriber found for '{key}'."
    return _dumps(rows[0])


@tool
def get_usage_summary(account_id: str, days: int = 7) -> str:
    """Get recent data/voice/roaming usage for an account over the last N days (default 7)."""
    rows = fetch_all(
        """
        SELECT usage_date, data_gb, voice_minutes, roaming_data_gb, roaming_country
        FROM gulfnet.usage_daily
        WHERE account_id = %s AND usage_date >= CURRENT_DATE - %s::int
        ORDER BY usage_date DESC
        """,
        (account_id, days),
    )
    if not rows:
        return f"No usage rows for {account_id} in the last {days} days."
    totals = {
        "data_gb": sum(float(r["data_gb"] or 0) for r in rows),
        "voice_minutes": sum(int(r["voice_minutes"] or 0) for r in rows),
        "roaming_data_gb": sum(float(r["roaming_data_gb"] or 0) for r in rows),
        "days": days,
        "rows": rows,
    }
    return _dumps(totals)


@tool
def search_knowledge(query: str, category: Optional[str] = None, limit: int = 5) -> str:
    """Hybrid knowledge search over GulfNet tariffs, roaming, SLA, and coverage docs.

    Uses Postgres full-text (BM25-style ranking via ts_rank) and optional category filter.
    When Lakebase Search (lakebase_vector / lakebase_text) is enabled, swap the SQL
    in agent_server/search.py for native hybrid RRF.
    """
    from agent_server.search import hybrid_search

    results = hybrid_search(query=query, category=category, limit=limit)
    if not results:
        return "No knowledge base hits."
    return _dumps(results)


@tool
def check_network_status(emirate: Optional[str] = None, cell_area: Optional[str] = None) -> str:
    """Check synthetic live network events (outage/degraded/info) by emirate and/or cell area."""
    clauses = ["(ended_at IS NULL OR ended_at > NOW() - INTERVAL '1 day')"]
    args: list[Any] = []
    if emirate:
        clauses.append("emirate ILIKE %s")
        args.append(emirate)
    if cell_area:
        clauses.append("cell_area ILIKE %s")
        args.append(f"%{cell_area}%")
    sql = f"""
        SELECT event_id, emirate, cell_area, severity, started_at, ended_at,
               description, affected_tech
        FROM gulfnet.network_events
        WHERE {' AND '.join(clauses)}
        ORDER BY started_at DESC
        LIMIT 20
    """
    rows = fetch_all(sql, tuple(args))
    if not rows:
        return "No matching network events."
    return _dumps(rows)


@tool
def recommend_plan(account_id: str, intent: str) -> str:
    """Recommend a plan change based on subscriber profile, usage, and stated intent
    (e.g. 'roaming to Riyadh', 'more data', 'cheaper').
    """
    profile = fetch_all(
        """
        SELECT s.*, p.name_en AS current_plan, p.monthly_fee_aed AS current_fee,
               p.roaming_gcc, p.roaming_intl, p.data_gb AS current_data_gb
        FROM gulfnet.subscribers s
        JOIN gulfnet.plans p ON p.plan_id = s.plan_id
        WHERE s.account_id = %s
        """,
        (account_id,),
    )
    if not profile:
        return f"Unknown account {account_id}"
    plans = fetch_all(
        """
        SELECT plan_id, name_en, type, monthly_fee_aed, data_gb, roaming_gcc, roaming_intl, description_en
        FROM gulfnet.plans
        ORDER BY monthly_fee_aed
        """
    )
    intent_l = intent.lower()
    scored: list[dict[str, Any]] = []
    for plan in plans:
        score = 0
        reasons: list[str] = []
        if "roam" in intent_l or "riyadh" in intent_l or "ksa" in intent_l or "saudi" in intent_l:
            if plan["roaming_gcc"]:
                score += 5
                reasons.append("includes GCC roaming")
            if plan["roaming_intl"]:
                score += 2
                reasons.append("includes international roaming")
        if "data" in intent_l or "gb" in intent_l:
            if (plan["data_gb"] or 0) > (profile[0]["current_data_gb"] or 0):
                score += 3
                reasons.append("more data than current plan")
        if "cheap" in intent_l or "save" in intent_l:
            if (plan["monthly_fee_aed"] or 0) < (profile[0]["current_fee"] or 0):
                score += 4
                reasons.append("lower monthly fee")
        if plan["plan_id"] == profile[0]["plan_id"]:
            score -= 10
            reasons.append("already on this plan")
        scored.append({**plan, "score": score, "reasons": reasons})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return _dumps(
        {
            "account": {
                "account_id": profile[0]["account_id"],
                "current_plan": profile[0]["current_plan"],
                "segment": profile[0]["segment"],
                "churn_risk": profile[0]["churn_risk"],
            },
            "intent": intent,
            "recommendations": scored[:3],
        }
    )


@tool
def create_support_ticket(
    account_id: str,
    category: str,
    summary: str,
    priority: str = "medium",
) -> str:
    """Create a support ticket for a subscriber. Categories: roaming, network, billing, plan, other."""
    import uuid

    ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
    execute(
        """
        INSERT INTO gulfnet.tickets (ticket_id, account_id, category, priority, status, summary)
        VALUES (%s, %s, %s, %s, 'open', %s)
        """,
        (ticket_id, account_id, category, priority, summary),
    )
    return _dumps({"ticket_id": ticket_id, "status": "open", "account_id": account_id})


@tool
def enqueue_ops_task(task_type: str, payload_json: str, priority: int = 80) -> str:
    """Enqueue a long-running ops task on the Lakebase Postgres queue.

    Supported task_type values:
    - vip_outage_impact: payload {"emirate":"Dubai","cell_area":"Dubai Marina"}
    - churn_offer_batch: payload {"segment":"prepaid","min_risk":"high"}
    """
    from agent_server.orchestration import enqueue_task

    try:
        payload = json.loads(payload_json) if payload_json else {}
    except json.JSONDecodeError as e:
        return f"Invalid payload JSON: {e}"
    task = enqueue_task(task_type=task_type, payload=payload, priority=priority)
    return _dumps(task)


@tool
def get_task_status(task_id: str) -> str:
    """Get status and result of an orchestrated ops task by task_id (UUID)."""
    from agent_server.orchestration import get_task

    task = get_task(task_id)
    if not task:
        return f"Task {task_id} not found."
    return _dumps(task)


def gulfnet_tools():
    return [
        lookup_subscriber,
        get_usage_summary,
        search_knowledge,
        check_network_status,
        recommend_plan,
        create_support_ticket,
        enqueue_ops_task,
        get_task_status,
    ]
