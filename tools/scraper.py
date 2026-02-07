"""
Web Scraper Tool
웹 페이지 스크래핑 도구
"""

import asyncio
from typing import Optional, Dict, Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup


class WebScraper:
    """웹 페이지 스크래퍼"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
    
    def scrape(self, url: str) -> Dict[str, Any]:
        """
        URL에서 텍스트 콘텐츠 추출
        
        Args:
            url: 스크래핑할 URL
            
        Returns:
            추출된 콘텐츠 딕셔너리
        """
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                # 불필요한 요소 제거
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                
                # 메타 정보 추출
                title = soup.title.string if soup.title else ""
                meta_desc = ""
                meta_tag = soup.find("meta", attrs={"name": "description"})
                if meta_tag:
                    meta_desc = meta_tag.get("content", "")
                
                # 본문 텍스트 추출
                # article 또는 main 태그 우선
                main_content = soup.find("article") or soup.find("main") or soup.body
                
                if main_content:
                    # 문단별로 텍스트 추출
                    paragraphs = main_content.find_all(["p", "h1", "h2", "h3", "h4", "li"])
                    text_parts = [p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)]
                    content = "\n\n".join(text_parts)
                else:
                    content = soup.get_text(separator="\n", strip=True)
                
                # 텍스트 정리
                content = self._clean_text(content)
                
                return {
                    "url": url,
                    "title": title.strip() if title else "",
                    "description": meta_desc,
                    "content": content[:10000],  # 최대 10000자
                    "domain": urlparse(url).netloc,
                    "success": True
                }
                
        except httpx.HTTPError as e:
            return {
                "url": url,
                "error": f"HTTP 오류: {str(e)}",
                "success": False
            }
        except Exception as e:
            return {
                "url": url,
                "error": f"스크래핑 오류: {str(e)}",
                "success": False
            }
    
    async def scrape_async(self, url: str) -> Dict[str, Any]:
        """비동기 스크래핑"""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=self.headers, follow_redirects=True)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, "html.parser")
                
                for tag in soup(["script", "style", "nav", "footer"]):
                    tag.decompose()
                
                title = soup.title.string if soup.title else ""
                main_content = soup.find("article") or soup.find("main") or soup.body
                
                if main_content:
                    content = main_content.get_text(separator="\n", strip=True)
                else:
                    content = soup.get_text(separator="\n", strip=True)
                
                return {
                    "url": url,
                    "title": title.strip() if title else "",
                    "content": self._clean_text(content)[:10000],
                    "success": True
                }
                
        except Exception as e:
            return {
                "url": url,
                "error": str(e),
                "success": False
            }
    
    async def scrape_multiple(self, urls: list) -> list:
        """여러 URL 동시 스크래핑"""
        tasks = [self.scrape_async(url) for url in urls]
        return await asyncio.gather(*tasks)
    
    def _clean_text(self, text: str) -> str:
        """텍스트 정리"""
        import re
        # 여러 줄바꿈을 2개로 통일
        text = re.sub(r'\n{3,}', '\n\n', text)
        # 여러 공백을 1개로 통일
        text = re.sub(r' {2,}', ' ', text)
        return text.strip()


def scrape_url(url: str) -> Dict[str, Any]:
    """URL 스크래핑 헬퍼 함수"""
    scraper = WebScraper()
    return scraper.scrape(url)


def scrape_urls(urls: list) -> list:
    """여러 URL 스크래핑 헬퍼 함수"""
    scraper = WebScraper()
    return asyncio.run(scraper.scrape_multiple(urls))
