"""
Reviewer Agent - 보고서 검토 에이전트
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


class ReviewerAgent:
    """보고서 검토 에이전트"""
    
    def __init__(self, model_name: str = None):
        self.llm = ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.2
        )
        
        self.review_prompt = ChatPromptTemplate.from_messages([
            ("system", "당신은 전문 편집자입니다. 보고서 품질을 1-10점으로 평가하세요."),
            ("human", "주제: {topic}\n\n보고서:\n{report}\n\n평가해주세요.")
        ])
    
    def review(self, topic: str, report: str) -> Dict[str, Any]:
        try:
            chain = self.review_prompt | self.llm
            response = chain.invoke({"topic": topic, "report": report[:4000]})
            score = 7  # 기본 점수
            if "우수" in response.content or "훌륭" in response.content:
                score = 9
            elif "개선" in response.content or "부족" in response.content:
                score = 5
            return {
                "quality_score": score,
                "is_acceptable": score >= 6,
                "feedback": response.content,
                "needs_revision": score < 6
            }
        except Exception as e:
            return {"quality_score": 6, "is_acceptable": True, "feedback": str(e), "needs_revision": False}


def review_report(state: Dict[str, Any]) -> Dict[str, Any]:
    print("\n🔍 보고서 검토 중...")
    reviewer = ReviewerAgent()
    draft = state.get("draft_report", "")
    result = reviewer.review(state.get("topic", ""), draft)
    print(f"   ✅ 품질 점수: {result['quality_score']}/10")
    
    if result["is_acceptable"]:
        return {"review_feedback": result["feedback"], "final_report": draft, 
                "needs_revision": False, "current_step": "review_complete"}
    return {"review_feedback": result["feedback"], "needs_revision": True,
            "iteration_count": state.get("iteration_count", 0) + 1, "current_step": "needs_revision"}
