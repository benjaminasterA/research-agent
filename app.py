"""
자율 리서치 에이전트 - CLI 버전
LangGraph를 활용한 멀티에이전트 리서치 시스템

사용법:
    python app.py "연구 주제"
    python app.py "AI 기술 트렌드" --output report.md
"""

import sys
import os
import argparse
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트를 path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()


def check_api_keys():
    """API 키 확인"""
    openai_key = os.getenv("OPENAI_API_KEY", "")
    tavily_key = os.getenv("TAVILY_API_KEY", "")
    
    if not openai_key or openai_key.startswith("sk-your"):
        print("❌ OpenAI API 키가 설정되지 않았습니다.")
        print("   .env 파일에 OPENAI_API_KEY를 설정해주세요.")
        return False
    
    if not tavily_key or tavily_key.startswith("tvly-your"):
        print("⚠️  Tavily API 키가 없습니다. Mock 검색을 사용합니다.")
        print("   실제 웹 검색을 위해 https://tavily.com 에서 API 키를 발급받으세요.")
    
    return True


def save_report(report: str, topic: str, output_path: str = None):
    """보고서 저장"""
    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    
    if output_path:
        filepath = Path(output_path)
    else:
        # 파일명 생성 (제목 기반)
        safe_topic = "".join(c if c.isalnum() or c in " -_" else "" for c in topic)[:30]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = reports_dir / f"{safe_topic}_{timestamp}.md"
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n📁 보고서 저장됨: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(
        description="자율 리서치 에이전트 - AI가 웹을 검색하고 보고서를 작성합니다."
    )
    parser.add_argument(
        "topic",
        nargs="?",
        help="리서치할 주제"
    )
    parser.add_argument(
        "--output", "-o",
        help="보고서 저장 경로"
    )
    parser.add_argument(
        "--max-iterations", "-m",
        type=int,
        default=2,
        help="최대 수정 반복 횟수 (기본: 2)"
    )
    
    args = parser.parse_args()
    
    # 주제 입력
    if args.topic:
        topic = args.topic
    else:
        print("\n🔬 자율 리서치 에이전트")
        print("=" * 40)
        topic = input("연구할 주제를 입력하세요: ").strip()
        if not topic:
            print("주제가 입력되지 않았습니다.")
            return
    
    # API 키 확인
    if not check_api_keys():
        return
    
    print(f"\n📚 주제: {topic}")
    print(f"🔄 최대 반복: {args.max_iterations}회")
    
    try:
        # 리서치 실행
        from graph.workflow import run_research
        
        result = run_research(topic, max_iterations=args.max_iterations)
        
        # 결과 출력
        final_report = result.get("final_report") or result.get("draft_report", "")
        
        if final_report:
            print("\n" + "=" * 50)
            print("📄 최종 보고서")
            print("=" * 50)
            print(final_report[:2000])
            if len(final_report) > 2000:
                print(f"\n... (총 {len(final_report)} 자)")
            
            # 저장
            save_report(final_report, topic, args.output)
        else:
            print("\n❌ 보고서 생성에 실패했습니다.")
            if result.get("errors"):
                print("오류:", result["errors"])
        
        # 검토 피드백 출력
        if result.get("review_feedback"):
            print("\n📋 검토 피드백:")
            print(result["review_feedback"][:500])
            
    except ImportError as e:
        print(f"\n❌ 모듈 import 오류: {e}")
        print("   pip install -r requirements.txt 를 실행해주세요.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
