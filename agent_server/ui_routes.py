"""Browser-facing routes: architecture page, chat console, memory inspector."""

from __future__ import annotations

import logging
import os
from functools import lru_cache

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from agent_server.ui_chat import CHAT_HTML
from agent_server.ui_landing import LANDING_HTML
from agent_server.utils_memory import (
    LakebaseConfig,
    acquire_lakebase_resources,
    init_lakebase_config,
    memory_namespace,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ui"])


@lru_cache(maxsize=1)
def _config() -> LakebaseConfig:
    return init_lakebase_config()


@router.get("/", response_class=HTMLResponse, include_in_schema=False)
def home() -> HTMLResponse:
    return HTMLResponse(LANDING_HTML)


@router.get("/chat", response_class=HTMLResponse, include_in_schema=False)
def chat() -> HTMLResponse:
    return HTMLResponse(CHAT_HTML)


@router.get("/ui/memory", include_in_schema=False)
async def ui_memory(user_id: str) -> dict:
    """What the agent currently remembers about a user, for the chat flow rail."""
    limit = int(os.getenv("MEMORY_RECALL_LIMIT", "10"))
    try:
        async with acquire_lakebase_resources(_config()) as (_checkpointer, store):
            items = await store.asearch(memory_namespace(user_id), limit=limit)
    except Exception as e:
        logger.exception("Memory inspection failed for user %s", user_id)
        return {"count": 0, "items": [], "error": f"Memory unavailable: {e}"}

    return {
        "count": len(items),
        "items": [{"key": item.key, "value": item.value} for item in items],
    }
