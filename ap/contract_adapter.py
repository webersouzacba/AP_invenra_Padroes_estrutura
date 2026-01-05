from __future__ import annotations

from typing import Any, Dict, Optional

from .models import AnalyticsQueryRequest


class ContractAdapter:
    """Adapter (Structural Pattern) for the Inven!RA contract."""

    @staticmethod
    def adapt_activity_id(activity_id: str) -> str:
        activity_id = (activity_id or "").strip()
        if not activity_id:
            raise ValueError("activityID is required")
        return activity_id

    @staticmethod
    def adapt_user_id(user_id: Optional[str]) -> Optional[str]:
        if user_id is None:
            return None
        user_id = user_id.strip()
        return user_id or None

    @staticmethod
    def adapt_analytics_request(req: AnalyticsQueryRequest) -> Dict[str, Any]:
        """
        Normaliza o payload de /analytics, garantindo:
        - activityID obrigatório e sem espaços
        - userID opcional, mas normalizado
        - query com valor 'default' quando vazio
        - params sempre dicionário (fallback para {})
        """
        return {
            "activityID": ContractAdapter.adapt_activity_id(req.activityID),
            "userID": ContractAdapter.adapt_user_id(req.userID),
            "query": (req.query or "default").strip() or "default",
            "params": req.params or {},
        }
