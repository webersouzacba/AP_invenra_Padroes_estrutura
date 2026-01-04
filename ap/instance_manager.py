from __future__ import annotations

from typing import Optional


class InstanceManager:
    """Singleton-like registry (supporting pattern from prior activity)."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._registry = {}  # type: ignore[attr-defined]
        return cls._instance

    def get_instance_id(self, activity_id: str) -> Optional[str]:
        return self._registry.get(activity_id)

    def set_instance_id(self, activity_id: str, instance_id: str) -> None:
        self._registry[activity_id] = instance_id
