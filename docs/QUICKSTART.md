# TrendRadar 빠른 시작 가이드

## 설치

### 1. 저장소 클론

```bash
git clone https://github.com/<username>/TrendRadar.git
cd TrendRadar
```

### 2. 가상환경 생성 및 활성화

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

개발 의존성까지 설치하려면:
```bash
pip install -r requirements-dev.txt
```

## 네이버 API 설정

### 1. 네이버 개발자센터 앱 등록

1. [네이버 개발자센터](https://developers.naver.com) 접속
2. "Application > 애플리케이션 등록" 클릭
3. 애플리케이션 정보 입력:
   - 애플리케이션 이름: TrendRadar
   - 사용 API: 데이터랩 (검색어 트렌드)
4. 등록 완료 후 **Client ID**와 **Client Secret** 복사

### 2. 환경 변수 설정

**Windows (PowerShell):**
```powershell
$env:NAVER_CLIENT_ID="your_client_id"
$env:NAVER_CLIENT_SECRET="your_client_secret"
```

**Windows (CMD):**
```cmd
set NAVER_CLIENT_ID=your_client_id
set NAVER_CLIENT_SECRET=your_client_secret
```

**Linux/Mac:**
```bash
export NAVER_CLIENT_ID="your_client_id"
export NAVER_CLIENT_SECRET="your_client_secret"
```

또는 `.env` 파일 생성:
```bash
echo "NAVER_CLIENT_ID=your_client_id" > .env
echo "NAVER_CLIENT_SECRET=your_client_secret" >> .env
```

## 키워드 세트 설정

`config/keyword_sets.yaml` 파일을 수정하여 관심 키워드를 정의하세요:

```yaml
keyword_sets:
  - name: "나의 첫 번째 트렌드"
    enabled: true
    description: "테스트용 키워드 세트"
    keywords:
      - "파이썬"
      - "자바스크립트"
      - "타입스크립트"
    channels:
      - naver
      - google
    time_range:
      start: "2024-10-01"
      end: "2025-11-24"
    filters:
      time_unit: date
      geo: KR
      device: ""
      gender: ""
      ages: []
```

### 키워드 세트 옵션 설명

| 옵션 | 설명 | 예시 |
|------|------|------|
| `name` | 키워드 세트 이름 | "위스키 시장 동향" |
| `enabled` | 활성화 여부 | true / false |
| `keywords` | 검색 키워드 리스트 (최대 5개) | ["위스키", "싱글몰트"] |
| `channels` | 데이터 소스 | ["naver", "google"] |
| `time_range.start` | 시작일 | "2024-01-01" |
| `time_range.end` | 종료일 | "2025-11-24" |
| `filters.time_unit` | 시간 단위 (Naver) | date, week, month |
| `filters.device` | 디바이스 (Naver) | "", "pc", "mo" |
| `filters.gender` | 성별 (Naver) | "", "m", "f" |
| `filters.ages` | 연령대 (Naver) | [], ["1", "2"] (10대, 20대) |
| `filters.geo` | 지역 (Google) | "KR", "US", "JP" |

## 실행

### 1회 수집

```bash
python main.py --mode once --generate-report
```

### 특정 소스만 수집

**Naver만:**
```bash
python main.py --mode once --source naver --generate-report
```

**Google만:**
```bash
python main.py --mode once --source google --generate-report
```

### 정기 수집 (스케줄러)

24시간마다 자동 수집:
```bash
python main.py --mode scheduler --interval 24 --generate-report
```

12시간마다:
```bash
python main.py --mode scheduler --interval 12
```

### Dry-run (설정 확인)

```bash
python main.py --dry-run
```

## 리포트 확인

리포트는 `docs/reports/` 디렉토리에 HTML 파일로 생성됩니다:

```
docs/reports/2025-11-24.html
```

브라우저에서 열어 확인하세요.

## 데이터 조회

Python 스크립트에서 직접 데이터 조회:

```python
from storage import trend_store

# 특정 키워드의 모든 데이터
points = trend_store.query_trend_points(keyword="위스키")

# 특정 기간의 데이터
points = trend_store.query_trend_points(
    keyword="위스키",
    start_date="2024-10-01",
    end_date="2024-11-01"
)

# Naver 데이터만
naver_points = trend_store.query_trend_points(
    source="naver",
    keyword="위스키"
)
```

## 문제 해결

### 1. 네이버 API 에러

**에러:** `NAVER_CLIENT_ID와 NAVER_CLIENT_SECRET 환경 변수를 설정해주세요`

**해결:**
- 환경 변수가 올바르게 설정되었는지 확인
- 터미널을 재시작하고 다시 설정

### 2. pytrends 에러

**에러:** `Google Trends 데이터 수집 실패`

**해결:**
- pytrends는 비공식 API이므로 일시적으로 차단될 수 있음
- 잠시 후 재시도
- `--source naver`로 네이버만 사용

### 3. DuckDB 에러

**에러:** `IO Error: Could not open file`

**해결:**
- `data/` 디렉토리가 존재하는지 확인
- 파일 권한 확인

## 다음 단계

1. **키워드 세트 추가**: `config/keyword_sets.yaml`에 새로운 세트 추가
2. **정기 수집 설정**: 스케줄러 모드로 자동화
3. **데이터 분석**: DuckDB 파일을 SQL 클라이언트로 직접 조회
4. **리포트 커스터마이징**: `reporters/templates/` 템플릿 수정

## 추가 리소스

- [아키텍처 문서](ARCHITECTURE.md)
- [네이버 데이터랩 API 문서](https://developers.naver.com/docs/serviceapi/datalab/search/search.md)
- [pytrends GitHub](https://github.com/GeneralMills/pytrends)
