"""로드된 경기도 지역화폐 가맹점 DataFrame을 검색한다."""

import pandas as pd


def search_merchants(
    merchants: pd.DataFrame,
    *,
    city: str | None = None,
    name: str | None = None,
    industry: str | None = None,
    status: str | None = None,
) -> pd.DataFrame:
    """지정한 조건을 모두 만족하는 행을 원본 순서로 반환한다.

    입력값의 앞뒤 공백을 제거하고 None과 빈 조건을 생략한다.
    시군명과 휴폐업상태는 정확히 일치해야 하며, 상호명과 업종명은
    대소문자를 구분하지 않고 입력한 문자열을 그대로 부분 검색한다.
    """
    city = (city or "").strip()
    name = (name or "").strip()
    industry = (industry or "").strip()
    status = (status or "").strip()
    if not any((city, name, industry, status)):
        return merchants.copy(deep=False)

    matches = pd.Series(True, index=merchants.index)
    if city:
        matches &= merchants["시군명"].eq(city)
    if name:
        matches &= merchants["상호명"].str.contains(name, case=False, regex=False, na=False)
    if industry:
        matches &= merchants["업종명"].str.contains(industry, case=False, regex=False, na=False)
    if status:
        matches &= merchants["휴폐업상태"].eq(status)
    return merchants.loc[matches]
