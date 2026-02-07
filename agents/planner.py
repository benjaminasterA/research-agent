"""
Planner Agent
리서치 계획 수립 및 검색 쿼리 생성 에이전트
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
# (langchain_core.prompts에서 필요한 템플릿 도구 임포트함)
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

# (langchain_core.output_parsers에서 파서를 임포트함 - 이 줄이 꼭 필요함!)
from langchain_core.output_parsers import PydanticOutputParser

# (데이터 구조 정의를 위해 pydantic에서 BaseModel 등을 임포트함)
from pydantic import BaseModel, Field

load_dotenv()


class ResearchPlan(BaseModel):
    """리서치 계획 출력 스키마"""
    topic_summary: str = Field(description="주제 요약")
    key_aspects: List[str] = Field(description="조사할 핵심 측면들")
    search_queries: List[str] = Field(description="검색할 쿼리 목록 (5-7개)")
    expected_sections: List[str] = Field(description="예상되는 보고서 섹션")


class PlannerAgent:
    """리서치 계획 수립 에이전트"""
    
    def __init__(self, model_name: str = None):
        self.llm = ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.3
        )
        self.parser = PydanticOutputParser(pydantic_object=ResearchPlan)
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 전문 리서치 계획 수립자입니다.
주어진 주제에 대해 체계적인 연구 계획을 수립합니다.

다음을 수행하세요:
1. 주제를 분석하고 핵심 측면을 파악
2. 효과적인 검색 쿼리 5-7개 생성
3. 보고서에 포함될 섹션 구조 설계

{format_instructions}"""),
            ("human", """다음 주제에 대한 리서치 계획을 수립해주세요:

주제: {topic}

참고사항:
- 검색 쿼리는 구체적이고 다양한 관점을 포함해야 합니다
- 한국어와 영어 쿼리를 적절히 혼합하세요
- 최신 정보를 얻을 수 있는 쿼리를 포함하세요""")
        ])
    
    def create_plan(self, topic: str) -> Dict[str, Any]:
        """
        리서치 계획 생성
        
        Args:
            topic: 연구 주제
            
        Returns:
            리서치 계획 딕셔너리
        """
        try:
            chain = self.prompt | self.llm | self.parser
            
            result = chain.invoke({
                "topic": topic,
                "format_instructions": self.parser.get_format_instructions()
            })
            
            return {
                "success": True,
                "topic_summary": result.topic_summary,
                "key_aspects": result.key_aspects,
                "search_queries": result.search_queries,
                "expected_sections": result.expected_sections
            }
            
        except Exception as e:
            # 파싱 실패 시 기본 계획 생성
            return self._fallback_plan(topic, str(e))
    
    def _fallback_plan(self, topic: str, error: str) -> Dict[str, Any]:
        """파싱 실패 시 기본 계획"""
        return {
            "success": True,
            "topic_summary": f"{topic}에 대한 종합적인 연구",
            "key_aspects": [
                "개요 및 정의",
                "현재 동향",
                "주요 사례",
                "미래 전망"
            ],
            "search_queries": [
                topic,
                f"{topic} 최신 동향 2025",
                f"{topic} 사례 분석",
                f"{topic} 전망",
                f"what is {topic}",
                f"{topic} trends 2025"
            ],
            "expected_sections": [
                "개요",
                "주요 내용",
                "사례 분석",
                "결론 및 전망"
            ],
            "note": f"기본 계획 사용 (파싱 오류: {error})"
        }


def plan_research(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph 노드 함수: 리서치 계획 수립
    
    Args:
        state: 현재 상태
        
    Returns:
        업데이트된 상태
    """
    print("\n📋 리서치 계획 수립 중...")
    
    planner = PlannerAgent()
    plan = planner.create_plan(state["topic"])
    
    print(f"   ✅ 검색 쿼리 {len(plan['search_queries'])}개 생성됨")
    
    # 계획 요약 출력
    plan_text = f"""
## 리서치 계획

**주제 요약**: {plan['topic_summary']}

**핵심 측면**:
{chr(10).join(f'- {aspect}' for aspect in plan['key_aspects'])}

**검색 쿼리**:
{chr(10).join(f'{i+1}. {q}' for i, q in enumerate(plan['search_queries']))}

**예상 섹션**:
{chr(10).join(f'- {section}' for section in plan['expected_sections'])}
"""
    
    return {
        "research_plan": plan_text,
        "search_queries": plan["search_queries"],
        "current_step": "planning_complete"
    }
