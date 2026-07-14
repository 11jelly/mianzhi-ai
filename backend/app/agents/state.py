from typing import Literal, TypedDict

AgentAction = Literal["FOLLOW_UP", "NEXT_PRIMARY", "READY_FOR_REPORT"]


class AgentState(TypedDict, total=False):
    session_id: str
    question_id: str
    question_type: str
    parent_question_id: str | None
    target_role: str
    difficulty: str
    interview_type: str
    question_text: str
    answer_text: str
    evaluation: dict
    current_question_index: int
    question_count: int
    follow_up_count: int
    max_follow_ups_per_session: int
    max_follow_ups_per_primary: int
    follow_up_min_score: int
    follow_up_score_threshold: int
    resume_context: str
    can_follow_up: bool
    agent_action: AgentAction
    follow_up_question: str | None
    follow_up_category: str | None
    reason_summary: str | None
