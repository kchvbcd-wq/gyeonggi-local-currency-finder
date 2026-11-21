"""경기도 지역화폐 가맹점 CSV의 로딩 결과와 집계만 표시한다."""

from pathlib import Path
import sys

from src.local_currency.loader import CSVLoadError, load_merchant_csv


CSV_PATH = Path(__file__).resolve().parent / "data" / "raw" / "지역화폐가맹점현황.csv"


def main() -> int:
    try:
        merchants = load_merchant_csv(CSV_PATH)
    except (FileNotFoundError, CSVLoadError) as error:
        print(f"로딩 실패. {error}", file=sys.stderr)
        return 1

    rows, columns = merchants.shape
    cities = merchants["시군명"]
    print("로딩 성공")
    print(f"전체 행 수 {rows:,}개")
    print(f"전체 컬럼 수 {columns:,}개")
    print(f"전체 컬럼명 {' · '.join(merchants.columns)}")
    print(f"시군 개수 {cities[cities != ''].nunique():,}개")
    print("휴폐업상태별 기록 수")
    for status, count in merchants["휴폐업상태"].value_counts().items():
        print(f"  {status or '(빈 문자열)'} {count:,}건")
    return 0


if __name__ == "__main__":
    sys.exit(main())
