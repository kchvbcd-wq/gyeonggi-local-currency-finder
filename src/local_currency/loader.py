"""경기도 지역화폐 가맹점 CSV를 검증하고 읽는다."""

import csv
from pathlib import Path
from typing import TextIO

import pandas as pd


REQUIRED_COLUMNS = (
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


class CSVLoadError(ValueError):
    """가맹점 CSV를 읽거나 검증할 수 없을 때 발생한다."""


def _validate_csv(stream: TextIO) -> None:
    rows = csv.reader(stream, strict=True)
    try:
        header = next((row for row in rows if row), None)
        if header is None:
            raise CSVLoadError("CSV 파일이 비어 있습니다. 컬럼 헤더가 필요합니다.")
        if "" in header or len(set(header)) != len(header):
            raise CSVLoadError("CSV 헤더에 비어 있거나 중복된 컬럼명이 있습니다.")

        missing = [column for column in REQUIRED_COLUMNS if column not in header]
        if missing:
            raise CSVLoadError(f"CSV 필수 컬럼이 누락되었습니다. {', '.join(missing)}")

        # Pandas는 필드가 부족한 레코드를 빈 값으로 채울 수 있으므로 미리 검사한다.
        width = len(header)
        for row in rows:
            if row and len(row) != width:
                raise CSVLoadError(
                    f"CSV {rows.line_num}번째 줄에서 끝나는 레코드의 필드 수가 "
                    f"{len(row)}개입니다. 헤더와 같은 {width}개가 필요합니다."
                )
    except csv.Error:
        raise CSVLoadError(
            f"CSV 형식 오류가 발생했습니다. {rows.line_num}번째 줄 부근의 "
            "따옴표와 쉼표를 확인하세요."
        ) from None


def load_merchant_csv(path: str | Path) -> pd.DataFrame:
    """CP949 CSV의 모든 데이터 값을 문자열로 읽어 원본 순서로 반환한다.

    유효한 헤더만 있는 CSV는 빈 DataFrame으로 반환한다.
    파일이 없으면 FileNotFoundError, 읽기 또는 검증 실패 시 CSVLoadError가 발생한다.
    """
    csv_path = Path(path)
    try:
        with csv_path.open(encoding="cp949", newline="") as stream:
            _validate_csv(stream)
            stream.seek(0)
            return pd.read_csv(
                stream,
                engine="python",
                dtype=str,
                keep_default_na=False,
                skip_blank_lines=True,
                on_bad_lines="error",
            )
    except FileNotFoundError:
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다. 경로: {csv_path}") from None
    except UnicodeDecodeError:
        raise CSVLoadError("CSV를 CP949로 읽을 수 없습니다. 파일 인코딩을 확인하세요.") from None
    except pd.errors.ParserError:
        raise CSVLoadError("CSV 형식 오류가 발생했습니다. 헤더와 필드 구성을 확인하세요.") from None
    except OSError:
        raise CSVLoadError(f"CSV 파일을 열 수 없습니다. 경로와 읽기 권한을 확인하세요. {csv_path}") from None
