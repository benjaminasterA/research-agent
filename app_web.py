import streamlit as st
import os
import sys
import time
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

# API 키 확인 함수
def check_api_keys():
    openai_key = os.getenv("OPENAI_API_KEY", "")
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    
    if not openai_key or openai_key.startswith("sk-your"):
        st.error("❌ OpenAI API 키가 설정되지 않았습니다. .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        return False
    
    if not tavily_key or tavily_key.startswith("tvly-your"):
        st.warning("⚠️ Tavily API 키가 없습니다. Mock 검색을 사용합니다. 실제 웹 검색을 위해 https://tavily.com 에서 API 키를 발급받으세요.")
    
    return True

def save_report(report: str, topic: str):
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    safe_topic = "".join(c if c.isalnum() or c in " -_" else "" for c in topic)[:30]
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = reports_dir / f"{safe_topic}_{timestamp}.md"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    
    return filepath

def main():
    st.set_page_config(page_title="자율 리서치 에이전트", page_icon="🔍", layout="wide")
    
    st.title("🔍 자율 리서치 에이전트")
    st.markdown("LangGraph와 Multi-Agent 시스템을 활용한 자동 리서치 및 보고서 생성 도구입니다.")
    
    if not check_api_keys():
        st.stop()
    
    with st.sidebar:
        st.header("설정")
        max_iterations = st.slider("최대 수정 반복 횟수", min_value=1, max_value=5, value=2)
        
    topic = st.text_input("연구할 주제를 입력하세요", placeholder="예: 2025년 AI 기술 트렌드")
    
    if st.button("리서치 시작", type="primary"):
        if not topic:
            st.warning("주제를 입력해주세요.")
            return
            
        status_container = st.container()
        result_container = st.container()
        
        with status_container:
            st.info(f"📚 주제: {topic} (최대 {max_iterations}회 반복)")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            status_text.text("🚀 리서치 에이전트 시작...")
            progress_bar.progress(10)
            
            try:
                # 리서치 실행
                from graph.workflow import run_research
                
                # 실행 로그를 화면에 표시하기 위해 stdout 캡처는 복잡할 수 있으므로
                # 간단히 실행 상태만 표시
                with st.spinner('에이전트들이 열심히 조사하고 보고서를 작성 중입니다...'):
                    result = run_research(topic, max_iterations=max_iterations)
                
                progress_bar.progress(100)
                status_text.text("✅ 리서치 완료!")
                
                final_report = result.get("final_report") or result.get("draft_report", "")
                
                with result_container:
                    if final_report:
                        st.subheader("📄 최종 보고서")
                        st.markdown(final_report)
                        
                        # 파일 저장
                        saved_path = save_report(final_report, topic)
                        st.success(f"보고서가 로컬에 저장되었습니다: {saved_path}")
                        
                        # 다운로드 버튼
                        st.download_button(
                            label="보고서 다운로드 (Markdown)",
                            data=final_report,
                            file_name=os.path.basename(saved_path),
                            mime="text/markdown"
                        )
                    else:
                        st.error("보고서 생성에 실패했습니다.")
                        if result.get("errors"):
                            st.error(f"오류: {result['errors']}")
                            
                    if result.get("review_feedback"):
                        with st.expander("검토 피드백 보기"):
                            st.text(result["review_feedback"])
                            
            except ImportError as e:
                st.error(f"❌ 모듈 import 오류: {e}")
                st.info("pip install -r requirements.txt 를 실행해주세요.")
            except Exception as e:
                st.error(f"❌ 오류 발생: {e}")
                import traceback
                st.code(traceback.format_exc())

if __name__ == "__main__":
    main()