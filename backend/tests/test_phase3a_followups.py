from fastapi.testclient import TestClient

from app.schemas.evaluation import EvaluationResult
from app.schemas.llm import FollowUpDecision
from app.schemas.report import ReportGenerationResult
from tests.test_phase1_auth_interviews import auth_headers, login_user, register_user
from tests.test_phase2a_questions import create_interview, override_llm
from tests.test_phase2b_answers import FakeEvaluationLLMClient, submit_answer

pytest_plugins = ["tests.test_phase1_auth_interviews"]


class AdaptiveFollowUpLLMClient(FakeEvaluationLLMClient):
    def __init__(
        self,
        *,
        primary_score: int = 50,
        follow_up_score: int = 70,
        decisions: list[bool] | None = None,
    ) -> None:
        super().__init__()
        self.primary_score = primary_score
        self.follow_up_score = follow_up_score
        self.decisions = decisions or [True]
        self.decision_calls = 0

    async def evaluate_answer(self, interview, question, answer_text: str) -> EvaluationResult:
        self.evaluation_calls += 1
        score = (
            self.follow_up_score
            if question.question_type == "FOLLOW_UP"
            else self.primary_score
        )
        logic_score = min(score, 25)
        remaining_score = score - logic_score
        technical_score = min(remaining_score, 30)
        remaining_score -= technical_score
        expression_score = min(remaining_score, 20)
        project_depth_score = remaining_score - expression_score
        return EvaluationResult(
            total_score=score,
            logic_score=logic_score,
            technical_score=technical_score,
            expression_score=expression_score,
            project_depth_score=project_depth_score,
            strengths=["回答包含部分技术线索"] if score > 0 else [],
            weaknesses=["回答需要追问澄清"] if score > 0 else ["缺少有效技术内容"],
            improvement_suggestion="补充具体方案、边界条件和项目细节。",
            detailed_feedback="测试用评分结果。",
        )

    async def decide_follow_up(self, state: dict) -> FollowUpDecision:
        self.decision_calls += 1
        should_follow_up = self.decisions.pop(0) if self.decisions else True
        return FollowUpDecision(
            should_follow_up=should_follow_up,
            follow_up_category="技术追问",
            follow_up_question="请继续说明这个方案里的关键权衡和异常处理。",
            reason_summary="回答有部分技术内容，但关键细节不足。",
        )


class ZeroScoreLLMClient(AdaptiveFollowUpLLMClient):
    def __init__(self) -> None:
        super().__init__(primary_score=0, decisions=[True])


class ReportWithFollowUpLLMClient(AdaptiveFollowUpLLMClient):
    def __init__(self) -> None:
        super().__init__(primary_score=50, follow_up_score=90, decisions=[True, False, False])
        self.report_calls = 0

    async def generate_interview_report(
        self,
        interview,
        aggregate_scores: dict[str, int],
        records: list[dict],
    ) -> ReportGenerationResult:
        self.report_calls += 1
        assert aggregate_scores["overall_score"] == 50
        assert aggregate_scores["logic_score"] == 25
        assert len(records) == 4
        assert [record["question_type"] for record in records].count("FOLLOW_UP") == 1
        return ReportGenerationResult(
            summary="主问题计分稳定，追问作为补充上下文。",
            strengths=["能回答部分主问题"],
            weaknesses=["追问中暴露细节不足"],
            role_gap_analysis="仍需加强关键技术细节表达。",
            improvement_plan=[
                {
                    "priority": 1,
                    "topic": "方案细节",
                    "reason": "主问题得分偏低。",
                    "actions": ["补充异常处理", "补充技术权衡"],
                    "expected_outcome": "回答更完整。",
                }
            ],
            next_practice_questions=["请说明一个接口限流方案。"],
        )


def start_with_fake_llm(client: TestClient, token: str, fake_llm, question_count: int = 3):
    session_id = create_interview(client, token, question_count=question_count)
    override_llm(client, fake_llm)
    response = client.post(f"/api/v1/interviews/{session_id}/start", headers=auth_headers(token))
    assert response.status_code == 200
    return session_id, response.json()["current_question"]


def test_primary_answer_can_create_follow_up_and_current_question_returns_it(
    client: TestClient,
) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = AdaptiveFollowUpLLMClient(decisions=[True])
    session_id, first_question = start_with_fake_llm(client, token, fake_llm)

    response = submit_answer(client, token, session_id, first_question["id"])
    current_response = client.get(
        f"/api/v1/interviews/{session_id}/current-question",
        headers=auth_headers(token),
    )
    events_response = client.get(
        f"/api/v1/interviews/{session_id}/agent-events",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["agent_action"] == "FOLLOW_UP"
    assert data["next_question"]["question_type"] == "FOLLOW_UP"
    assert data["next_question"]["parent_question_id"] == first_question["id"]
    assert current_response.json()["id"] == data["next_question"]["id"]
    assert events_response.status_code == 200
    assert events_response.json()[0]["decision"] == "FOLLOW_UP"


def test_follow_up_answer_advances_to_next_primary_without_follow_up_loop(
    client: TestClient,
) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = AdaptiveFollowUpLLMClient(decisions=[True, True])
    session_id, first_question = start_with_fake_llm(client, token, fake_llm)

    first_response = submit_answer(client, token, session_id, first_question["id"]).json()
    follow_up = first_response["next_question"]
    follow_up_response = submit_answer(client, token, session_id, follow_up["id"])

    assert follow_up_response.status_code == 200
    data = follow_up_response.json()
    assert data["agent_action"] == "NEXT_PRIMARY"
    assert data["next_question"]["question_type"] == "PRIMARY"
    assert data["next_question"]["sequence"] == 2
    assert fake_llm.decision_calls == 1


def test_session_follow_up_cap_falls_back_to_primary_flow(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = AdaptiveFollowUpLLMClient(decisions=[True, True, True])
    session_id, first_question = start_with_fake_llm(client, token, fake_llm, question_count=3)

    first = submit_answer(client, token, session_id, first_question["id"]).json()
    second_primary = submit_answer(client, token, session_id, first["next_question"]["id"]).json()[
        "next_question"
    ]
    second = submit_answer(client, token, session_id, second_primary["id"]).json()
    third_primary = submit_answer(client, token, session_id, second["next_question"]["id"]).json()[
        "next_question"
    ]
    third_response = submit_answer(client, token, session_id, third_primary["id"])

    assert third_response.status_code == 200
    assert third_response.json()["agent_action"] == "READY_FOR_REPORT"
    assert third_response.json()["next_question"] is None
    assert fake_llm.decision_calls == 2


def test_zero_score_does_not_trigger_follow_up(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = ZeroScoreLLMClient()
    session_id, first_question = start_with_fake_llm(client, token, fake_llm)

    response = submit_answer(
        client,
        token,
        session_id,
        first_question["id"],
        answer_text="我不会我不会我不会我不会我不会我不会我不会我不会我不会我不会",
    )

    assert response.status_code == 200
    assert response.json()["agent_action"] == "NEXT_PRIMARY"
    assert response.json()["next_question"]["question_type"] == "PRIMARY"
    assert fake_llm.decision_calls == 0


def test_report_uses_primary_scores_and_keeps_follow_up_records_for_prompt(
    client: TestClient,
) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = ReportWithFollowUpLLMClient()
    session_id, first_question = start_with_fake_llm(client, token, fake_llm, question_count=3)

    first = submit_answer(client, token, session_id, first_question["id"]).json()
    second_primary = submit_answer(client, token, session_id, first["next_question"]["id"]).json()[
        "next_question"
    ]
    third_primary = submit_answer(client, token, session_id, second_primary["id"]).json()[
        "next_question"
    ]
    submit_answer(client, token, session_id, third_primary["id"])

    response = client.post(f"/api/v1/interviews/{session_id}/report", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["overall_score"] == 50
    assert fake_llm.report_calls == 1


def test_user_cannot_read_other_users_agent_events(client: TestClient) -> None:
    register_user(client, "first_user", "first_phase3a@example.com")
    first_token = login_user(client, "first_user")
    register_user(client, "second_user", "second_phase3a@example.com")
    second_token = login_user(client, "second_user")
    fake_llm = AdaptiveFollowUpLLMClient(decisions=[True])
    session_id, first_question = start_with_fake_llm(client, first_token, fake_llm)
    submit_answer(client, first_token, session_id, first_question["id"])

    response = client.get(
        f"/api/v1/interviews/{session_id}/agent-events",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 404
