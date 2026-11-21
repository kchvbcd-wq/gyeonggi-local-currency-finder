import csv

import pytest

from src.local_currency.loader import CSVLoadError, load_merchant_csv


COLUMNS = (
    "시군명",
    "상호명",
    "업종명",
    "정제도로명주소",
    "정제지번주소",
    "정제우편번호",
    "정제WGS84위도",
    "정제WGS84경도",
    "사업자등록번호",
    "업종코드",
    "가맹점번호",
    "휴폐업상태",
    "휴폐업상태코드",
    "폐업일자",
)
RECORD = (
    "수원시",
    '테스트, "한글" 가게',
    "음식점",
    "시험로 1\n1층",
    "",
    "00123",
    "37.1000",
    "127.0000",
    "0000000000",
    "NA",
    "0007",
    "계속사업자",
    "01",
    "",
)


@pytest.fixture
def csv_path(tmp_path):
    return tmp_path / "가맹점.csv"


def write_csv(path, *records):
    with path.open("w", encoding="cp949", newline="") as stream:
        csv.writer(stream).writerows(records)


def test_loads_cp949_and_preserves_every_value_as_text(csv_path):
    write_csv(csv_path, COLUMNS, RECORD)

    merchants = load_merchant_csv(csv_path)

    assert tuple(merchants.columns) == COLUMNS
    assert merchants.shape == (1, len(COLUMNS))
    values = tuple(merchants.iloc[0])
    assert values == RECORD
    assert all(isinstance(value, str) for value in values)


def test_skips_trailing_blank_line_but_keeps_record_with_empty_fields(csv_path):
    empty_values = ("",) * len(COLUMNS)
    write_csv(csv_path, COLUMNS, RECORD, empty_values, ())

    merchants = load_merchant_csv(csv_path)

    assert list(merchants.itertuples(index=False, name=None)) == [RECORD, empty_values]


def test_preserves_row_order_and_all_columns_in_source_order(csv_path):
    columns = ("추가 컬럼", *reversed(COLUMNS))
    first = ("첫 번째", *reversed(RECORD))
    second = ("두 번째", *reversed(RECORD))
    write_csv(csv_path, columns, second, first, second)

    merchants = load_merchant_csv(str(csv_path))

    assert tuple(merchants.columns) == columns
    assert list(merchants.itertuples(index=False, name=None)) == [second, first, second]


def test_rejects_missing_required_column(csv_path):
    write_csv(csv_path, COLUMNS[:-1], RECORD[:-1])

    with pytest.raises(CSVLoadError, match="필수 컬럼.*폐업일자"):
        load_merchant_csv(csv_path)


def test_reports_missing_file(csv_path):
    with pytest.raises(FileNotFoundError, match="CSV 파일을 찾을 수 없습니다") as error:
        load_merchant_csv(csv_path)

    assert csv_path.name in str(error.value)


@pytest.mark.parametrize("contents", [b"", b"\r\n\r\n"])
def test_rejects_empty_file(csv_path, contents):
    csv_path.write_bytes(contents)

    with pytest.raises(CSVLoadError, match="CSV 파일이 비어 있습니다"):
        load_merchant_csv(csv_path)


def test_returns_empty_dataframe_for_valid_header_only(csv_path):
    write_csv(csv_path, COLUMNS)

    merchants = load_merchant_csv(csv_path)

    assert merchants.empty
    assert tuple(merchants.columns) == COLUMNS


@pytest.mark.parametrize("record", [RECORD[:-1], (*RECORD, "잉여"), (" ",)])
def test_rejects_wrong_field_count(csv_path, record):
    write_csv(csv_path, COLUMNS, record, RECORD)

    with pytest.raises(CSVLoadError, match=r"CSV \d+번째 줄.*필드 수"):
        load_merchant_csv(csv_path)


def test_rejects_unclosed_quote(csv_path):
    write_csv(csv_path, COLUMNS)
    with csv_path.open("a", encoding="cp949") as stream:
        stream.write('수원시,"닫히지 않은 따옴표')

    with pytest.raises(CSVLoadError, match="CSV 형식 오류.*2번째 줄"):
        load_merchant_csv(csv_path)


@pytest.mark.parametrize("column", ["", "시군명"])
def test_rejects_unnamed_or_duplicate_column(csv_path, column):
    write_csv(csv_path, (*COLUMNS, column))

    with pytest.raises(CSVLoadError, match="비어 있거나 중복된 컬럼명"):
        load_merchant_csv(csv_path)


def test_reports_cp949_decoding_error(csv_path):
    write_csv(csv_path, COLUMNS, RECORD)
    with csv_path.open("ab") as stream:
        stream.write(b"\xff\n")

    with pytest.raises(CSVLoadError, match="CP949.*인코딩"):
        load_merchant_csv(csv_path)
