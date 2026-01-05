# ap/domain_models.py
from typing import List, Optional
from pydantic import BaseModel


class AnalyticDef(BaseModel):
    name: str
    type: str  # ex.: "integer", "boolean", "text/plain", "URL"


class AnalyticsAvailable(BaseModel):
    qualAnalytics: List[AnalyticDef]
    quantAnalytics: List[AnalyticDef]


class AnalyticValue(BaseModel):
    name: str
    type: str
    value: object   # pode ser int, bool, str, etc.


class StudentAnalytics(BaseModel):
    inveniraStdID: str
    quantAnalytics: List[AnalyticValue]
    qualAnalytics: List[AnalyticValue]


class AnalyticsRequestDTO(BaseModel):
    activityID: str
    query: Optional[str] = None   # "all", "events_count", etc.


class AnalyticsQuery(BaseModel):
    activity_id: str
    query: str                    # sempre preenchido (adapter faz o default)
