# 경기도 지역화폐 가맹점 찾기

경기도 지역화폐 가맹점을 시군, 업종, 상호 등으로 검색하는 웹 앱을 만들기 위한 프로젝트입니다. 현재는 CSV 로더와 터미널 집계·검색 프로그램을 제공합니다.

## 데이터 출처와 배치

경기도가 경기데이터드림에서 제공하는 [지역화폐 가맹점 현황](https://data.gg.go.kr/portal/data/service/selectServicePage.do?infId=3NPA52LBMO36CQEQ1GMY28894927&infSeq=1)을 사용합니다.

1. 데이터셋 상세 화면에서 전체 데이터를 CSV 형식으로 내려받습니다.
2. 프로젝트 루트 기준 `data/raw/지역화폐가맹점현황.csv` 위치에 파일을 둡니다. 로더는 CP949 인코딩을 사용하므로 원본 파일을 그대로 배치합니다.
3. 아래 실행 명령으로 로딩 결과를 확인합니다. `data/raw/`는 `.gitignore`에 포함되어 있습니다.

## 설치와 실행

Python 3.11 이상이 필요합니다. 아래는 프로젝트 루트에서 실행하는 Windows PowerShell 명령입니다.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

이미 프로젝트 가상환경을 만들었다면 활성화부터 실행하면 됩니다. `main.py`는 로딩 성공 여부, 행·열 수, 전체 컬럼명, 시군 수, 휴폐업상태별 기록 수를 표시합니다. 레코드에 들어 있는 사업자등록번호나 가맹점번호 값은 집계 출력에 포함되지 않습니다.

## Python에서 Pandas 로더 사용

프로젝트 루트에서 다음과 같이 `pathlib.Path`를 전달하면 Pandas `DataFrame`을 받을 수 있습니다.

```python
from pathlib import Path

from src.local_currency.loader import load_merchant_csv

merchants = load_merchant_csv(Path("data/raw/지역화폐가맹점현황.csv"))
status_counts = merchants["휴폐업상태"].value_counts()
```

로더는 필수 컬럼 14개와 각 레코드의 필드 수를 검사합니다. 추가 컬럼과 원본 행·열 순서를 보존합니다. `pandas.read_csv`는 모든 값을 문자열로 읽으며 선행 0, 빈 문자열, `NA`를 그대로 유지합니다. 필드가 없는 빈 줄은 건너뛰고, 올바른 헤더만 있으면 빈 `DataFrame`을 반환합니다. 파일이 없거나 인코딩·구조에 문제가 있으면 원인을 설명하는 오류가 발생합니다.

## 터미널에서 가맹점 검색

```powershell
python search_cli.py --city "수원시"
python search_cli.py --name "스타벅스"
python search_cli.py --industry "커피전문점"
python search_cli.py --city "수원시" --name "스타벅스"
python search_cli.py --city "성남시" --industry "음식점" --limit 10
python search_cli.py --status "폐업자"
python search_cli.py --city "수원시" --status all
```

- `--city`와 `--status`는 정확히 일치해야 합니다. `--name`과 `--industry`는 대소문자 구분 없이 입력한 문자열을 그대로 부분 검색합니다. 입력 앞뒤 공백은 제거합니다.
- 여러 옵션을 지정하면 모든 조건에 일치하는 가맹점만 찾습니다(AND). 생략하거나 공백만 입력한 시군·상호·업종 조건은 적용하지 않습니다.
- `--status`를 생략하거나 공백만 입력하면 `계속사업자`만 검색합니다. `--status all`은 휴업자, 폐업자와 상태가 빈 기록도 검색합니다.
- `--limit`은 출력할 최대 행 수이며 기본값은 20입니다. 1 이상의 정수를 입력합니다. 전체 일치 건수는 출력 제한과 별도로 표시합니다.
- 결과는 원본 순서대로 시군명, 상호명, 업종명, 도로명주소, 휴폐업상태를 표시합니다. 도로명주소가 비어 있으면 지번주소를 사용합니다.

Python에서는 `from src.local_currency.search import search_merchants`로 검색 함수를 불러와 이미 로드한 DataFrame을 재사용할 수 있습니다. 예를 들어 `matches = search_merchants(merchants, city="수원시", name="스타벅스")`로 검색하고 `len(matches)`로 전체 일치 건수를 확인합니다. Python 함수에서는 `status`도 생략하거나 빈 값으로 두면 모든 상태를 검색합니다.

## 자동 테스트

```powershell
python -m pytest tests
```

로더 테스트는 임시 CSV를, 검색과 CLI 테스트는 샘플 DataFrame을 사용하므로 실제 원본 파일 없이 실행할 수 있습니다. 기본 임시 폴더에 접근할 수 없는 환경에서는 `--basetemp`로 프로젝트 안의 새로운 임시 경로를 지정할 수 있습니다.

## 현재 범위와 한계

현재 구현은 로컬 CSV 로딩, 요약 집계, 터미널 검색까지입니다. 지도와 Streamlit 앱은 개발 대상에 남아 있습니다. 업종 검색은 다운로드한 파일의 업종명 표기를 기준으로 합니다. CLI는 실행할 때 CSV 전체를 한 번 메모리에 읽으므로 파일 크기에 따라 메모리 사용량이 늘어납니다. 집계와 검색 결과는 다운로드한 파일의 시점에 해당합니다.
