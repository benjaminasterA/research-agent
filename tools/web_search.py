"""
Web Search Tool
Tavily API를 활용한 웹 검색 도구
"""

import os
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()


class TavilySearchTool:
    """Tavily 웹 검색 도구"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self._client = None
        
    @property
    def client(self):
        """Lazy initialization of Tavily client"""
        if self._client is None:
            if not self.api_key or self.api_key.startswith("tvly-your"):
                raise ValueError(
                    "Tavily API 키가 설정되지 않았습니다. "
                    ".env 파일에 TAVILY_API_KEY를 설정하거나 "
                    "https://tavily.com 에서 무료 API 키를 발급받으세요."
                )
            try:
                from tavily import TavilyClient
                self._client = TavilyClient(api_key=self.api_key)
            except ImportError:
                raise ImportError("tavily-python 패키지를 설치해주세요: pip install tavily-python")
        return self._client
    
    def search(
        self,
        query: str,
        max_results: int = 5,
        search_depth: str = "basic",
        include_domains: List[str] = None,
        exclude_domains: List[str] = None
    ) -> List[Dict[str, Any]]:
        """
        웹 검색 실행
        
        Args:
            query: 검색 쿼리
            max_results: 최대 결과 수
            search_depth: 검색 깊이 ("basic" or "advanced")
            include_domains: 포함할 도메인 목록
            exclude_domains: 제외할 도메인 목록
            
        Returns:
            검색 결과 리스트
        """
        try:
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth=search_depth,
                include_domains=include_domains or [],
                exclude_domains=exclude_domains or []
            )
            
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0)
                })
            
            return results
            
        except Exception as e:
            print(f"검색 오류: {e}")
            return []
    
    def get_search_context(
        self,
        query: str,
        max_results: int = 5
    ) -> str:
        """검색 결과를 컨텍스트 문자열로 반환"""
        try:
            response = self.client.get_search_context(
                query=query,
                max_results=max_results
            )
            return response
        except Exception as e:
            print(f"컨텍스트 검색 오류: {e}")
            return ""


class MockSearchTool:
    """Tavily API 키가 없을 때 사용하는 Mock 검색 도구"""
    
    def search(self, query: str, max_results: int = 5, **kwargs) -> List[Dict[str, Any]]:
        """Mock 검색 결과 반환"""
        return [
            {
                "title": f"[Mock] {query}에 대한 검색 결과 1",
                "url": "https://example.com/result1",
                "content": f"이것은 '{query}'에 대한 모의 검색 결과입니다. "
                          "실제 검색 결과를 얻으려면 Tavily API 키를 설정하세요.",
                "score": 0.9
            },
            {
                "title": f"[Mock] {query} 관련 정보",
                "url": "https://example.com/result2",
                "content": f"'{query}'와 관련된 추가 정보입니다. "
                          "https://tavily.com 에서 무료 API 키를 발급받을 수 있습니다.",
                "score": 0.8
            }
        ]


def search_web(
    query: str,
    max_results: int = 5,
    use_mock: bool = False
) -> List[Dict[str, Any]]:
    """
    웹 검색 헬퍼 함수
    
    Args:
        query: 검색 쿼리
        max_results: 최대 결과 수
        use_mock: Mock 검색 사용 여부
        
    Returns:
        검색 결과 리스트
    """
    if use_mock:
        tool = MockSearchTool()
    else:
        try:
            tool = TavilySearchTool()
            # API 키 검증을 위해 client 속성 접근
            _ = tool.client
        except (ValueError, ImportError):
            print("⚠️  Tavily API 키가 없거나 패키지가 없어 Mock 검색을 사용합니다.")
            tool = MockSearchTool()
    
    return tool.search(query, max_results=max_results)


# LangChain Tool 형태로 정의
def create_search_tool():
    """LangChain Tool 형태의 검색 도구 생성"""
    from langchain.tools import Tool
    
    def _search(query: str) -> str:
        results = search_web(query, max_results=5)
        if not results:
            return "검색 결과가 없습니다."
        
        output = []
        for i, r in enumerate(results, 1):
            output.append(f"{i}. {r['title']}")
            output.append(f"   URL: {r['url']}")
            output.append(f"   내용: {r['content'][:200]}...")
            output.append("")
        
        return "\n".join(output)
    
    return Tool(
        name="web_search",
        description="웹에서 정보를 검색합니다. 검색어를 입력하면 관련 웹 페이지 결과를 반환합니다.",
        func=_search
    )
