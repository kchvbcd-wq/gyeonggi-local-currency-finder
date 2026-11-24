"""경기도 지역화폐 가맹점을 터미널에서 검색한다."""

import argparse
from collections.abc import Sequence
import sys

from main import CSV_PATH
from src.local_currency.loader import CSVLoadError, load_merchant_csv
from src.local_currency.search import search_merchants


DEFAULT_STATUS = "계속사업자"
DISPLAY_COLUMNS = ["시군명", "상호명", "업종명", "정제도로명주소", "휴폐업상태"]


def _positive_limit(value: str) -> int:
    try:
        limit = int(value)
        if limit > 0:
            return limit
    except ValueError:
        pass
    raise argparse.ArgumentTypeError("출력 제한에는 1 이상의 정수를 입력하세요.")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="경기도 지역화폐 가맹점 검색")
    parser.add_argument("--city", type=str.strip, help="시군명 정확히 일치")
    parser.add_argument("--name", type=str.strip, help="상호명 부분 검색")
    parser.add_argument("--industry", type=str.strip, help="업종명 부분 검색")
    parser.add_argument("--status", type=str.strip, help=f"영업상태 검색 (기본 {DEFAULT_STATUS}, 전체 all)")
    parser.add_argument("--limit", type=_positive_limit, default=20, help="최대 출력 건수 (기본 20)")
    args = parser.parse_args(argv)

    status = None if args.status == "all" else args.status or DEFAULT_STATUS
    try:
        merchants = load_merchant_csv(CSV_PATH)
    except (FileNotFoundError, CSVLoadError) as error:
        print(f"로딩 실패. {error}", file=sys.stderr)
        return 1

    matches = search_merchants(
        merchants, city=args.city, name=args.name, industry=args.industry, status=status
    )
    print(
        f"검색 조건  시군명={args.city or '전체'} · 상호명={args.name or '전체'} · "
        f"업종명={args.industry or '전체'} · 휴폐업상태={status or '전체'}"
    )
    print(f"전체 일치 건수 {len(matches):,}건")
    if matches.empty:
        print("출력 건수 0건")
        print("일치하는 가맹점이 없습니다.")
        return 0

    page = matches.iloc[:args.limit]
    display = page.loc[:, DISPLAY_COLUMNS]
    road_address = display["정제도로명주소"]
    has_road_address = road_address.fillna("").str.strip().ne("")
    display["정제도로명주소"] = road_address.where(has_road_address, page["정제지번주소"])
    print(f"출력 건수 {len(display):,}건")
    print(display.to_string(index=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
