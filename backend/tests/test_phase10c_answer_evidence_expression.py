from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.prompts.answer_evaluation import build_answer_evaluation_prompt
from app.schemas.evaluation import EvaluationResult
from app.schemas.report import ReportGenerationResult
from app.services.expression_analysis import analyze_expression_quality
from tests.test_phase1_auth_interviews import auth_headers, login_user, register_user
from tests.test_phase2a_questions import FakeLLMClient, create_interview, override_llm
from tests.test_phase2b_answers import valid_answer_text

pytest_plugins = ["tests.test_phase1_auth_interviews"]


class EvidenceLLMClient(FakeLLMClient):
    def __init__(self, evidence_items: list[dict] | None = None) -> None:
        super().__init__()
        self.evidence_items = evidence_items or []
        self.report_calls = 0

    async def evaluate_answer(self, interview, question, answer_text: str) -> EvaluationResult:
        return EvaluationResult(
            total_score=78,
            logic_score=20,
            technical_score=24,
            expression_score=16,
            project_depth_score=18,
            strengths=["结构清晰"],
            weaknesses=["量化指标不足"],
            evidence_items=self.evidence_items,
            improvement_suggestion="补充更多量化数据。",
            detailed_feedback="回答整体完整，但结果量化还可以加强。",
        )

    async def generate_interview_report(
        self,
        interview,
        aggregate_scores: dict[str, int],
        records: list[dict],
    ) -> ReportGenerationResult:
        self.report_calls += 1
        return ReportGenerationResult(
            summary="本次面试表现稳定。",
            strengths=["结构较清晰"],
            weaknesses=["量化结果仍需加强"],
            role_gap_analysis="需要加强复杂场景下的方案拆解。",
            improvement_plan=[
                {
                    "priority": 1,
                    "topic": "表达量化结果",
                    "reason": "回答中缺少可衡量指标。",
                    "actions": ["补充项目指标", "练习 STAR 表达"],
                    "expected_outcome": "能够说明方案效果。",
                }
            ],
            next_practice_questions=["请说明一次接口性能优化经历。"],
        )


class PromptBuildFailureLLMClient(FakeLLMClient):
    async def evaluate_answer(self, interview, question, answer_text: str) -> EvaluationResult:
        raise ValueError("prompt construction failed before LLM call")


def start_interview_with_llm(client: TestClient, token: str, fake_llm) -> tuple[str, dict]:
    session_id = create_interview(client, token, question_count=3)
    override_llm(client, fake_llm)
    response = client.post(f"/api/v1/interviews/{session_id}/start", headers=auth_headers(token))
    assert response.status_code == 200
    return session_id, response.json()["current_question"]


def submit_answer(
    client: TestClient,
    token: str,
    session_id: str,
    question_id: str,
    answer_text: str,
    recording_duration_seconds: float | None = None,
):
    payload: dict[str, object] = {"question_id": question_id, "answer_text": answer_text}
    if recording_duration_seconds is not None:
        payload["recording_duration_seconds"] = recording_duration_seconds
    return client.post(
        f"/api/v1/interviews/{session_id}/answers",
        headers=auth_headers(token),
        json=payload,
    )


def test_answer_evaluation_prompt_builds_with_evidence_schema() -> None:
    interview = SimpleNamespace(
        target_role="Python 后端工程师",
        difficulty="intermediate",
        interview_type="technical",
    )
    question = SimpleNamespace(
        category="后端开发",
        question_text="请介绍一次接口性能优化经历。",
        expected_points=["定位瓶颈", "说明优化方案"],
    )
    answer_text = "我先通过监控定位慢查询，再补充索引并验证接口耗时下降。"

    prompt = build_answer_evaluation_prompt(
        interview=interview,
        question=question,
        answer_text=answer_text,
        rag_context="缓存与索引相关资料",
    )

    assert "evidence_items" in prompt
    assert "quote" in prompt
    assert "dimension" in prompt
    assert "polarity" in prompt
    assert "reason" in prompt
    assert "suggestion" in prompt
    assert question.question_text in prompt
    assert answer_text in prompt


def test_valid_quote_is_saved_and_returned_in_report(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    answer_text = "我会先说明项目背景，再介绍我的职责、技术方案、关键难点和最终结果。"
    quote = "技术方案、关键难点"
    fake_llm = EvidenceLLMClient(
        [
            {
                "dimension": "technical",
                "polarity": "strength",
                "quote": quote,
                "reason": "体现了技术方案意识。",
            }
        ]
    )
    session_id, question = start_interview_with_llm(client, token, fake_llm)

    response = submit_answer(client, token, session_id, question["id"], answer_text)

    assert response.status_code == 200
    evidence = response.json()["evaluation"]["evidence_items"]
    assert evidence[0]["quote"] == quote
    assert response.json()["evaluation"]["expression_metrics"]["speech_rate_status"] == "不可用"


def test_invalid_quotes_are_dropped_without_failing_score(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = EvidenceLLMClient(
        [
            {
                "dimension": "logic",
                "polarity": "strength",
                "quote": "候选人没有说过的内容",
                "reason": "不存在。",
            },
            {
                "dimension": "technical",
                "polarity": "improvement",
                "quote": "项目背景最终结果",
                "reason": "非连续片段。",
                "suggestion": "补充连续证据。",
            },
        ]
    )
    session_id, question = start_interview_with_llm(client, token, fake_llm)

    response = submit_answer(client, token, session_id, question["id"], valid_answer_text())

    assert response.status_code == 200
    assert response.json()["evaluation"]["total_score"] == 78
    assert response.json()["evaluation"]["evidence_items"] == []


def test_evidence_items_are_limited_to_six(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    answer_text = "首先我介绍背景。其次我介绍方案。最后我总结结果。因为方案有效，所以结果稳定。"
    quotes = ["首先", "背景", "其次", "方案", "最后", "结果", "稳定"]
    fake_llm = EvidenceLLMClient(
        [
            {
                "dimension": "expression",
                "polarity": "strength",
                "quote": quote,
                "reason": "来自原文。",
            }
            for quote in quotes
        ]
    )
    session_id, question = start_interview_with_llm(client, token, fake_llm)

    response = submit_answer(client, token, session_id, question["id"], answer_text)

    assert response.status_code == 200
    assert len(response.json()["evaluation"]["evidence_items"]) == 6


def test_manual_text_answer_does_not_fake_speech_rate(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id, question = start_interview_with_llm(client, token, EvidenceLLMClient())

    response = submit_answer(client, token, session_id, question["id"], valid_answer_text())

    metrics = response.json()["evaluation"]["expression_metrics"]
    assert response.status_code == 200
    assert metrics["estimated_speech_rate"] is None
    assert metrics["speech_rate_status"] == "不可用"


def test_failed_prompt_build_does_not_save_answer_or_advance_and_allows_retry(
    client: TestClient,
) -> None:
    register_user(client)
    token = login_user(client)
    session_id, question = start_interview_with_llm(
        client,
        token,
        PromptBuildFailureLLMClient(),
    )

    with pytest.raises(ValueError, match="prompt construction failed"):
        submit_answer(client, token, session_id, question["id"], valid_answer_text())
    detail_after_failure = client.get(
        f"/api/v1/interviews/{session_id}",
        headers=auth_headers(token),
    )
    answers_after_failure = client.get(
        f"/api/v1/interviews/{session_id}/answers",
        headers=auth_headers(token),
    )

    assert detail_after_failure.json()["current_question_index"] == 0
    assert detail_after_failure.json()["status"] == "IN_PROGRESS"
    assert answers_after_failure.json() == []

    override_llm(client, EvidenceLLMClient())
    retry = submit_answer(client, token, session_id, question["id"], valid_answer_text())
    answers_after_retry = client.get(
        f"/api/v1/interviews/{session_id}/answers",
        headers=auth_headers(token),
    )

    assert retry.status_code == 200
    assert retry.json()["evaluation"]["total_score"] == 78
    assert len(answers_after_retry.json()) == 1


def test_valid_recording_duration_generates_estimated_speech_rate(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id, question = start_interview_with_llm(client, token, EvidenceLLMClient())

    response = submit_answer(
        client,
        token,
        session_id,
        question["id"],
        valid_answer_text(),
        recording_duration_seconds=30,
    )

    metrics = response.json()["evaluation"]["expression_metrics"]
    assert response.status_code == 200
    assert response.json()["answer"]["recording_duration_seconds"] == 30
    assert metrics["estimated_speech_rate"] is not None
    assert metrics["speech_rate_status"] in {"偏慢", "适中", "偏快"}


def test_invalid_recording_duration_is_rejected(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id, question = start_interview_with_llm(client, token, EvidenceLLMClient())

    negative = submit_answer(
        client,
        token,
        session_id,
        question["id"],
        valid_answer_text(),
        recording_duration_seconds=-1,
    )
    too_large = submit_answer(
        client,
        token,
        session_id,
        question["id"],
        valid_answer_text(),
        recording_duration_seconds=301,
    )

    assert negative.status_code == 422
    assert too_large.status_code == 422


def test_expression_metric_rules_are_stable() -> None:
    metrics = analyze_expression_quality(
        "首先，我会说明背景。然后，然后介绍方案。所以最后总结结果。",
        recording_duration_seconds=20,
    )

    assert metrics["character_count"] > 0
    assert metrics["sentence_count"] == 3
    assert metrics["filler_word_count"] >= 2
    assert metrics["structure_signal_count"] >= 3
    assert metrics["estimated_speech_rate"] is not None


def test_report_returns_empty_structures_for_old_records(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    fake_llm = EvidenceLLMClient()
    session_id, question = start_interview_with_llm(client, token, fake_llm)
    first = submit_answer(client, token, session_id, question["id"], valid_answer_text()).json()
    second = submit_answer(
        client,
        token,
        session_id,
        first["next_question"]["id"],
        valid_answer_text(),
    ).json()
    submit_answer(client, token, session_id, second["next_question"]["id"], valid_answer_text())

    create_response = client.post(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )

    assert create_response.status_code == 200
    data = create_response.json()
    assert data["answer_evidence"]
    assert data["expression_analysis"]["summary"]["sample_size"] == 3


def test_other_user_cannot_read_evidence_report(client: TestClient) -> None:
    register_user(client, "first_user", "first_10c@example.com")
    first_token = login_user(client, "first_user")
    register_user(client, "second_user", "second_10c@example.com")
    second_token = login_user(client, "second_user")
    fake_llm = EvidenceLLMClient()
    session_id, question = start_interview_with_llm(client, first_token, fake_llm)
    first = submit_answer(
        client,
        first_token,
        session_id,
        question["id"],
        valid_answer_text(),
    ).json()
    second = submit_answer(
        client,
        first_token,
        session_id,
        first["next_question"]["id"],
        valid_answer_text(),
    ).json()
    submit_answer(
        client,
        first_token,
        session_id,
        second["next_question"]["id"],
        valid_answer_text(),
    )
    client.post(f"/api/v1/interviews/{session_id}/report", headers=auth_headers(first_token))

    response = client.get(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(second_token),
    )

    assert response.status_code == 404
