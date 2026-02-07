"""
Researcher Agent
웹 검색 및 정보 수집 에이전트
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.web_search import search_web

load_dotenv()


class ResearcherAgent:
    """웹 검색 및 정보 수집 에이전트"""
    
    def __init__(self, model_name: str = None):
        self.llm = ChatOpenAI(
            model=model_name or os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            temperature=0
        )
        
        self.summary_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 정보 분석 전문가입니다.
검색 결과에서 핵심 정보를 추출하고 요약합니다.
항상 출처 URL을 함께 기록하세요."""),
            ("human", """다음 검색 결과에서 '{query}'에 관한 핵심 정보를 추출해주세요:

{search_results}

요약 형식:
- 핵심 포인트를 bullet point로 정리
- 각 포인트 뒤에 [출처: URL] 형식으로 출처 표기
- 최대 5개 포인트로 요약""")
        ])
    
    def search_and_collect(
        self,
        queries: List[str],
        max_results_per_query: int = 3
    ) -> Dict[str, Any]:
        """
        검색 실행 및 정보 수집
        
        Args:
            queries: 검색 쿼리 목록
            max_results_per_query: 쿼리당 최대 결과 수
            
        Returns:
            수집된 정보 딕셔너리
        """
        all_results = []
        all_sources = []
        gathered_info = []
        
        for query in queries:
            print(f"   🔍 검색 중: {query}")
            
            try:
                results = search_web(query, max_results=max_results_per_query)
                
                for result in results:
                    all_results.append(result)
                    all_sources.append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "query": query
                    })
                
                # 검색 결과 요약
                if results:
                    summary = self._summarize_results(query, results)
                    gathered_info.append(summary)
                    
            except Exception as e:
                print(f"   ⚠️  검색 오류 ({query}): {e}")
        
        return {
            "search_results": all_results,
            "sources": all_sources,
            "gathered_info": gathered_info
        }
    
    def _summarize_results(self, query: str, results: List[Dict]) -> str:
        """검색 결과 요약"""
        # 검색 결과를 텍스트로 변환
        results_text = ""
        for i, r in enumerate(results, 1):
            results_text += f"\n[{i}] {r.get('title', 'No title')}\n"
            results_text += f"URL: {r.get('url', 'No URL')}\n"
            results_text += f"내용: {r.get('content', 'No content')[:500]}\n"
        
        try:
            chain = self.summary_prompt | self.llm
            response = chain.invoke({
                "query": query,
                "search_results": results_text
            })
            return f"### {query}\n\n{response.content}"
        except Exception as e:
            # LLM 호출 실패 시 기본 요약
            return f"### {query}\n\n" + "\n".join(
                f"- {r.get('title', 'N/A')} [출처: {r.get('url', 'N/A')}]"
                for r in results[:3]
            )


def execute_research(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph 노드 함수: 리서치 실행
    
    Args:
        state: 현재 상태
        
    Returns:
        업데이트된 상태
    """
    print("\n🔎 리서치 실행 중...")
    
    researcher = ResearcherAgent()
    queries = state.get("search_queries", [])
    
    if not queries:
        return {
            "errors": ["검색 쿼리가 없습니다."],
            "current_step": "research_failed"
        }
    
    results = researcher.search_and_collect(queries)
    
    print(f"   ✅ {len(results['search_results'])}개 결과 수집됨")
    print(f"   📚 {len(results['sources'])}개 출처 기록됨")
    
    return {
        "search_results": results["search_results"],
        "sources": results["sources"],
        "gathered_info": results["gathered_info"],
        "current_step": "research_complete"
    }
