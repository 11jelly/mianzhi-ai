import asyncio

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.session import get_db_session
from app.models.interview_report import InterviewReport
from app.models.interview_session import InterviewSession
from app.schemas.report import ReportGenerationResult
from app.services.llm_client import (
    REPORT_FAILURE_MESSAGE,
    LLMGenerationError,
    LLMResponseFormatError,
    validate_report_generation,
)
from tests.test_phase1_auth_interviews import auth_headers, login_user, register_user
from tests.test_phase2a_questions import create_interview, override_llm
from tests.test_phase2b_answers import FakeEvaluationLLMClient, submit_answer

pytest_plugins = ["tests.test_phase1_auth_interviews"]


def read_session_status_from_db(client: TestClient, session_id: str) -> str:
    async def read_status() -> str:
        override = client.app.dependency_overrides[get_db_session]
        async for session in override():
            result = await session.execute(
                select(InterviewSession.status).where(InterviewSession.id == session_id)
            )
            return result.scalar_one()
        raise AssertionError("database session override did not yield")

    return asyncio.run(read_status())


def read_report_count_from_db(client: TestClient, session_id: str) -> int:
    async def read_count() -> int:
        override = client.app.dependency_overrides[get_db_session]
        async for session in override():
            result = await session.execute(
                select(func.count())
                .select_from(InterviewReport)
                .where(InterviewReport.session_id == session_id)
            )
            return result.scalar_one()
        raise AssertionError("database session override did not yield")

    return asyncio.run(read_count())


def force_session_status_in_db(client: TestClient, session_id: str, status: str) -> None:
    async def force_status() -> None:
        override = client.app.dependency_overrides[get_db_session]
        async for session in override():
            interview = await session.get(InterviewSession, session_id)
            assert interview is not None
            interview.status = status
            await session.commit()
            return
        raise AssertionError("database session override did not yield")

    asyncio.run(force_status())


class FakeReportLLMClient(FakeEvaluationLLMClient):
    def __init__(self) -> None:
        super().__init__()
        self.report_calls = 0

    async def generate_interview_report(
        self,
        interview,
        aggregate_scores: dict[str, int],
        records: list[dict],
    ) -> ReportGenerationResult:
        self.report_calls += 1
        assert aggregate_scores["overall_score"] == 78
        assert len(records) == interview.question_count
        return ReportGenerationResult(
            summary="本次面试表现稳定，能够覆盖主要技术点。",
            strengths=["回答结构较清晰", "具备基础工程意识"],
            weaknesses=["量化结果仍需加强", "部分方案细节不足"],
            role_gap_analysis="与目标岗位相比，还需要加强复杂场景下的方案拆解。",
            improvement_plan=[
                {
                    "priority": 1,
                    "topic": "接口性能优化",
                    "reason": "回答中缺少监控指标和定位路径。",
                    "actions": ["复盘慢接口案例", "练习说明缓存与索引策略"],
                    "expected_outcome": "能够完整说明性能问题定位和优化路径。",
                }
            ],
            next_practice_questions=[
                "请设计一个高并发订单查询接口。",
                "请说明 Redis 缓存击穿的治理方案。",
            ],
        )


class InvalidReportLLMClient(FakeEvaluationLLMClient):
    async def generate_interview_report(
        self,
        interview,
        aggregate_scores: dict[str, int],
        records: list[dict],
    ) -> ReportGenerationResult:
        try:
            validate_report_generation("第一次不是 JSON")
        except LLMResponseFormatError:
            pass
        try:
            return validate_report_generation('{"summary": "缺少字段"}')
        except LLMResponseFormatError as exc:
            raise LLMGenerationError(REPORT_FAILURE_MESSAGE, status_code=502) from exc


def create_ready_for_report_session(
    client: TestClient,
    token: str,
    fake_llm,
    question_count: int = 3,
) -> str:
    session_id = create_interview(client, token, question_count=question_count)
    override_llm(client, fake_llm)
    start_response = client.post(
        f"/api/v1/interviews/{session_id}/start",
        headers=auth_headers(token),
    )
    question = start_response.json()["current_question"]
    for _index in range(question_count):
        answer_response = submit_answer(client, token, session_id, question["id"])
        data = answer_response.json()
        question = data["next_question"] if data["next_question"] else question
    detail_response = client.get(f"/api/v1/interviews/{session_id}", headers=auth_headers(token))
    assert detail_response.json()["status"] == "READY_FOR_REPORT"
    return session_id


def test_ready_session_can_generate_report(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = FakeReportLLMClient()
    session_id = create_ready_for_report_session(client, token, fake_llm)

    response = client.post(f"/api/v1/interviews/{session_id}/report", headers=auth_headers(token))
    detail_response = client.get(f"/api/v1/interviews/{session_id}", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert data["overall_score"] == 78
    assert data["logic_score"] == 20
    assert data["technical_score"] == 24
    assert data["expression_score"] == 16
    assert data["project_depth_score"] == 18
    assert data["summary"]
    assert detail_response.json()["status"] == "COMPLETED"
    assert read_report_count_from_db(client, session_id) == 1
    assert read_session_status_from_db(client, session_id) == "COMPLETED"
    assert fake_llm.report_calls == 1


def test_non_ready_session_cannot_generate_report(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=3)
    override_llm(client, FakeReportLLMClient())

    response = client.post(f"/api/v1/interviews/{session_id}/report", headers=auth_headers(token))

    assert response.status_code == 409
    assert response.json()["detail"] == "Interview is not ready for report generation."


def test_user_cannot_generate_other_users_report(client: TestClient) -> None:
    register_user(client, "first_user", "first_report@example.com")
    first_token = login_user(client, "first_user")
    register_user(client, "second_user", "second_report@example.com")
    second_token = login_user(client, "second_user")
    fake_llm = FakeReportLLMClient()
    session_id = create_ready_for_report_session(client, first_token, fake_llm)

    response = client.post(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 404
    assert fake_llm.report_calls == 0


def test_completed_session_reuses_existing_report_without_llm_call(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = FakeReportLLMClient()
    session_id = create_ready_for_report_session(client, token, fake_llm)

    first_response = client.post(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )
    second_response = client.post(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )
    get_response = client.get(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert get_response.status_code == 200
    assert second_response.json()["id"] == first_response.json()["id"]
    assert get_response.json()["id"] == first_response.json()["id"]
    assert read_report_count_from_db(client, session_id) == 1
    assert read_session_status_from_db(client, session_id) == "COMPLETED"
    assert fake_llm.report_calls == 1


def test_get_interview_repairs_completed_status_when_report_exists(
    client: TestClient,
) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = FakeReportLLMClient()
    session_id = create_ready_for_report_session(client, token, fake_llm)
    create_response = client.post(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )
    force_session_status_in_db(client, session_id, "READY_FOR_REPORT")

    detail_response = client.get(f"/api/v1/interviews/{session_id}", headers=auth_headers(token))

    assert create_response.status_code == 200
    assert detail_response.status_code == 200
    assert detail_response.json()["status"] == "COMPLETED"
    assert read_report_count_from_db(client, session_id) == 1
    assert read_session_status_from_db(client, session_id) == "COMPLETED"
    assert fake_llm.report_calls == 1


def test_get_report_repairs_completed_status_when_report_exists(
    client: TestClient,
) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = FakeReportLLMClient()
    session_id = create_ready_for_report_session(client, token, fake_llm)
    create_response = client.post(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )
    force_session_status_in_db(client, session_id, "READY_FOR_REPORT")

    get_response = client.get(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )

    assert create_response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json()["id"] == create_response.json()["id"]
    assert read_report_count_from_db(client, session_id) == 1
    assert read_session_status_from_db(client, session_id) == "COMPLETED"
    assert fake_llm.report_calls == 1


def test_repeated_report_generation_repairs_completed_status_when_report_exists(
    client: TestClient,
) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = FakeReportLLMClient()
    session_id = create_ready_for_report_session(client, token, fake_llm)
    create_response = client.post(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )
    force_session_status_in_db(client, session_id, "READY_FOR_REPORT")

    second_response = client.post(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )

    assert create_response.status_code == 200
    assert second_response.status_code == 200
    assert second_response.json()["id"] == create_response.json()["id"]
    assert read_report_count_from_db(client, session_id) == 1
    assert read_session_status_from_db(client, session_id) == "COMPLETED"
    assert fake_llm.report_calls == 1


def test_report_generation_failure_keeps_ready_state(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = InvalidReportLLMClient()
    session_id = create_ready_for_report_session(client, token, fake_llm)

    response = client.post(f"/api/v1/interviews/{session_id}/report", headers=auth_headers(token))
    detail_response = client.get(f"/api/v1/interviews/{session_id}", headers=auth_headers(token))
    get_response = client.get(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )

    assert response.status_code == 502
    assert response.json()["detail"] == REPORT_FAILURE_MESSAGE
    assert detail_response.json()["status"] == "READY_FOR_REPORT"
    assert get_response.status_code == 404


def test_get_report_returns_completed_report(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = FakeReportLLMClient()
    session_id = create_ready_for_report_session(client, token, fake_llm)

    create_response = client.post(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )
    get_response = client.get(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )

    assert create_response.status_code == 200
    assert get_response.status_code == 200
    assert get_response.json()["id"] == create_response.json()["id"]
    assert "expected_points" not in get_response.json()
