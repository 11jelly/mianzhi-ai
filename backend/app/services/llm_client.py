import json
import re
from typing import Any

from openai import APIConnectionError, APITimeoutError, AsyncOpenAI, OpenAIError
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.exceptions import AppError
from app.models.interview_question import InterviewQuestion
from app.models.interview_session import InterviewSession
from app.prompts.answer_evaluation import (
    build_answer_evaluation_prompt,
    build_answer_evaluation_repair_prompt,
)
from app.prompts.follow_up_decision import build_follow_up_decision_prompt
from app.prompts.question_generation import build_question_generation_prompt
from app.prompts.report_generation import (
    build_report_generation_prompt,
    build_report_generation_repair_prompt,
)
from app.schemas.evaluation import EvaluationResult
from app.schemas.llm import FollowUpDecision, GeneratedQuestionSet
from app.schemas.report import ReportGenerationResult

EVALUATION_FAILURE_MESSAGE = "AI 暂时无法完成本题评分，请稍后重试。当前回答未保存。"
REPORT_FAILURE_MESSAGE = "AI 暂时无法生成综合诊断报告，请稍后重试。"
FOLLOW_UP_FAILURE_MESSAGE = "AI 追问决策暂时不可用，已进入下一题。"
REPORT_FORBIDDEN_SCORE_FIELDS = {
    "overall_score",
    "total_score",
    "logic_score",
    "technical_score",
    "expression_score",
    "project_depth_score",
}


class LLMConfigurationError(AppError):
    pass


class LLMGenerationError(AppError):
    pass


class LLMResponseFormatError(LLMGenerationError):
    pass


def clean_json_payload(content: str) -> str:
    stripped = content.strip()
    fenced = re.match(r"^```(?:json)?\s*(.*?)\s*```$", stripped, re.DOTALL | re.IGNORECASE)
    if fenced:
        return fenced.group(1).strip()
    return stripped


def extract_json_object(content: str) -> dict[str, Any]:
    stripped = clean_json_payload(content)
    decoder = json.JSONDecoder()
    try:
        payload = json.loads(stripped)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        return payload

    fenced_blocks = re.findall(
        r"```(?:json)?\s*(.*?)\s*```",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )
    for block in fenced_blocks:
        try:
            payload = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload

    # Some models add a short sentence before or after the JSON. Use the JSON
    # decoder from every object start so nested braces and strings are handled
    # by a real parser instead of brittle brace slicing.
    for match in re.finditer(r"\{", content):
        try:
            payload, _index = decoder.raw_decode(content[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return payload

    raise LLMResponseFormatError("LLM response does not contain a JSON object.", status_code=502)


def normalize_evaluation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)

    # Compatibility rule 1: Some providers return a single string for list
    # fields. Converting it to a one-item JSON string array preserves meaning
    # without accepting missing or structurally invalid fields.
    for field_name in ("strengths", "weaknesses"):
        value = normalized.get(field_name)
        if isinstance(value, str):
            normalized[field_name] = [value]
    if not isinstance(normalized.get("evidence_items"), list):
        normalized["evidence_items"] = []

    # Compatibility rule 2: If all four dimension scores are valid integers,
    # the canonical total is the sum. This keeps strong validation for each
    # dimension while tolerating arithmetic mistakes in total_score.
    score_fields = (
        ("logic_score", 0, 25),
        ("technical_score", 0, 30),
        ("expression_score", 0, 20),
        ("project_depth_score", 0, 25),
    )
    dimension_scores: list[int] = []
    for field_name, minimum, maximum in score_fields:
        value = normalized.get(field_name)
        if not isinstance(value, int) or not minimum <= value <= maximum:
            break
        dimension_scores.append(value)
    if len(dimension_scores) == len(score_fields):
        normalized["total_score"] = sum(dimension_scores)

    return normalized


def normalize_report_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    for field_name in ("strengths", "weaknesses", "next_practice_questions"):
        value = normalized.get(field_name)
        if isinstance(value, str):
            normalized[field_name] = [value]
    return normalized


def validate_generated_questions(
    raw_content: str,
    expected_count: int,
) -> GeneratedQuestionSet:
    try:
        payload = json.loads(clean_json_payload(raw_content))
        question_set = GeneratedQuestionSet.model_validate(payload)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise LLMGenerationError("LLM 返回的题目 JSON 格式不合法。", status_code=502) from exc

    questions = question_set.questions
    if len(questions) != expected_count:
        raise LLMGenerationError("LLM 返回的题目数量不符合会话配置。", status_code=502)

    expected_sequences = list(range(1, expected_count + 1))
    actual_sequences = [question.sequence for question in questions]
    if actual_sequences != expected_sequences:
        raise LLMGenerationError("LLM 返回的题目序号必须从 1 连续递增。", status_code=502)

    normalized_texts = [question.question_text.strip() for question in questions]
    if len(set(normalized_texts)) != len(normalized_texts):
        raise LLMGenerationError("LLM 返回了重复题目。", status_code=502)

    return question_set


def validate_answer_evaluation(raw_content: str) -> EvaluationResult:
    try:
        payload = normalize_evaluation_payload(extract_json_object(raw_content))
        return EvaluationResult.model_validate(payload)
    except (LLMResponseFormatError, ValidationError, TypeError, ValueError) as exc:
        raise LLMResponseFormatError(EVALUATION_FAILURE_MESSAGE, status_code=502) from exc


def validate_report_generation(raw_content: str) -> ReportGenerationResult:
    try:
        payload = normalize_report_payload(extract_json_object(raw_content))
        forbidden_fields = REPORT_FORBIDDEN_SCORE_FIELDS.intersection(payload)
        if forbidden_fields:
            fields = ", ".join(sorted(forbidden_fields))
            raise ValueError(f"report must not include score fields: {fields}")
        return ReportGenerationResult.model_validate(payload)
    except (LLMResponseFormatError, ValidationError, TypeError, ValueError) as exc:
        raise LLMResponseFormatError(REPORT_FAILURE_MESSAGE, status_code=502) from exc


def validate_follow_up_decision(raw_content: str) -> FollowUpDecision:
    try:
        payload = extract_json_object(raw_content)
        return FollowUpDecision.model_validate(payload)
    except (LLMResponseFormatError, ValidationError, TypeError, ValueError) as exc:
        raise LLMResponseFormatError(FOLLOW_UP_FAILURE_MESSAGE, status_code=502) from exc


class LLMClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _create_client(self) -> AsyncOpenAI:
        if not self.settings.llm_api_key or not self.settings.llm_base_url:
            raise LLMConfigurationError("LLM 配置缺失，无法调用模型。", status_code=503)
        return AsyncOpenAI(
            api_key=self.settings.llm_api_key,
            base_url=self.settings.llm_base_url,
            timeout=45.0,
        )

    async def _complete(self, client: AsyncOpenAI, prompt: str, temperature: float) -> str:
        try:
            response = await client.chat.completions.create(
                model=self.settings.llm_model,
                messages=[
                    {"role": "system", "content": "你只输出严格 JSON，不输出 Markdown 或解释。"},
                    {"role": "user", "content": prompt},
                ],
                temperature=temperature,
            )
        except (APITimeoutError, APIConnectionError) as exc:
            raise LLMGenerationError("LLM 服务连接超时或网络异常。", status_code=503) from exc
        except OpenAIError as exc:
            raise LLMGenerationError("LLM 服务调用失败。", status_code=502) from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise LLMGenerationError("LLM 未返回内容。", status_code=502)
        return content

    async def generate_interview_questions(
        self,
        interview: InterviewSession,
        rag_context: str = "无",
        resume_context: str = "",
    ) -> GeneratedQuestionSet:
        client = self._create_client()
        prompt = build_question_generation_prompt(interview, rag_context, resume_context)
        content = await self._complete(client, prompt, temperature=0.4)
        return validate_generated_questions(content, interview.question_count)

    async def evaluate_answer(
        self,
        interview: InterviewSession,
        question: InterviewQuestion,
        answer_text: str,
        rag_context: str = "无",
    ) -> EvaluationResult:
        client = self._create_client()
        prompt = build_answer_evaluation_prompt(interview, question, answer_text, rag_context)
        content = await self._complete(client, prompt, temperature=0.2)
        try:
            return validate_answer_evaluation(content)
        except LLMResponseFormatError as first_error:
            repair_prompt = build_answer_evaluation_repair_prompt(
                original_prompt=prompt,
                invalid_content=content,
                error_message=str(first_error.__cause__ or first_error),
            )

        repair_content = await self._complete(client, repair_prompt, temperature=0.0)
        try:
            return validate_answer_evaluation(repair_content)
        except LLMResponseFormatError as second_error:
            raise LLMGenerationError(EVALUATION_FAILURE_MESSAGE, status_code=502) from second_error

    async def generate_interview_report(
        self,
        interview: InterviewSession,
        aggregate_scores: dict[str, int],
        records: list[dict],
        rag_context: str = "无",
    ) -> ReportGenerationResult:
        client = self._create_client()
        prompt = build_report_generation_prompt(interview, aggregate_scores, records, rag_context)
        content = await self._complete(client, prompt, temperature=0.3)
        try:
            return validate_report_generation(content)
        except LLMResponseFormatError as first_error:
            repair_prompt = build_report_generation_repair_prompt(
                original_prompt=prompt,
                invalid_content=content,
                error_message=str(first_error.__cause__ or first_error),
            )

        repair_content = await self._complete(client, repair_prompt, temperature=0.0)
        try:
            return validate_report_generation(repair_content)
        except LLMResponseFormatError as second_error:
            raise LLMGenerationError(REPORT_FAILURE_MESSAGE, status_code=502) from second_error

    async def decide_follow_up(self, state: dict) -> FollowUpDecision:
        client = self._create_client()
        prompt = build_follow_up_decision_prompt(state)
        content = await self._complete(client, prompt, temperature=0.2)
        try:
            return validate_follow_up_decision(content)
        except LLMResponseFormatError as first_error:
            repair_prompt = (
                "请把上一次追问决策修复为合法 JSON，不要输出 Markdown 或解释。\n"
                f"原始任务：\n{prompt}\n\n"
                f"上一次非法输出：\n{content}\n\n"
                f"内部错误：{first_error.__cause__ or first_error}"
            )
        repair_content = await self._complete(client, repair_prompt, temperature=0.0)
        try:
            return validate_follow_up_decision(repair_content)
        except LLMResponseFormatError as second_error:
            raise LLMGenerationError(FOLLOW_UP_FAILURE_MESSAGE, status_code=502) from second_error


def get_llm_client() -> LLMClient:
    return LLMClient()
