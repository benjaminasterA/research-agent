"""
Research Agent State Definition
LangGraph 상태 관리를 위한 타입 정의
"""

from typing import TypedDict, List, Optional, Annotated
from operator import add


class SearchResult(TypedDict):
    """검색 결과 타입"""
    title: str
    url: str
    content: str
    score: float


class ResearchState(TypedDict):
    """
    리서치 에이전트 상태 정의
    
    LangGraph에서 노드 간 데이터 전달에 사용됨
    """
    # 사용자 입력
    topic: str
    
    # 계획 단계
    research_plan: Optional[str]
    search_queries: Annotated[List[str], add]
    
    # 검색 단계
    search_results: Annotated[List[SearchResult], add]
    gathered_info: Annotated[List[str], add]
    sources: Annotated[List[dict], add]
    
    # 작성 단계
    draft_report: Optional[str]
    final_report: Optional[str]
    
    # 검토 단계
    review_feedback: Optional[str]
    needs_revision: bool
    
    # 메타데이터
    iteration_count: int
    max_iterations: int
    current_step: str
    errors: Annotated[List[str], add]


def create_initial_state(topic: str, max_iterations: int = 3) -> ResearchState:
    """초기 상태 생성"""
    return ResearchState(
        topic=topic,
        research_plan=None,
        search_queries=[],
        search_results=[],
        gathered_info=[],
        sources=[],
        draft_report=None,
        final_report=None,
        review_feedback=None,
        needs_revision=False,
        iteration_count=0,
        max_iterations=max_iterations,
        current_step="start",
        errors=[]
    )
