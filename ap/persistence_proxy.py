from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .store_json import JsonFileDatabase


class PersistenceProxy:
    """Proxy (Structural Pattern) para acessso a persistencia."""

    def __init__(self, db: JsonFileDatabase) -> None:
        self._db = db
        self._cache: Optional[Dict[str, Any]] = None
        self._cache_ts: float = 0.0

    def _ensure_cache(self) -> Dict[str, Any]:
        if self._cache is None or (time.time() - self._cache_ts) > 1.0:
            self._cache = self._db.read_all()
            self._cache_ts = time.time()
        return self._cache

    def _flush(self) -> None:
        if self._cache is not None:
            self._db.write_all(self._cache)
            self._cache_ts = time.time()

    def get_instance(self, instance_id: str) -> Optional[Dict[str, Any]]:
        data = self._ensure_cache()
        return data.get("instances", {}).get(instance_id)

    def upsert_instance(self, instance_id: str, payload: Dict[str, Any]) -> None:
        data = self._ensure_cache()
        instances = data.setdefault("instances", {})
        instances[instance_id] = payload
        self._flush()

    def append_event(self, event: Dict[str, Any]) -> None:
        data = self._ensure_cache()
        events = data.setdefault("events", [])
        events.append(event)
        self._flush()

    def list_events(self, activity_id: Optional[str] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        data = self._ensure_cache()
        events: List[Dict[str, Any]] = data.get("events", [])
        out: List[Dict[str, Any]] = []
        for e in events:
            if activity_id and e.get("activityID") != activity_id:
                continue
            if user_id and e.get("userID") != user_id:
                continue
            out.append(e)
        return out
