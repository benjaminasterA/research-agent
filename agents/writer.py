"""
Writer Agent
보고서 작성 에이전트
"""

import os
from typing import Dict, Any, List
from datetime import datetime
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


class WriterAgent:
    """보고서 작성 에이전트"""
    
    def __init__(self, model_name: str = None):
        self.llm = ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0.5
        )
        
        self.write_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 전문 리서치 보고서 작성자입니다.
수집된 정보를 바탕으로 체계적이고 읽기 쉬운 보고서를 작성합니다.

보고서 작성 규칙:
1. 명확한 구조: 서론, 본론, 결론
2. 인용 표기: 정보 출처를 [1], [2] 형식으로 표기
3. 객관적 서술: 사실에 기반한 분석
4. 한국어 작성: 자연스러운 한국어 사용
5. Markdown 형식: 제목, 목록, 강조 등 활용"""),
            ("human", """다음 정보를 바탕으로 '{topic}'에 대한 종합 보고서를 작성해주세요.

## 수집된 정보
{gathered_info}

## 출처 목록
{sources}

## 리서치 계획
{research_plan}

---

위 정보를 종합하여 다음 구조로 보고서를 작성해주세요:

1. **제목**: 주제를 명확히 표현
2. **요약** (Executive Summary): 3-4문장으로 핵심 내용 요약
3. **목차**
4. **서론**: 주제 소개 및 중요성
5. **본론**: 핵심 내용을 2-3개 섹션으로 구분하여 상세 설명
6. **결론**: 핵심 인사이트 및 시사점
7. **참고문헌**: 출처 목록

보고서 작성 시 반드시 출처를 인용하세요 (예: [1], [2]).""")
        ])
    
    def write_report(
        self,
        topic: str,
        gathered_info: List[str],
        sources: List[Dict],
        research_plan: str
    ) -> str:
        """
        보고서 작성
        
        Args:
            topic: 연구 주제
            gathered_info: 수집된 정보 목록
            sources: 출처 목록
            research_plan: 리서치 계획
            
        Returns:
            작성된 보고서 (Markdown)
        """
        # 정보 포맷팅
        info_text = "\n\n".join(gathered_info) if gathered_info else "수집된 정보 없음"
        
        # 출처 포맷팅
        sources_text = self._format_sources(sources)
        
        try:
            chain = self.write_prompt | self.llm
            response = chain.invoke({
                "topic": topic,
                "gathered_info": info_text,
                "sources": sources_text,
                "research_plan": research_plan or "계획 없음"
            })
            
            report = response.content
            
            # 메타데이터 추가
            report = self._add_metadata(report, topic)
            
            return report
            
        except Exception as e:
            return self._fallback_report(topic, gathered_info, sources, str(e))
    
    def _format_sources(self, sources: List[Dict]) -> str:
        """출처 목록 포맷팅"""
        if not sources:
            return "출처 없음"
        
        # 중복 제거
        unique_sources = []
        seen_urls = set()
        for s in sources:
            url = s.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(s)
        
        lines = []
        for i, source in enumerate(unique_sources[:20], 1):  # 최대 20개
            title = source.get("title", "제목 없음")
            url = source.get("url", "URL 없음")
            lines.append(f"[{i}] {title}\n    {url}")
        
        return "\n".join(lines)
    
    def _add_metadata(self, report: str, topic: str) -> str:
        """보고서에 메타데이터 추가"""
        today = datetime.now().strftime("%Y년 %m월 %d일")
        
        metadata = f"""---
제목: {topic} 리서치 보고서
작성일: {today}
작성자: AI Research Agent
---

"""
        return metadata + report
    
    def _fallback_report(
        self,
        topic: str,
        gathered_info: List[str],
        sources: List[Dict],
        error: str
    ) -> str:
        """LLM 실패 시 기본 보고서"""
        today = datetime.now().strftime("%Y년 %m월 %d일")
        
        report = f"""---
제목: {topic} 리서치 보고서
작성일: {today}
---

# {topic}

## 요약

이 보고서는 '{topic}'에 대한 웹 검색 결과를 정리한 것입니다.

## 수집된 정보

"""
        for info in gathered_info:
            report += f"{info}\n\n"
        
        report += "\n## 참고문헌\n\n"
        for i, source in enumerate(sources[:10], 1):
            report += f"[{i}] {source.get('title', 'N/A')} - {source.get('url', 'N/A')}\n"
        
        report += f"\n\n---\n*참고: 자동 보고서 생성 중 오류 발생 ({error})*"
        
        return report


def write_report(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph 노드 함수: 보고서 작성
    
    Args:
        state: 현재 상태
        
    Returns:
        업데이트된 상태
    """
    print("\n✍️  보고서 작성 중...")
    
    writer = WriterAgent()
    
    report = writer.write_report(
        topic=state.get("topic", ""),
        gathered_info=state.get("gathered_info", []),
        sources=state.get("sources", []),
        research_plan=state.get("research_plan", "")
    )
    
    print(f"   ✅ 보고서 작성 완료 ({len(report)} 자)")
    
    return {
        "draft_report": report,
        "current_step": "writing_complete"
    }
