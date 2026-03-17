"""
Agent Memory - Short-term (in-process) + Long-term (DB-persisted)
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Optional
import json


# ── Short-term memory (per pipeline run, lives in RAM) ───────────────────────

class ShortTermMemory:
    """Stores context for the current pipeline run only."""

    def __init__(self):
        self._store: dict[str, Any] = {}

    def set(self, key: str, value: Any) -> None:
        self._store[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._store.get(key, default)

    def update(self, data: dict[str, Any]) -> None:
        self._store.update(data)

    def all(self) -> dict[str, Any]:
        return dict(self._store)

    def clear(self) -> None:
        self._store.clear()


# ── Long-term memory (DB-persisted across runs) ───────────────────────────────

class LongTermMemory:
    """
    Persists agent observations to the AgentMemory DB table.
    Agents can query past runs to avoid known bad patterns.
    """

    def __init__(self, db_session_factory):
        self._factory = db_session_factory

    def remember(self, agent_name: str, key: str, value: Any, run_id: Optional[str] = None) -> None:
        from src.database.models import AgentMemory
        db = self._factory()
        try:
            record = AgentMemory(
                agent_name=agent_name,
                key=key,
                value=json.dumps(value),
                run_id=run_id,
                created_at=datetime.utcnow()
            )
            db.add(record)
            db.commit()
        finally:
            db.close()

    def recall(self, agent_name: str, key: str, limit: int = 10) -> list[Any]:
        from src.database.models import AgentMemory
        db = self._factory()
        try:
            rows = (
                db.query(AgentMemory)
                .filter(AgentMemory.agent_name == agent_name, AgentMemory.key == key)
                .order_by(AgentMemory.created_at.desc())
                .limit(limit)
                .all()
            )
            return [json.loads(r.value) for r in rows]
        finally:
            db.close()

    def recall_conflicts(self, limit: int = 20) -> list[dict]:
        """Retrieve historically problematic room/slot combos."""
        return self.recall("ConflictResolutionAgent", "conflict_pattern", limit)
