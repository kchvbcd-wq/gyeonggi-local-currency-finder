from unittest.mock import Mock

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

import search_cli
from src.local_currency.search import search_merchants


@pytest.fixture
def merchants():
    return pd.DataFrame(
        {
            "시군명": ["수원시", "수원시", "성남시", "수원시", "수원시", "수원시청"],
            "상호명": ["Bean [Lab].", "bean Roasters", "BEAN Point", "한끼", "해뜰 찻집", "BEAN Annex"],
            "업종명": ["커피[Cafe]전문점", "커피전문점", "커피전문점", "한식 음식점", "커피전문점", "커피전문점"],
            "정제도로명주소": ["샘플로 1", "", "샘플로 3", "샘플로 4", " \t", "샘플로 6"],
            "정제지번주소": [f"대체 지번 {n}" for n in range(1, 7)],
            "휴폐업상태": ["계속사업자", "폐업자", "계속사업자", "휴업자", "", "계속사업자"],
            "사업자등록번호": [f"TEST-BIZ-{n}" for n in range(1, 7)],
            "가맹점번호": [f"TEST-MERCHANT-{n}" for n in range(1, 7)],
        },
        index=[40, 7, 50, 3, 25, 12],
    )


@pytest.fixture
def mock_loader(monkeypatch, merchants):
    loader = Mock(return_value=merchants)
    monkeypatch.setattr(search_cli, "load_merchant_csv", loader)
    return loader


def test_searches_exact_city_and_trims_input(merchants):
    assert search_merchants(merchants, city=" \t수원시 \n").index.tolist() == [40, 7, 3, 25]


def test_searches_name_substring_case_insensitively_in_source_order(merchants):
    result = search_merchants(merchants, name=" bEaN ")

    assert_frame_equal(result, merchants.iloc[[0, 1, 2, 5]])


def test_searches_industry_substring_case_insensitively(merchants):
    assert search_merchants(merchants, industry="커피").index.tolist() == [40, 7, 50, 25, 12]
    assert search_merchants(merchants, industry="cAfE").index.tolist() == [40]


def test_searches_exact_status(merchants):
    assert search_merchants(merchants, status="폐업자").index.tolist() == [7]
    assert search_merchants(merchants, status="폐업").empty


def test_combines_all_filters_with_and(merchants):
    result = search_merchants(
        merchants, city="수원시", name="bean", industry="커피", status="계속사업자"
    )

    assert result.index.tolist() == [40]


@pytest.mark.parametrize(
    ("filters", "expected"),
    [({"name": "[lAb]."}, [40]), ({"industry": "[cAfE]"}, [40]), ({"name": ".*"}, [])],
)
def test_treats_regex_metacharacters_as_literal_characters(merchants, filters, expected):
    assert search_merchants(merchants, **filters).index.tolist() == expected


def test_omits_none_and_blank_conditions(merchants):
    result = search_merchants(merchants, city=None, name="", industry=" \t", status=" ")
    assert_frame_equal(result, merchants)

    result = search_merchants(merchants, city="수원시", name=None, status="")
    assert result.index.tolist() == [40, 7, 3, 25]


def test_returns_empty_dataframe_with_source_columns_when_no_rows_match(merchants):
    result = search_merchants(merchants, city="성남시", industry="한식")

    assert_frame_equal(result, merchants.iloc[:0])


@pytest.mark.parametrize("filters", [{}, {"city": "수원시"}])
def test_search_and_result_edits_leave_source_unchanged(merchants, filters):
    original = merchants.copy()

    result = search_merchants(merchants, **filters)
    result.loc[40, "상호명"] = "변경된 결과"

    assert_frame_equal(merchants, original)


@pytest.mark.parametrize("limit", ["0", "-1", "2.5", "abc"])
def test_cli_rejects_invalid_limit_before_loading(mock_loader, capsys, limit):
    with pytest.raises(SystemExit) as error:
        search_cli.main(["--limit", limit])

    assert error.value.code == 2
    assert "1 이상의 정수" in capsys.readouterr().err
    mock_loader.assert_not_called()


@pytest.mark.parametrize(
    ("args", "status_label", "count"),
    [
        ([], "계속사업자", 3),
        (["--status", " "], "계속사업자", 3),
        (["--status", "all"], "전체", 6),
        (["--status", "휴업자"], "휴업자", 1),
    ],
)
def test_cli_applies_default_all_and_explicit_status(mock_loader, capsys, args, status_label, count):
    assert search_cli.main(args) == 0

    output = capsys.readouterr().out
    assert f"휴폐업상태={status_label}" in output
    assert f"전체 일치 건수 {count}건" in output
    mock_loader.assert_called_once_with(search_cli.CSV_PATH)


def test_cli_displays_only_allowed_columns_and_uses_address_fallback(mock_loader, capsys):
    assert search_cli.main(["--status", "all"]) == 0

    output = capsys.readouterr().out
    assert output.splitlines()[3].split() == ["시군명", "상호명", "업종명", "정제도로명주소", "휴폐업상태"]
    assert "샘플로 1" in output
    assert "대체 지번 1" not in output
    assert "대체 지번 2" in output
    assert "대체 지번 5" in output
    assert "사업자등록번호" not in output
    assert "가맹점번호" not in output
    assert "TEST-BIZ-" not in output
    assert "TEST-MERCHANT-" not in output


def test_cli_reports_total_and_limits_displayed_rows(mock_loader, capsys):
    assert search_cli.main(["--city", " 수원시 ", "--status", "all", "--limit", "1"]) == 0

    output = capsys.readouterr().out
    assert "시군명=수원시" in output
    assert "전체 일치 건수 4건" in output
    assert "출력 건수 1건" in output
    assert "Bean [Lab]." in output
    assert "bean Roasters" not in output
    assert len(output.splitlines()[4:]) == 1


def test_cli_defaults_to_twenty_displayed_rows(mock_loader, capsys, merchants):
    mock_loader.return_value = pd.concat([merchants] * 8)

    assert search_cli.main([]) == 0

    output = capsys.readouterr().out
    assert "전체 일치 건수 24건" in output
    assert "출력 건수 20건" in output
    assert len(output.splitlines()[4:]) == 20


def test_cli_reports_no_matches(mock_loader, capsys):
    assert search_cli.main(["--city", "없는 시군"]) == 0

    output = capsys.readouterr().out
    assert "전체 일치 건수 0건" in output
    assert "출력 건수 0건" in output
    assert "일치하는 가맹점이 없습니다." in output
