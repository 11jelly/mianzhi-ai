from fastapi.testclient import TestClient

from app.schemas.evaluation import EvaluationResult
from app.services.llm_client import (
    EVALUATION_FAILURE_MESSAGE,
    LLMGenerationError,
    LLMResponseFormatError,
    validate_answer_evaluation,
)
from tests.test_phase1_auth_interviews import auth_headers, login_user, register_user
from tests.test_phase2a_questions import FakeLLMClient, create_interview, override_llm

pytest_plugins = ["tests.test_phase1_auth_interviews"]


class FakeEvaluationLLMClient(FakeLLMClient):
    def __init__(self) -> None:
        super().__init__()
        self.evaluation_calls = 0

    async def evaluate_answer(self, interview, question, answer_text: str) -> EvaluationResult:
        self.evaluation_calls += 1
        return EvaluationResult(
            total_score=78,
            logic_score=20,
            technical_score=24,
            expression_score=16,
            project_depth_score=18,
            strengths=["结构清晰", "能够结合项目经验"],
            weaknesses=["指标不够量化"],
            improvement_suggestion="补充更多量化数据和异常处理细节。",
            detailed_feedback="回答整体完整，但技术细节和结果量化还可以加强。",
        )


class InvalidEvaluationLLMClient(FakeLLMClient):
    async def evaluate_answer(self, interview, question, answer_text: str) -> EvaluationResult:
        return validate_answer_evaluation('{"total_score": 90, "logic_score": 1}')


class ScriptedRawEvaluationLLMClient(FakeLLMClient):
    def __init__(self, contents: list[str]) -> None:
        super().__init__()
        self.contents = contents
        self.evaluation_calls = 0

    async def evaluate_answer(self, interview, question, answer_text: str) -> EvaluationResult:
        self.evaluation_calls += 1
        first_content = self.contents[0]
        try:
            return validate_answer_evaluation(first_content)
        except LLMResponseFormatError:
            if len(self.contents) < 2:
                raise LLMGenerationError(EVALUATION_FAILURE_MESSAGE, status_code=502) from None
        try:
            return validate_answer_evaluation(self.contents[1])
        except LLMResponseFormatError as exc:
            raise LLMGenerationError(EVALUATION_FAILURE_MESSAGE, status_code=502) from exc


def low_quality_markdown_json() -> str:
    return """```json
{
  "total_score": 8,
  "logic_score": 2,
  "technical_score": 1,
  "expression_score": 3,
  "project_depth_score": 2,
  "strengths": [],
  "weaknesses": ["回答重复且缺少有效技术内容"],
  "improvement_suggestion": "请先尝试说明一个相关概念、方案或项目经历，再补充技术细节。",
  "detailed_feedback": "当前回答主要是重复表达不会，无法体现对题目的理解和技术实践。"
}
```"""


def start_interview(client: TestClient, token: str, question_count: int = 3) -> tuple[str, dict]:
    session_id = create_interview(client, token, question_count=question_count)
    fake_llm = FakeEvaluationLLMClient()
    override_llm(client, fake_llm)
    response = client.post(f"/api/v1/interviews/{session_id}/start", headers=auth_headers(token))
    assert response.status_code == 200
    return session_id, response.json()["current_question"]


def valid_answer_text() -> str:
    return "我会先说明项目背景，再介绍我的职责、技术方案、关键难点和最终结果。"


def submit_answer(
    client: TestClient,
    token: str,
    session_id: str,
    question_id: str,
    answer_text: str | None = None,
):
    return client.post(
        f"/api/v1/interviews/{session_id}/answers",
        headers=auth_headers(token),
        json={
            "question_id": question_id,
            "answer_text": answer_text or valid_answer_text(),
        },
    )


def test_user_can_submit_current_question_answer(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id, question = start_interview(client, token)

    response = submit_answer(client, token, session_id, question["id"])

    assert response.status_code == 200
    data = response.json()
    assert data["answer"]["question_id"] == question["id"]
    assert data["evaluation"]["total_score"] == 78
    assert data["answered_question_count"] == 1
    assert data["question_count"] == 3


def test_submit_success_saves_evaluation_advances_and_returns_next_question(
    client: TestClient,
) -> None:
    register_user(client)
    token = login_user(client)
    session_id, question = start_interview(client, token, question_count=3)

    response = submit_answer(client, token, session_id, question["id"])
    detail_response = client.get(f"/api/v1/interviews/{session_id}", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert data["session_status"] == "IN_PROGRESS"
    assert data["next_question"]["sequence"] == 2
    assert detail_response.json()["current_question_index"] == 1


def test_current_question_advances_after_each_answer(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id, first_question = start_interview(client, token, question_count=3)

    first_response = submit_answer(client, token, session_id, first_question["id"])
    second_current_response = client.get(
        f"/api/v1/interviews/{session_id}/current-question",
        headers=auth_headers(token),
    )
    second_question = second_current_response.json()
    second_response = submit_answer(client, token, session_id, second_question["id"])
    third_current_response = client.get(
        f"/api/v1/interviews/{session_id}/current-question",
        headers=auth_headers(token),
    )

    assert first_response.status_code == 200
    assert second_current_response.status_code == 200
    assert second_question["sequence"] == 2
    assert second_response.status_code == 200
    assert third_current_response.status_code == 200
    assert third_current_response.json()["sequence"] == 3


def test_current_question_is_unavailable_after_last_answer(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id, first_question = start_interview(client, token, question_count=3)

    first = submit_answer(client, token, session_id, first_question["id"]).json()
    second = submit_answer(client, token, session_id, first["next_question"]["id"]).json()
    third_response = submit_answer(client, token, session_id, second["next_question"]["id"])
    current_response = client.get(
        f"/api/v1/interviews/{session_id}/current-question",
        headers=auth_headers(token),
    )

    assert third_response.status_code == 200
    assert third_response.json()["session_status"] == "READY_FOR_REPORT"
    assert current_response.status_code == 409
    assert current_response.json()["detail"] == "Interview questions have been completed."


def test_answered_question_cannot_be_submitted_as_current_again(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id, first_question = start_interview(client, token, question_count=3)

    first_response = submit_answer(client, token, session_id, first_question["id"])
    repeat_response = submit_answer(client, token, session_id, first_question["id"])

    assert first_response.status_code == 200
    assert repeat_response.status_code == 409
    assert repeat_response.json()["detail"] == "This is not the current question."


def test_user_cannot_submit_answer_to_other_users_session(client: TestClient) -> None:
    register_user(client, "first_user", "first_2b@example.com")
    first_token = login_user(client, "first_user")
    register_user(client, "second_user", "second_2b@example.com")
    second_token = login_user(client, "second_user")
    session_id, question = start_interview(client, first_token)

    response = submit_answer(client, second_token, session_id, question["id"])

    assert response.status_code == 404


def test_question_must_belong_to_session(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    first_session_id, _first_question = start_interview(client, token)
    second_session_id, second_question = start_interview(client, token)

    response = submit_answer(client, token, first_session_id, second_question["id"])

    assert response.status_code == 404
    assert second_session_id


def test_cannot_answer_non_current_question(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id, first_question = start_interview(client, token, question_count=3)
    questions_response = client.get(
        f"/api/v1/interviews/{session_id}/questions",
        headers=auth_headers(token),
    )
    second_question = questions_response.json()[1]

    response = submit_answer(client, token, session_id, second_question["id"])
    first_response = submit_answer(client, token, session_id, first_question["id"])

    assert response.status_code == 409
    assert first_response.status_code == 200


def test_duplicate_answer_returns_409(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id, question = start_interview(client, token)

    first_response = submit_answer(client, token, session_id, question["id"])
    second_response = submit_answer(client, token, session_id, question["id"])

    assert first_response.status_code == 200
    assert second_response.status_code == 409


def test_short_answer_returns_422(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id, question = start_interview(client, token)

    response = submit_answer(client, token, session_id, question["id"], answer_text="太短")

    assert response.status_code == 422


def test_repeated_low_quality_answer_with_markdown_json_is_saved(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=3)
    fake_llm = ScriptedRawEvaluationLLMClient([low_quality_markdown_json()])
    override_llm(client, fake_llm)
    start_response = client.post(
        f"/api/v1/interviews/{session_id}/start",
        headers=auth_headers(token),
    )
    question = start_response.json()["current_question"]

    response = submit_answer(
        client,
        token,
        session_id,
        question["id"],
        answer_text="我不会我不会我不会我不会我不会我不会我不会我不会我不会我不会",
    )

    assert response.status_code == 200
    data = response.json()
    assert data["evaluation"]["total_score"] == 8
    assert data["evaluation"]["strengths"] == []
    assert data["evaluation"]["weaknesses"] == ["回答重复且缺少有效技术内容"]
    assert data["next_question"]["sequence"] == 2


def test_invalid_first_evaluation_retries_and_saves_low_score(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=3)
    fake_llm = ScriptedRawEvaluationLLMClient(
        [
            "这段回答质量较低，我无法按你的要求评分。",
            low_quality_markdown_json(),
        ]
    )
    override_llm(client, fake_llm)
    start_response = client.post(
        f"/api/v1/interviews/{session_id}/start",
        headers=auth_headers(token),
    )
    question = start_response.json()["current_question"]

    response = submit_answer(
        client,
        token,
        session_id,
        question["id"],
        answer_text="我不会我不会我不会我不会我不会我不会我不会我不会我不会我不会",
    )
    detail_response = client.get(f"/api/v1/interviews/{session_id}", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json()["evaluation"]["total_score"] == 8
    assert detail_response.json()["current_question_index"] == 1


def test_evaluation_total_score_is_normalized_from_dimensions(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=3)
    fake_llm = ScriptedRawEvaluationLLMClient(
        [
            """
            {
              "total_score": 100,
              "logic_score": 4,
              "technical_score": 3,
              "expression_score": 2,
              "project_depth_score": 1,
              "strengths": "仍然尝试作答",
              "weaknesses": "缺少有效技术内容",
              "improvement_suggestion": "补充具体技术方案和项目细节。",
              "detailed_feedback": "回答内容不足，当前只能给出较低评分。"
            }
            """
        ]
    )
    override_llm(client, fake_llm)
    start_response = client.post(
        f"/api/v1/interviews/{session_id}/start",
        headers=auth_headers(token),
    )
    question = start_response.json()["current_question"]

    response = submit_answer(client, token, session_id, question["id"])

    assert response.status_code == 200
    data = response.json()
    assert data["evaluation"]["total_score"] == 10
    assert data["evaluation"]["strengths"] == ["仍然尝试作答"]
    assert data["evaluation"]["weaknesses"] == ["缺少有效技术内容"]


def test_invalid_evaluation_does_not_write_or_advance(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=3)
    invalid_llm = InvalidEvaluationLLMClient()
    override_llm(client, invalid_llm)
    start_response = client.post(
        f"/api/v1/interviews/{session_id}/start",
        headers=auth_headers(token),
    )
    question = start_response.json()["current_question"]

    response = submit_answer(client, token, session_id, question["id"])
    detail_response = client.get(f"/api/v1/interviews/{session_id}", headers=auth_headers(token))
    answers_response = client.get(
        f"/api/v1/interviews/{session_id}/answers",
        headers=auth_headers(token),
    )

    assert response.status_code == 502
    assert detail_response.json()["current_question_index"] == 0
    assert detail_response.json()["status"] == "IN_PROGRESS"
    assert answers_response.json() == []


def test_evaluation_failure_after_retry_does_not_write_or_advance(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=3)
    fake_llm = ScriptedRawEvaluationLLMClient(
        ["第一次不是 JSON", '{"total_score": 10, "logic_score": 1}']
    )
    override_llm(client, fake_llm)
    start_response = client.post(
        f"/api/v1/interviews/{session_id}/start",
        headers=auth_headers(token),
    )
    question = start_response.json()["current_question"]

    response = submit_answer(client, token, session_id, question["id"])
    detail_response = client.get(f"/api/v1/interviews/{session_id}", headers=auth_headers(token))
    answers_response = client.get(
        f"/api/v1/interviews/{session_id}/answers",
        headers=auth_headers(token),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == EVALUATION_FAILURE_MESSAGE
    assert detail_response.json()["current_question_index"] == 0
    assert detail_response.json()["status"] == "IN_PROGRESS"
    assert answers_response.json() == []


def test_last_answer_sets_ready_for_report(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id, question = start_interview(client, token, question_count=3)

    first = submit_answer(client, token, session_id, question["id"]).json()
    second = submit_answer(client, token, session_id, first["next_question"]["id"]).json()
    third_response = submit_answer(client, token, session_id, second["next_question"]["id"])

    assert third_response.status_code == 200
    data = third_response.json()
    assert data["session_status"] == "READY_FOR_REPORT"
    assert data["next_question"] is None


def test_get_answers_returns_completed_records(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id, question = start_interview(client, token)
    submit_answer(client, token, session_id, question["id"])

    response = client.get(f"/api/v1/interviews/{session_id}/answers", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["question_id"] == question["id"]
    assert data[0]["evaluation"]["total_score"] == 78
    assert "expected_points" not in data[0]
