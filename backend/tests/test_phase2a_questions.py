from fastapi.testclient import TestClient

from app.api.v1.interviews import get_llm_client
from app.schemas.llm import GeneratedQuestionSet
from app.services.llm_client import validate_generated_questions
from tests.test_phase1_auth_interviews import (
    auth_headers,
    login_user,
    register_user,
)

pytest_plugins = ["tests.test_phase1_auth_interviews"]


class FakeLLMClient:
    def __init__(self) -> None:
        self.calls = 0

    async def generate_interview_questions(self, interview) -> GeneratedQuestionSet:
        self.calls += 1
        return GeneratedQuestionSet(
            questions=[
                {
                    "sequence": sequence,
                    "category": "技术基础",
                    "question_text": f"请回答第 {sequence} 个关于 {interview.target_role} 的问题。",
                    "expected_points": ["理解问题", "结合经验", "表达清晰"],
                }
                for sequence in range(1, interview.question_count + 1)
            ]
        )


class InvalidJSONLLMClient:
    async def generate_interview_questions(self, interview) -> GeneratedQuestionSet:
        return validate_generated_questions("not-json", interview.question_count)


def create_interview(client: TestClient, token: str, question_count: int = 3) -> str:
    response = client.post(
        "/api/v1/interviews",
        headers=auth_headers(token),
        json={
            "target_role": "Python backend developer",
            "difficulty": "intermediate",
            "interview_type": "technical",
            "question_count": question_count,
        },
    )
    assert response.status_code == 201
    return str(response.json()["id"])


def override_llm(client: TestClient, fake_client) -> None:
    client.app.dependency_overrides[get_llm_client] = lambda: fake_client


def test_user_can_start_own_created_interview(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=3)
    fake_llm = FakeLLMClient()
    override_llm(client, fake_llm)

    response = client.post(f"/api/v1/interviews/{session_id}/start", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "IN_PROGRESS"
    assert data["question_count"] == 3
    assert data["current_question_index"] == 0
    assert data["current_question"]["sequence"] == 1
    assert fake_llm.calls == 1


def test_start_success_creates_questions_and_current_question(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=5)
    override_llm(client, FakeLLMClient())

    client.post(f"/api/v1/interviews/{session_id}/start", headers=auth_headers(token))
    current_response = client.get(
        f"/api/v1/interviews/{session_id}/current-question",
        headers=auth_headers(token),
    )
    questions_response = client.get(
        f"/api/v1/interviews/{session_id}/questions",
        headers=auth_headers(token),
    )
    detail_response = client.get(
        f"/api/v1/interviews/{session_id}",
        headers=auth_headers(token),
    )

    assert current_response.status_code == 200
    assert current_response.json()["sequence"] == 1
    assert "expected_points" not in current_response.json()
    assert questions_response.status_code == 200
    assert len(questions_response.json()) == 5
    assert [item["sequence"] for item in questions_response.json()] == [1, 2, 3, 4, 5]
    assert detail_response.json()["status"] == "IN_PROGRESS"


def test_repeated_start_does_not_generate_duplicate_questions(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=3)
    fake_llm = FakeLLMClient()
    override_llm(client, fake_llm)

    first_response = client.post(
        f"/api/v1/interviews/{session_id}/start",
        headers=auth_headers(token),
    )
    second_response = client.post(
        f"/api/v1/interviews/{session_id}/start",
        headers=auth_headers(token),
    )
    questions_response = client.get(
        f"/api/v1/interviews/{session_id}/questions",
        headers=auth_headers(token),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert fake_llm.calls == 1
    assert len(questions_response.json()) == 3


def test_user_cannot_start_or_view_other_users_questions(client: TestClient) -> None:
    register_user(client, "first_user", "first_phase2a@example.com")
    first_token = login_user(client, "first_user")
    register_user(client, "second_user", "second_phase2a@example.com")
    second_token = login_user(client, "second_user")
    session_id = create_interview(client, first_token, question_count=3)
    override_llm(client, FakeLLMClient())

    start_response = client.post(
        f"/api/v1/interviews/{session_id}/start",
        headers=auth_headers(second_token),
    )
    current_response = client.get(
        f"/api/v1/interviews/{session_id}/current-question",
        headers=auth_headers(second_token),
    )
    questions_response = client.get(
        f"/api/v1/interviews/{session_id}/questions",
        headers=auth_headers(second_token),
    )

    assert start_response.status_code == 404
    assert current_response.status_code == 404
    assert questions_response.status_code == 404


def test_current_question_before_start_returns_business_error(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=3)

    response = client.get(
        f"/api/v1/interviews/{session_id}/current-question",
        headers=auth_headers(token),
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Interview has not been started."


def test_invalid_llm_output_keeps_session_created_and_no_partial_questions(
    client: TestClient,
) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=3)
    override_llm(client, InvalidJSONLLMClient())

    start_response = client.post(
        f"/api/v1/interviews/{session_id}/start",
        headers=auth_headers(token),
    )
    detail_response = client.get(
        f"/api/v1/interviews/{session_id}",
        headers=auth_headers(token),
    )
    questions_response = client.get(
        f"/api/v1/interviews/{session_id}/questions",
        headers=auth_headers(token),
    )

    assert start_response.status_code == 502
    assert detail_response.json()["status"] == "CREATED"
    assert questions_response.status_code == 200
    assert questions_response.json() == []
