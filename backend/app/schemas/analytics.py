from datetime import datetime

from pydantic import BaseModel


class AnalyticsReportPoint(BaseModel):
    session_id: str
    target_role: str
    created_at: datetime
    overall_score: int
    logic_score: int
    technical_score: int
    expression_score: int
    project_depth_score: int


class AbilityAverages(BaseModel):
    logic_score: float
    technical_score: float
    expression_score: float
    project_depth_score: float


class WeakestDimension(BaseModel):
    key: str
    label: str
    average_score: float
    max_score: int


class AnalyticsImprovementPlanItem(BaseModel):
    priority: str
    topic: str


class AnalyticsOverview(BaseModel):
    completed_interview_count: int
    average_overall_score: float
    latest_report: AnalyticsReportPoint | None
    ability_averages: AbilityAverages | None
    weakest_dimension: WeakestDimension | None
    latest_improvement_plan: list[AnalyticsImprovementPlanItem]


class AnalyticsTrendItem(BaseModel):
    session_id: str
    target_role: str
    report_created_at: datetime
    overall_score: int
    logic_score: int
    technical_score: int
    expression_score: int
    project_depth_score: int


class AnalyticsTrendResponse(BaseModel):
    items: list[AnalyticsTrendItem]


class AnalyticsHistoryItem(AnalyticsTrendItem):
    difficulty: str
    interview_type: str
    knowledge_base_names: list[str]

