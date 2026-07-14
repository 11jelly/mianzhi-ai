import asyncio
from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.session import get_db_session
from app.models.interview_knowledge_base_link import InterviewKnowledgeBaseLink
from app.models.interview_report import InterviewReport
from app.models.interview_session import InterviewSession
from app.models.knowledge_base import KnowledgeBase
from app.models.user import User
from tests.test_phase1_auth_interviews import auth_headers, login_user, register_user

pytest_plugins = ["tests.test_phase1_auth_interviews"]


def create_completed_report(
    client: TestClient,
    *,
    username: str,
    target_role: str = "Python Backend",
    status: str = "COMPLETED",
    created_at: datetime | None = None,
    overall_score: int = 80,
    logic_score: int = 20,
    technical_score: int = 24,
    expression_score: int = 16,
    project_depth_score: int = 20,
    with_report: bool = True,
    knowledge_base_name: str | None = None,
) -> str:
    async def create_record() -> str:
        override = client.app.dependency_overrides[get_db_session]
        async for session in override():
            user_result = await session.execute(select(User).where(User.username == username))
            user = user_result.scalar_one()
            interview = InterviewSession(
                user_id=user.id,
                target_role=target_role,
                difficulty="intermediate",
                interview_type="technical",
                question_count=3,
                status=status,
            )
            session.add(interview)
            await session.flush()
            if knowledge_base_name:
                knowledge_base = KnowledgeBase(
                    owner_id=user.id,
                    name=knowledge_base_name,
                    description="analytics test kb",
                )
                session.add(knowledge_base)
                await session.flush()
                session.add(
                    InterviewKnowledgeBaseLink(
                        interview_session_id=interview.id,
                        knowledge_base_id=knowledge_base.id,
                    )
                )
            if with_report:
                session.add(
                    InterviewReport(
                        session_id=interview.id,
                        overall_score=overall_score,
                        logic_score=logic_score,
                        technical_score=technical_score,
                        expression_score=expression_score,
                        project_depth_score=project_depth_score,
                        summary="summary",
                        strengths=["stable"],
                        weaknesses=["practice"],
                        role_gap_analysis="gap",
                        improvement_plan=[
                            {
                                "priority": 1,
                                "topic": "API expression",
                                "reason": "needs clarity",
                                "actions": ["review history"],
                                "expected_outcome": "clearer answers",
                            }
                        ],
                        next_practice_questions=["practice one"],
                        created_at=created_at or datetime.now(UTC),
                    )
                )
            await session.commit()
            return interview.id
        raise AssertionError("database session override did not yield")

    return asyncio.run(create_record())


def test_overview_returns_empty_state_without_completed_reports(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)

    response = client.get("/api/v1/analytics/overview", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json() == {
        "completed_interview_count": 0,
        "average_overall_score": 0.0,
        "latest_report": None,
        "ability_averages": None,
        "weakest_dimension": None,
        "latest_improvement_plan": [],
    }


def test_overview_only_counts_completed_sessions_with_reports(client: TestClient) -> None:
    register_user(client, "analytics_user", "analytics@example.com")
    token = login_user(client, "analytics_user")
    now = datetime.now(UTC)
    create_completed_report(
        client,
        username="analytics_user",
        created_at=now - timedelta(days=3),
        overall_score=70,
        logic_score=18,
        technical_score=20,
        expression_score=14,
        project_depth_score=18,
    )
    latest_id = create_completed_report(
        client,
        username="analytics_user",
        created_at=now,
        overall_score=80,
        logic_score=20,
        technical_score=24,
        expression_score=16,
        project_depth_score=20,
    )
    create_completed_report(client, username="analytics_user", status="IN_PROGRESS")
    create_completed_report(client, username="analytics_user", status="READY_FOR_REPORT")
    create_completed_report(client, username="analytics_user", with_report=False)

    response = client.get("/api/v1/analytics/overview", headers=auth_headers(token))

    assert response.status_code == 200
    data = response.json()
    assert data["completed_interview_count"] == 2
    assert data["average_overall_score"] == 75.0
    assert data["latest_report"]["session_id"] == latest_id
    assert data["latest_report"]["overall_score"] == 80
    assert data["ability_averages"] == {
        "logic_score": 19.0,
        "technical_score": 22.0,
        "expression_score": 15.0,
        "project_depth_score": 19.0,
    }
    assert data["latest_improvement_plan"] == [{"priority": "P1", "topic": "API expression"}]


def test_weakest_dimension_uses_latest_five_reports(client: TestClient) -> None:
    register_user(client, "weak_user", "weak@example.com")
    token = login_user(client, "weak_user")
    now = datetime.now(UTC)
    for index in range(6):
        create_completed_report(
            client,
            username="weak_user",
            created_at=now - timedelta(days=6 - index),
            overall_score=70 + index,
            logic_score=24,
            technical_score=29,
            expression_score=10 + index,
            project_depth_score=23,
        )

    response = client.get("/api/v1/analytics/overview", headers=auth_headers(token))

    assert response.status_code == 200
    weakest = response.json()["weakest_dimension"]
    assert weakest["key"] == "expression_score"
    assert weakest["label"] == "表达清晰度"
    assert weakest["average_score"] == 13.0
    assert weakest["max_score"] == 20


def test_trend_orders_by_report_time_and_filters(client: TestClient) -> None:
    register_user(client, "trend_user", "trend@example.com")
    token = login_user(client, "trend_user")
    now = datetime.now(UTC)
    old_id = create_completed_report(
        client,
        username="trend_user",
        target_role="Python Backend",
        created_at=now - timedelta(days=40),
        overall_score=60,
    )
    first_id = create_completed_report(
        client,
        username="trend_user",
        target_role="Python Backend",
        created_at=now - timedelta(days=2),
        overall_score=72,
    )
    second_id = create_completed_report(
        client,
        username="trend_user",
        target_role="Java Backend",
        created_at=now - timedelta(days=1),
        overall_score=82,
    )

    response = client.get("/api/v1/analytics/trend?days=30", headers=auth_headers(token))
    filtered_response = client.get(
        "/api/v1/analytics/trend?days=365&target_role=Python Backend",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert [item["session_id"] for item in response.json()["items"]] == [first_id, second_id]
    assert filtered_response.status_code == 200
    assert [item["session_id"] for item in filtered_response.json()["items"]] == [
        old_id,
        first_id,
    ]


def test_history_paginates_and_returns_knowledge_base_names(client: TestClient) -> None:
    register_user(client, "history_user", "history@example.com")
    token = login_user(client, "history_user")
    now = datetime.now(UTC)
    create_completed_report(
        client,
        username="history_user",
        created_at=now - timedelta(days=2),
        overall_score=70,
    )
    latest_id = create_completed_report(
        client,
        username="history_user",
        created_at=now,
        overall_score=88,
        knowledge_base_name="Python JD",
    )

    response = client.get(
        "/api/v1/analytics/history?page=1&page_size=1",
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    data = response.json()
    assert data["meta"] == {"page": 1, "page_size": 1, "total": 2}
    assert len(data["items"]) == 1
    assert data["items"][0]["session_id"] == latest_id
    assert data["items"][0]["knowledge_base_names"] == ["Python JD"]


def test_user_cannot_read_other_users_analytics(client: TestClient) -> None:
    register_user(client, "owner", "owner_analytics@example.com")
    owner_token = login_user(client, "owner")
    register_user(client, "viewer", "viewer_analytics@example.com")
    viewer_token = login_user(client, "viewer")
    create_completed_report(client, username="owner", overall_score=99)

    owner_response = client.get("/api/v1/analytics/overview", headers=auth_headers(owner_token))
    viewer_response = client.get("/api/v1/analytics/overview", headers=auth_headers(viewer_token))

    assert owner_response.status_code == 200
    assert owner_response.json()["completed_interview_count"] == 1
    assert viewer_response.status_code == 200
    assert viewer_response.json()["completed_interview_count"] == 0
