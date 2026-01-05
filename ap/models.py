from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional


class AnalyticsQueryRequest(BaseModel):
    """Request body for aggregated analytics queries."""
    activityID: str = Field(..., min_length=1,
                            description="Activity instance identifier.")
    userID: Optional[str] = Field(
        default=None, description="Optional learner identifier.")
    query: Optional[str] = Field(
        default=None, description="Optional query name/identifier.")
    params: Dict[str, Any] = Field(
        default_factory=dict, description="Optional query parameters.")


class AnalyticsListResponse(BaseModel):
    available_queries: List[Dict[str, Any]]


class UserUrlResponse(BaseModel):
    activityID: str
    entry_url: str
    instance_id: str
