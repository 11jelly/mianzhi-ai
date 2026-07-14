import sys
import types

from fastapi.testclient import TestClient

from app.api.v1.interviews import get_llm_client
from app.api.v1.knowledge_bases import get_embedding_client
from app.schemas.evaluation import EvaluationResult
from app.schemas.llm import FollowUpDecision, GeneratedQuestionSet
from app.schemas.report import ReportGenerationResult
from tests.test_phase1_auth_interviews import auth_headers, login_user, register_user
from tests.test_phase2a_questions import create_interview, override_llm
from tests.test_phase2b_answers import submit_answer

pytest_plugins = ["tests.test_phase1_auth_interviews"]


class FakeEmbeddingClient:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.calls: list[tuple[list[str], str]] = []

    async def embed_texts(self, texts: list[str], input_type: str) -> list[list[float]]:
        self.calls.append((texts, input_type))
        if self.fail:
            raise RuntimeError("fake embedding failure")
        return [self._vector(text, input_type) for text in texts]

    def _vector(self, text: str, input_type: str) -> list[float]:
        normalized = text.lower()
        if "cache" in normalized or "缓存" in normalized or input_type == "query":
            return [1.0, 0.0, 0.0, 0.0]
        if "database" in normalized or "数据库" in normalized:
            return [0.0, 1.0, 0.0, 0.0]
        return [0.5, 0.5, 0.0, 0.0]


class RagAwareLLMClient:
    def __init__(self) -> None:
        self.question_rag_context = ""
        self.evaluation_rag_context = ""
        self.report_rag_context = ""
        self.report_calls = 0

    async def generate_interview_questions(
        self,
        interview,
        rag_context: str = "无",
    ) -> GeneratedQuestionSet:
        self.question_rag_context = rag_context
        return GeneratedQuestionSet(
            questions=[
                {
                    "sequence": sequence,
                    "category": "技术基础",
                    "question_text": f"请说明缓存与数据库优化方案 {sequence}",
                    "expected_points": ["缓存", "数据库"],
                }
                for sequence in range(1, interview.question_count + 1)
            ]
        )

    async def evaluate_answer(
        self,
        interview,
        question,
        answer_text: str,
        rag_context: str = "无",
    ) -> EvaluationResult:
        self.evaluation_rag_context = rag_context
        return EvaluationResult(
            total_score=80,
            logic_score=20,
            technical_score=25,
            expression_score=15,
            project_depth_score=20,
            strengths=["结构清晰"],
            weaknesses=["可以补充细节"],
            improvement_suggestion="补充指标和权衡。",
            detailed_feedback="回答可用。",
        )

    async def decide_follow_up(self, state: dict) -> FollowUpDecision:
        return FollowUpDecision(
            should_follow_up=False,
            follow_up_category="",
            follow_up_question="",
            reason_summary="无需追问。",
        )

    async def generate_interview_report(
        self,
        interview,
        aggregate_scores: dict[str, int],
        records: list[dict],
        rag_context: str = "无",
    ) -> ReportGenerationResult:
        self.report_calls += 1
        self.report_rag_context = rag_context
        return ReportGenerationResult(
            summary="结合岗位知识库生成报告。",
            strengths=["基础扎实"],
            weaknesses=["需要更贴近岗位要求"],
            role_gap_analysis="岗位要求中强调缓存治理。",
            improvement_plan=[
                {
                    "priority": 1,
                    "topic": "缓存治理",
                    "reason": "知识库强调缓存能力。",
                    "actions": ["练习缓存穿透治理"],
                    "expected_outcome": "能说明完整方案。",
                }
            ],
            next_practice_questions=["请说明缓存击穿治理方案。"],
        )


def override_embedding(client: TestClient, fake_embedding) -> None:
    client.app.dependency_overrides[get_embedding_client] = lambda: fake_embedding


def create_base(client: TestClient, token: str, name: str = "Python 后端岗位") -> dict:
    response = client.post(
        "/api/v1/knowledge-bases",
        headers=auth_headers(token),
        json={"name": name, "description": "岗位 JD 与项目要求"},
    )
    assert response.status_code == 201
    return response.json()


def upload_document(
    client: TestClient,
    token: str,
    knowledge_base_id: str,
    content: bytes,
    filename: str = "jd.txt",
    content_type: str = "text/plain",
):
    return client.post(
        f"/api/v1/knowledge-bases/{knowledge_base_id}/documents",
        headers=auth_headers(token),
        files={"file": (filename, content, content_type)},
    )


def test_user_can_create_list_and_delete_own_knowledge_base(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)

    knowledge_base = create_base(client, token)
    list_response = client.get("/api/v1/knowledge-bases", headers=auth_headers(token))
    delete_response = client.delete(
        f"/api/v1/knowledge-bases/{knowledge_base['id']}",
        headers=auth_headers(token),
    )
    list_after_delete = client.get("/api/v1/knowledge-bases", headers=auth_headers(token))

    assert list_response.status_code == 200
    assert list_response.json()[0]["id"] == knowledge_base["id"]
    assert delete_response.status_code == 204
    assert list_after_delete.json() == []


def test_user_cannot_access_or_upload_to_other_users_knowledge_base(
    client: TestClient,
) -> None:
    register_user(client, "first_user", "first_rag@example.com")
    first_token = login_user(client, "first_user")
    register_user(client, "second_user", "second_rag@example.com")
    second_token = login_user(client, "second_user")
    knowledge_base = create_base(client, first_token)
    override_embedding(client, FakeEmbeddingClient())

    read_response = client.get(
        f"/api/v1/knowledge-bases/{knowledge_base['id']}",
        headers=auth_headers(second_token),
    )
    upload_response = upload_document(
        client,
        second_token,
        knowledge_base["id"],
        b"cache requirements",
    )

    assert read_response.status_code == 404
    assert upload_response.status_code == 404


def test_upload_txt_md_and_pdf_documents_are_parsed_and_chunked(
    client: TestClient,
    monkeypatch,
) -> None:
    register_user(client)
    token = login_user(client)
    knowledge_base = create_base(client, token)
    fake_embedding = FakeEmbeddingClient()
    override_embedding(client, fake_embedding)

    fake_pypdf = types.SimpleNamespace(
        PdfReader=lambda _stream: types.SimpleNamespace(
            pages=[
                types.SimpleNamespace(extract_text=lambda: "PDF 中要求掌握缓存和数据库优化。")
            ]
        )
    )
    monkeypatch.setitem(sys.modules, "pypdf", fake_pypdf)

    txt_response = upload_document(
        client,
        token,
        knowledge_base["id"],
        "缓存 cache 要求\n数据库 database 要求".encode(),
        "jd.txt",
    )
    md_response = upload_document(
        client,
        token,
        knowledge_base["id"],
        "# 项目说明\n需要 Redis 缓存治理".encode(),
        "project.md",
        "text/markdown",
    )
    pdf_response = upload_document(
        client,
        token,
        knowledge_base["id"],
        b"%PDF fake",
        "jd.pdf",
        "application/pdf",
    )

    assert txt_response.status_code == 200
    assert md_response.status_code == 200
    assert pdf_response.status_code == 200
    assert txt_response.json()["status"] == "READY"
    assert txt_response.json()["chunk_count"] >= 1
    assert fake_embedding.calls[0][1] == "document"


def test_invalid_empty_large_and_duplicate_documents_are_rejected(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    knowledge_base = create_base(client, token)
    override_embedding(client, FakeEmbeddingClient())

    empty_response = upload_document(client, token, knowledge_base["id"], b"")
    invalid_response = upload_document(
        client,
        token,
        knowledge_base["id"],
        b"not allowed",
        "jd.docx",
    )
    first_response = upload_document(client, token, knowledge_base["id"], b"cache requirements")
    duplicate_response = upload_document(client, token, knowledge_base["id"], b"cache requirements")
    large_response = upload_document(
        client,
        token,
        knowledge_base["id"],
        b"x" * (6 * 1024 * 1024),
        "large.txt",
    )

    assert empty_response.status_code == 422
    assert invalid_response.status_code == 422
    assert first_response.status_code == 200
    assert duplicate_response.status_code == 409
    assert large_response.status_code == 413


def test_embedding_failure_marks_document_failed_without_chunks(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    knowledge_base = create_base(client, token)
    override_embedding(client, FakeEmbeddingClient(fail=True))

    response = upload_document(client, token, knowledge_base["id"], b"cache requirements")
    documents_response = client.get(
        f"/api/v1/knowledge-bases/{knowledge_base['id']}/documents",
        headers=auth_headers(token),
    )

    assert response.status_code == 500 or response.status_code == 502
    document = documents_response.json()[0]
    assert document["status"] == "FAILED"
    assert document["chunk_count"] == 0


def test_search_results_are_sorted_by_cosine_similarity(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    knowledge_base = create_base(client, token)
    override_embedding(client, FakeEmbeddingClient())
    upload_document(client, token, knowledge_base["id"], b"database optimization requirements")
    upload_document(client, token, knowledge_base["id"], b"cache optimization requirements")

    response = client.post(
        f"/api/v1/knowledge-bases/{knowledge_base['id']}/search",
        headers=auth_headers(token),
        json={"query": "cache requirements", "top_k": 2},
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["score"] >= items[1]["score"]
    assert "cache" in items[0]["content_preview"]


def test_create_interview_can_link_owned_knowledge_base(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    knowledge_base = create_base(client, token)

    response = client.post(
        "/api/v1/interviews",
        headers=auth_headers(token),
        json={
            "target_role": "Python backend developer",
            "difficulty": "intermediate",
            "interview_type": "technical",
            "question_count": 3,
            "knowledge_base_ids": [knowledge_base["id"]],
        },
    )

    assert response.status_code == 201
    assert response.json()["knowledge_bases"][0]["id"] == knowledge_base["id"]


def test_interview_flow_receives_rag_context_when_knowledge_base_is_linked(
    client: TestClient,
) -> None:
    register_user(client)
    token = login_user(client)
    knowledge_base = create_base(client, token)
    fake_embedding = FakeEmbeddingClient()
    fake_llm = RagAwareLLMClient()
    override_embedding(client, fake_embedding)
    client.app.dependency_overrides[get_llm_client] = lambda: fake_llm
    upload_document(client, token, knowledge_base["id"], b"cache optimization requirements")

    create_response = client.post(
        "/api/v1/interviews",
        headers=auth_headers(token),
        json={
            "target_role": "Python backend developer",
            "difficulty": "intermediate",
            "interview_type": "technical",
            "question_count": 3,
            "knowledge_base_ids": [knowledge_base["id"]],
        },
    )
    session_id = create_response.json()["id"]
    start_response = client.post(
        f"/api/v1/interviews/{session_id}/start",
        headers=auth_headers(token),
    )
    question = start_response.json()["current_question"]
    first = submit_answer(client, token, session_id, question["id"]).json()
    second = submit_answer(client, token, session_id, first["next_question"]["id"]).json()
    submit_answer(client, token, session_id, second["next_question"]["id"])
    report_response = client.post(
        f"/api/v1/interviews/{session_id}/report",
        headers=auth_headers(token),
    )

    assert start_response.status_code == 200
    assert report_response.status_code == 200
    assert "cache" in fake_llm.question_rag_context
    assert "cache" in fake_llm.evaluation_rag_context
    assert "cache" in fake_llm.report_rag_context
    assert report_response.json()["overall_score"] == 80


def test_unlinked_interview_flow_keeps_old_llm_signature(client: TestClient) -> None:
    register_user(client)
    token = login_user(client)
    session_id = create_interview(client, token, question_count=3)
    from tests.test_phase2b_answers import FakeEvaluationLLMClient

    override_llm(client, FakeEvaluationLLMClient())

    response = client.post(f"/api/v1/interviews/{session_id}/start", headers=auth_headers(token))

    assert response.status_code == 200
