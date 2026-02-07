"""
LangGraph Workflow - 리서치 에이전트 워크플로우
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from .state import ResearchState, create_initial_state
from agents.planner import plan_research
from agents.researcher import execute_research
from agents.writer import write_report
from agents.reviewer import review_report


def should_continue_research(state: ResearchState) -> Literal["write", "end"]:
    """검색 결과가 충분한지 확인"""
    if len(state.get("search_results", [])) >= 3:
        return "write"
    return "end"


def should_revise(state: ResearchState) -> Literal["revise", "end"]:
    """수정이 필요한지 확인"""
    if state.get("needs_revision", False):
        if state.get("iteration_count", 0) < state.get("max_iterations", 3):
            return "revise"
    return "end"


def create_research_graph() -> StateGraph:
    """리서치 워크플로우 그래프 생성"""
    
    # 그래프 생성
    workflow = StateGraph(ResearchState)
    
    # 노드 추가
    workflow.add_node("plan", plan_research)
    workflow.add_node("research", execute_research)
    workflow.add_node("write", write_report)
    workflow.add_node("review", review_report)
    
    # 엣지 연결
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "research")
    workflow.add_edge("research", "write")
    workflow.add_edge("write", "review")
    
    # 조건부 엣지
    workflow.add_conditional_edges(
        "review",
        should_revise,
        {"revise": "write", "end": END}
    )
    
    return workflow.compile()


def run_research(topic: str, max_iterations: int = 3) -> dict:
    """리서치 실행"""
    print(f"\n{'='*50}")
    print(f"🔬 리서치 시작: {topic}")
    print(f"{'='*50}")
    
    graph = create_research_graph()
    initial_state = create_initial_state(topic, max_iterations)
    
    final_state = graph.invoke(initial_state)
    
    print(f"\n{'='*50}")
    print("✅ 리서치 완료!")
    print(f"{'='*50}")
    
    return final_state
