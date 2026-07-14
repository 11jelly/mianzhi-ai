from langgraph.graph import END, StateGraph

from app.agents.state import AgentState
from app.services.llm_client import LLMClient, LLMGenerationError


def load_context(state: AgentState) -> AgentState:
    return state


def check_follow_up_eligibility(state: AgentState) -> AgentState:
    score = int(state["evaluation"]["total_score"])
    can_follow_up = (
        state["question_type"] == "PRIMARY"
        and state.get("max_follow_ups_per_primary", 1) > 0
        and state["follow_up_count"] < state["max_follow_ups_per_session"]
        and state["follow_up_min_score"] <= score <= state["follow_up_score_threshold"]
    )
    return {**state, "can_follow_up": can_follow_up}


async def decide_follow_up(state: AgentState, llm_client: LLMClient) -> AgentState:
    if not state.get("can_follow_up"):
        return {
            **state,
            "agent_action": "NEXT_PRIMARY",
            "reason_summary": "当前回答不满足追问条件。",
        }
    try:
        decision = await llm_client.decide_follow_up(state)
    except LLMGenerationError:
        return {
            **state,
            "agent_action": "NEXT_PRIMARY",
            "reason_summary": "Agent 决策失败，已回退到下一道主问题。",
        }
    if not decision.should_follow_up:
        return {
            **state,
            "agent_action": "NEXT_PRIMARY",
            "reason_summary": decision.reason_summary,
        }
    return {
        **state,
        "agent_action": "FOLLOW_UP",
        "follow_up_question": decision.follow_up_question,
        "follow_up_category": decision.follow_up_category,
        "reason_summary": decision.reason_summary,
    }


def create_follow_up(state: AgentState) -> AgentState:
    return state


def select_next_primary(state: AgentState) -> AgentState:
    if state["current_question_index"] >= state["question_count"]:
        return {**state, "agent_action": "READY_FOR_REPORT"}
    return {**state, "agent_action": "NEXT_PRIMARY"}


def ready_for_report(state: AgentState) -> AgentState:
    return {**state, "agent_action": "READY_FOR_REPORT"}


def route_after_decision(state: AgentState) -> str:
    if state.get("agent_action") == "FOLLOW_UP":
        return "create_follow_up"
    return "select_next_primary"


def route_after_next_primary(state: AgentState) -> str:
    if state.get("agent_action") == "READY_FOR_REPORT":
        return "ready_for_report"
    return END


def build_interview_graph(llm_client: LLMClient):
    async def decide_follow_up_node(state: AgentState) -> AgentState:
        return await decide_follow_up(state, llm_client)

    graph = StateGraph(AgentState)
    graph.add_node("load_context", load_context)
    graph.add_node("check_follow_up_eligibility", check_follow_up_eligibility)
    graph.add_node("decide_follow_up", decide_follow_up_node)
    graph.add_node("create_follow_up", create_follow_up)
    graph.add_node("select_next_primary", select_next_primary)
    graph.add_node("ready_for_report", ready_for_report)
    graph.set_entry_point("load_context")
    graph.add_edge("load_context", "check_follow_up_eligibility")
    graph.add_edge("check_follow_up_eligibility", "decide_follow_up")
    graph.add_conditional_edges("decide_follow_up", route_after_decision)
    graph.add_edge("create_follow_up", END)
    graph.add_conditional_edges("select_next_primary", route_after_next_primary)
    graph.add_edge("ready_for_report", END)
    return graph.compile()
