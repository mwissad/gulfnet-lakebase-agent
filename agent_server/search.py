"""Simplify FTS hybrid search (category optional)."""

from __future__ import annotations

import os
from typing import Any, Optional

from agent_server.db import fetch_all


def hybrid_search(
    query: str,
    category: Optional[str] = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    if os.getenv("USE_LAKEBASE_SEARCH", "").lower() in {"1", "true", "yes"}:
        try:
            return hybrid_search_lakebase(query, category=category, limit=limit)
        except Exception:
            pass
    return hybrid_search_fts(query, category=category, limit=limit)


def hybrid_search_fts(
    query: str,
    category: Optional[str] = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    like = f"%{query}%"
    if category:
        return fetch_all(
            """
            SELECT c.chunk_id, d.doc_id, d.title, d.category, d.language,
                   c.content, c.metadata,
                   ts_rank(c.content_tsv, plainto_tsquery('english', %s)) AS rank
            FROM gulfnet.kb_chunks c
            JOIN gulfnet.kb_documents d ON d.doc_id = c.doc_id
            WHERE d.category = %s
              AND (
                c.content_tsv @@ plainto_tsquery('english', %s)
                OR c.content ILIKE %s
              )
            ORDER BY rank DESC NULLS LAST, c.chunk_id
            LIMIT %s
            """,
            (query, category, query, like, limit),
        )
    return fetch_all(
        """
        SELECT c.chunk_id, d.doc_id, d.title, d.category, d.language,
               c.content, c.metadata,
               ts_rank(c.content_tsv, plainto_tsquery('english', %s)) AS rank
        FROM gulfnet.kb_chunks c
        JOIN gulfnet.kb_documents d ON d.doc_id = c.doc_id
        WHERE c.content_tsv @@ plainto_tsquery('english', %s)
           OR c.content ILIKE %s
        ORDER BY rank DESC NULLS LAST, c.chunk_id
        LIMIT %s
        """,
        (query, query, like, limit),
    )


def hybrid_search_lakebase(
    query: str,
    category: Optional[str] = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Swap in lakebase_vector + lakebase_text RRF when extensions are enabled."""
    return hybrid_search_fts(query, category=category, limit=limit)
