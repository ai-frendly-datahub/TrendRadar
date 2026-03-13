"""급상승 키워드 리포트 생성 예시."""

from datetime import datetime
from pathlib import Path

from reporters.spike_reporter import generate_spike_report


def main():
    """급상승 리포트 생성."""
    print("🎯 TrendRadar 급상승 리포트 생성")
    print("=" * 60)

    db_path = Path("data/trendradar.duckdb")

    if not db_path.exists():
        print("❌ 데이터베이스 파일이 없습니다.")
        print("   먼저 데이터를 수집해주세요:")
        print("   python main.py --mode once")
        return

    output_dir = Path("docs/reports")
    output_dir.mkdir(parents=True, exist_ok=True)

    today = datetime.now().date()

    print(f"📅 리포트 날짜: {today}")
    print(f"📁 출력 디렉토리: {output_dir}")
    print(f"💾 데이터베이스: {db_path}")
    print()

    try:
        generate_spike_report(
            target_date=today,
            db_path=db_path,
            output_dir=output_dir,
        )

        report_file = output_dir / f"spike_{today.isoformat()}.html"

        print()
        print("✅ 리포트 생성 완료!")
        print(f"📄 파일: {report_file}")
        print()
        print("💡 브라우저에서 열어보세요:")
        print(f"   start {report_file}")  # Windows
        # print(f"   open {report_file}")  # Mac
        # print(f"   xdg-open {report_file}")  # Linux

    except Exception as e:
        print(f"❌ 리포트 생성 실패: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
