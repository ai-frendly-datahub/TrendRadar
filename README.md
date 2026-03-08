# TrendRadar

**🌐 Live Report**: https://ai-frendly-datahub.github.io/TrendRadar/


[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**사람들이 지금 무엇에 관심을 두고 있는지, 검색 행동을 통해 레이더처럼 계속 보여주는 도구**

TrendRadar는 Google Trends와 네이버 데이터랩(통합 검색어 트렌드)을 코어 데이터 소스로 하여, 키워드 세트를 정의하고 두 채널에서 동일한 키워드를 비교·수집하여 DuckDB에 저장한 뒤 분석 및 시각화를 제공하는 트렌드 분석 자동화 도구입니다.

## 프로젝트 목표

- **검색 트렌드 통합**: Google Trends + 네이버 데이터랩의 검색 데이터를 하나의 파이프라인으로 수집·비교
- **글로벌 vs 국내 비교**: 동일 키워드의 해외(Google)와 국내(Naver) 관심도 차이를 시각적으로 분석
- **스파이크 조기 감지**: 검색량 급등을 자동으로 감지하고 알림하여 트렌드 선점 기회 제공
- **경쟁 분석**: 브랜드/제품/캠페인 키워드의 검색 점유율 변화를 시계열로 추적
- **YouTube/Wikipedia 확장**: 검색 트렌드 외 영상 조회수, 위키 페이지뷰 등 다채널 관심도 측정

## 주요 기능

1. **관심 키워드 세트 비교**
   - 내 브랜드 vs 경쟁사
   - 특정 카테고리(예: 와인 종류, 부동산 지역, 상품군 등) 내 키워드 비교
   - 이벤트/캠페인 전후 검색량 변화 추적

2. **두 채널의 시각: Google vs Naver**
   - 같은 키워드를 두 채널에서 동시에 조회
   - 해외/글로벌 관점(Google) + 국내/포털 관점(Naver) 차이 확인
   - 네이버는 연령/성별/디바이스별 필터 지원

3. **급상승 신호 탐지 🔥**
   - 일정 기간 대비 갑자기 뛴 키워드 자동 탐지
   - 3가지 감지 유형: **Surge** (급상승), **Emerging** (신규 등장), **Viral** (바이럴)
   - 0-100점 스코어링 시스템으로 강도 측정
   - 자동 HTML 리포트 생성

4. **크로스 채널 분석 📊**
   - 채널 간 격차 분석 (YouTube vs Google vs Naver)
   - 특정 채널 독점 키워드 발견
   - 플랫폼별 트렌드 강도 비교

## 프로젝트 구조

```
TrendRadar/
├── collectors/        # 5개 데이터 수집기 (Google, Naver, YouTube, Reddit, Shopping)
├── analyzers/         # 급상승 감지 & 크로스 채널 분석 ⭐
│   ├── spike_detector.py
│   └── cross_channel_analyzer.py
├── storage/           # DuckDB 기반 저장소 관리
├── reporters/         # HTML 리포트 생성 (일일 + 급상승)
│   ├── html_reporter.py
│   └── spike_reporter.py ⭐
├── config/            # 키워드 세트 및 설정
├── docs/              # 아키텍처 및 문서
│   ├── ANALYZERS.md ⭐
│   ├── COLLECTORS.md ⭐
│   ├── DATA_SOURCES.md ⭐
│   └── reports/       # 생성된 리포트
├── tests/             # unit / integration 테스트
├── examples/          # 사용 예시 스크립트 ⭐
├── .github/workflows/ # GitHub Actions 자동화 ⭐
└── main.py            # 메인 실행 스크립트
```

## 빠른 시작

### 사전 요구사항

- Python 3.11 이상
- 네이버 개발자센터 계정 (Naver DataLab API 사용 시)

### 설치

```bash
git clone https://github.com/<username>/TrendRadar.git
cd TrendRadar

# 가상환경 생성 및 의존성 설치
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 환경 변수 설정

API 키를 설정하세요 (필요한 것만):

```bash
# 필수 (Naver DataLab)
export NAVER_CLIENT_ID="your_client_id"
export NAVER_CLIENT_SECRET="your_client_secret"

# 선택 (YouTube)
export YOUTUBE_API_KEY="your_youtube_api_key"

# 선택 (Reddit)
export REDDIT_CLIENT_ID="your_reddit_client_id"
export REDDIT_CLIENT_SECRET="your_reddit_client_secret"
```

API 키 발급:
- **Naver**: [네이버 개발자센터](https://developers.naver.com) → [상세 가이드](#naver-datalab-api-설정)
- **YouTube**: [Google Cloud Console](https://console.cloud.google.com) → [상세 가이드](#youtube-data-api-v3-설정)
- **Reddit**: [Reddit App Settings](https://www.reddit.com/prefs/apps) → [상세 가이드](#reddit-api-설정)

### 실행 예시

#### 1회 수집 실행 (일일 리포트 + 급상승 리포트)

```bash
python main.py --mode once --generate-report
```

이 명령은 다음을 수행합니다:
- 모든 키워드 세트 수집 (Google, Naver, YouTube 등)
- DuckDB에 저장
- 일일 트렌드 리포트 생성 (`docs/reports/trend_YYYY-MM-DD.html`)
- 급상승 키워드 감지 및 리포트 생성 (`docs/reports/spike_YYYY-MM-DD.html`)

#### 정기 수집 스케줄러 실행 (24시간 간격)

```bash
python main.py --mode scheduler --interval 24
```

#### 특정 소스만 수집

```bash
# Naver만 수집
python main.py --mode once --source naver --generate-report

# Google만 수집
python main.py --mode once --source google --generate-report
```

#### 급상승 분석만 실행 (수집 없이)

```bash
# 기존 데이터로 급상승 분석
python examples/analyzer_example.py

# 급상승 리포트만 생성
python examples/generate_spike_report.py
```

### 키워드 세트 설정

[config/keyword_sets.yaml](config/keyword_sets.yaml)에서 관심 키워드 세트를 정의하세요:

```yaml
keyword_sets:
  - name: "위스키 시장 동향"
    enabled: true
    keywords:
      - "위스키"
      - "싱글몰트"
      - "하이볼"
    channels:
      - naver
      - google
    time_range:
      start: "2024-01-01"
      end: "2025-11-24"
    filters:
      time_unit: date
      geo: KR
      device: ""
      gender: ""
      ages: []
```

## CLI 옵션

```
--mode              실행 모드: once (1회 실행) 또는 scheduler (정기 실행)
--interval          스케줄러 모드에서 수집 간격 (시간 단위, 기본 24)
--dry-run           Dry-run 모드 (수집 없이 설정만 확인)
--generate-report   HTML 리포트 생성 (일일 + 급상승 리포트) ⭐
--report-dir        리포트 출력 디렉토리 (기본값: docs/reports)
--source            특정 소스만 수집 (naver, google, youtube 등)
--db-path           DuckDB 파일 경로 (기본값: data/trendradar.duckdb)
```

## 급상승 감지 알고리즘

TrendRadar는 3가지 유형의 급상승 신호를 자동으로 감지합니다:

### 🔥 Surge (급상승)
최근 7일 평균이 직전 30일 평균 대비 **1.5배 이상** 증가
```python
spike_ratio = recent_avg / baseline_avg >= 1.5
```
**예시**: 시즌 이벤트, 마케팅 캠페인 효과

### 🌟 Emerging (신규 등장)
과거에는 낮았지만 최근 갑자기 나타남
```python
current_value >= 30 and baseline_value <= 5
```
**예시**: 신제품 출시, 신조어 등장

### 💥 Viral (바이럴)
짧은 기간(3일) 동안 **2배 이상** 폭발적 증가
```python
growth_rate = recent_3days / early_3days >= 2.0
```
**예시**: 소셜미디어 바이럴, 돌발 이슈

자세한 내용은 [docs/ANALYZERS.md](docs/ANALYZERS.md)를 참고하세요.

## 데이터 스키마

### trend_points 테이블

| 컬럼 | 타입 | 설명 |
|------|------|------|
| source | TEXT | 데이터 소스 (google, naver) |
| keyword | TEXT | 조회한 키워드 |
| ts | TIMESTAMP | 타임스탬프 (UTC) |
| value_normalized | FLOAT | 정규화된 검색 관심도 (0-100) |
| meta_json | JSON | 메타데이터 (set_name, filters 등) |

## 기술 스택

- **언어**: Python 3.11+
- **데이터 저장소**: DuckDB
- **데이터 수집**:
  - pytrends (Google Trends 비공식 API)
  - Naver DataLab API (공식)
  - YouTube Data API v3 (공식)
  - Reddit API (공식)
  - Naver Shopping Insight API (공식)
- **데이터 처리**: pandas, numpy
- **템플릿**: Jinja2
- **테스트**: pytest
- **자동화**: GitHub Actions

## 개발 상태

### ✅ 완료 (Phase 1-2)
- ✅ 프로젝트 구조 설계
- ✅ 메인 실행 스크립트 (main.py)
- ✅ 설정 파일 시스템 (keyword_sets.yaml)
- ✅ **5개 데이터 수집기** (Google, Naver, YouTube, Reddit, Shopping)
- ✅ DuckDB 저장소 모듈
- ✅ HTML 리포트 생성 (일일 + 급상승)
- ✅ **급상승 키워드 감지 알고리즘** (Surge/Emerging/Viral)
- ✅ **크로스 채널 분석** (채널 간 격차, 독점 키워드)
- ✅ 통합 테스트 프레임워크
- ✅ **GitHub Actions 자동화**
- ✅ 문서화 (ANALYZERS.md, COLLECTORS.md, DATA_SOURCES.md)

### 📋 예정 (Phase 3-4)
- 대시보드 UI (FastAPI + React)
- 이메일/Telegram 알림 채널
- 시계열 예측 (ARIMA)
- 키워드 클러스터링
- MCP 서버 연동 (Claude Desktop)

## GitHub Actions 자동화

TrendRadar는 GitHub Actions로 자동화된 워크플로를 제공합니다:

### 📅 Daily Trend Collection
매일 오전 9시(KST) 자동 수집 및 리포트 생성
```yaml
# .github/workflows/daily_trends.yml
- 모든 소스에서 트렌드 수집
- 일일 리포트 + 급상승 리포트 생성
- GitHub Pages에 자동 배포
```

### 🔍 On-Demand Spike Analysis
수동 실행으로 급상승 분석
```yaml
# .github/workflows/spike_analysis.yml
- 기존 데이터로 급상승 분석
- 분석 기간 커스터마이징 가능
```

**설정 방법**:
1. GitHub Secrets에 API 키 추가 (`NAVER_CLIENT_ID`, `YOUTUBE_API_KEY` 등)
2. GitHub Pages 활성화 (Settings > Pages > Source: gh-pages branch)
3. 워크플로 자동 실행 또는 수동 트리거

## 주요 문서

### 사용 가이드
- [📊 ANALYZERS.md](docs/ANALYZERS.md) - 급상승 감지 및 크로스 채널 분석 가이드
- [🔌 COLLECTORS.md](docs/COLLECTORS.md) - 5개 데이터 수집기 사용법
- [🌐 DATA_SOURCES.md](docs/DATA_SOURCES.md) - 데이터 소스 리서치 및 우선순위
- [🧪 TESTING.md](docs/TESTING.md) - 테스트 실행 가이드

### 아키텍처 & 배포
- [🏗️ ARCHITECTURE.md](docs/ARCHITECTURE.md) - 시스템 아키텍처
- [🚀 DEPLOYMENT.md](DEPLOYMENT.md) - 배포 가이드 (GitHub Actions, 로컬, 클라우드, Docker)
- [📈 STATUS.md](STATUS.md) - 프로젝트 현황 및 로드맵

### 기여 & 개발
- [🤝 CONTRIBUTING.md](CONTRIBUTING.md) - 기여 가이드 및 코딩 스타일
- [👥 CONTRIBUTORS.md](CONTRIBUTORS.md) - 기여자 목록
- [📝 .env.example](.env.example) - 환경 변수 템플릿

## 주의사항

- **Google Trends**: 비공식 API(pytrends)를 사용하므로 rate limit이 있을 수 있습니다. 호출 간격 관리와 캐시 활용을 권장합니다.
- **Naver DataLab**: 공식 API로 일 1,000회 호출 한도가 있습니다. 키워드 세트와 수집 주기를 분산하여 사용하세요.

---

## API 설정 상세 가이드

### Naver Datalab API 설정

Naver Datalab API는 네이버 검색 트렌드 데이터를 제공합니다. 아래 단계에 따라 API 키를 발급받으세요.

#### 1단계: API 이용 신청 및 키 발급

1. **Naver Developers 접속**: [Naver Developers 센터](https://developers.naver.com/apps/#/register)에 접속하여 네이버 계정으로 로그인
2. **애플리케이션 등록**:
   - **애플리케이션 이름**: `TrendRadar-Collector` (또는 자유롭게 입력)
   - **사용 API**: 카테고리에서 **데이터랩(검색어트렌드)** 선택 및 추가
   - **서비스 환경**: **Web 설정** 선택
   - **웹 설정 정보**:
     - **웹 서비스 URL**: `http://localhost` (실제 서비스가 아니므로 임의 입력 가능)
     - **Callback URL**: `http://localhost` (데이터랩 API는 콜백을 사용하지 않으나 필수 입력 항목)
3. **등록 완료**: 하단의 [등록하기] 버튼 클릭
4. **키 확인**: 생성된 애플리케이션의 **[내 애플리케이션] > [개요]** 탭에서 `Client ID`와 `Client Secret` 복사

#### 2단계: 환경 변수 설정

`.env` 파일에 발급받은 키를 추가합니다:

```env
NAVER_CLIENT_ID=발급받은_Client_ID
NAVER_CLIENT_SECRET=발급받은_Client_Secret
```

#### 3단계: API 작동 테스트

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

url = "https://openapi.naver.com/v1/datalab/search"
headers = {
    "X-Naver-Client-Id": os.getenv("NAVER_CLIENT_ID"),
    "X-Naver-Client-Secret": os.getenv("NAVER_CLIENT_SECRET"),
    "Content-Type": "application/json"
}
body = {
    "startDate": "2024-01-01",
    "endDate": "2024-01-31",
    "timeUnit": "month",
    "keywordGroups": [{"groupName": "AI", "keywords": ["인공지능", "AI"]}]
}

response = requests.post(url, headers=headers, json=body)
if response.status_code == 200:
    print("✅ API 연결 성공!")
else:
    print(f"❌ 연결 실패: {response.status_code}")
```

#### API 제한사항

- **일일 호출 한도**: 1,000회/일
- **데이터 형식**: 상대적 비율(0-100)로 제공
- **공식 문서**: [네이버 데이터랩 API 레퍼런스](https://developers.naver.com/docs/serviceapi/datalab/search/search.md)

---

### YouTube Data API v3 설정

YouTube Data API v3는 YouTube 트렌딩 비디오 및 검색 통계를 제공합니다.

#### 1단계: Google Cloud 프로젝트 생성

1. [Google Cloud Console](https://console.cloud.google.com) 접속 및 로그인
2. **새 프로젝트 생성**: 상단 프로젝트 드롭다운 → **"새 프로젝트"** 선택
   - **프로젝트 이름**: `TrendRadar-YouTube` (또는 원하는 이름)
   - **"만들기"** 클릭

#### 2단계: YouTube Data API v3 활성화

1. **API 라이브러리** → 검색창에 `YouTube Data API v3` 입력
2. **YouTube Data API v3** 클릭 → **"사용"** 버튼 클릭

#### 3단계: API 키 생성

1. **API 및 서비스** → **자격 증명** 선택
2. **"자격 증명 만들기"** → **"API 키"** 선택
3. 생성된 API 키 복사

#### 4단계: API 키 제한 설정 (보안 필수)

**애플리케이션 제한 (권장)**:
- IP 주소 제한: 서버 IP 입력
- HTTP 리퍼러 제한: 웹사이트 도메인 입력

**API 제한**:
- **API 제한** → **"키 제한"** 선택 → **YouTube Data API v3** 체크

#### 5단계: 환경 변수 설정

```env
YOUTUBE_API_KEY=발급받은_API_키
```

#### 6단계: 테스트

```python
import os
import requests

API_KEY = os.getenv('YOUTUBE_API_KEY')
url = "https://www.googleapis.com/youtube/v3/videos"
params = {'key': API_KEY, 'id': 'dQw4w9WgXcQ', 'part': 'statistics'}

response = requests.get(url, params=params)
if response.status_code == 200:
    print("✅ API 키 유효!")
else:
    print(f"❌ 연결 실패: {response.status_code}")
```

#### API 제한사항

- **무료 할당량**: 10,000 units/일
- **API 호출 비용**:
  - `search.list`: 100 units
  - `videos.list`: 1 unit
- **공식 문서**: [YouTube Data API v3 레퍼런스](https://developers.google.com/youtube/v3/docs)

---

### Reddit API 설정

Reddit API는 subreddit의 인기 게시물 및 트렌드 토픽을 수집합니다.

#### 1단계: Reddit 앱 등록

1. [Reddit Apps](https://www.reddit.com/prefs/apps) 접속 및 로그인
2. **"create another app..."** 또는 **"Create App"** 클릭
3. **앱 정보 입력**:
   - **Name**: `TrendRadar-Collector`
   - **Type**: **script** 선택
   - **Description**: `TrendRadar용 Reddit 데이터 수집기` (선택)
   - **Redirect URI**: `http://localhost:8080`

#### 2단계: 자격 증명 확인

앱 생성 후 표시되는 정보:
- **Client ID**: 앱 이름 바로 아래 14자 문자열
- **Client Secret**: 더 긴 시크릿 문자열

#### 3단계: 환경 변수 설정

```env
REDDIT_CLIENT_ID=발급받은_Client_ID
REDDIT_CLIENT_SECRET=발급받은_Client_Secret
REDDIT_USER_AGENT=python:TrendRadar:1.0.0 (by /u/your_username)
```

**User-Agent 형식 (필수)**:
```
<platform>:<app_id>:<version> (by /u/<your_username>)
```

> ⚠️ **중요**: User-Agent가 없으면 API 요청이 차단됩니다!

#### 4단계: 테스트 (PRAW 라이브러리 사용)

```bash
pip install praw
```

```python
import praw
import os

reddit = praw.Reddit(
    client_id=os.getenv('REDDIT_CLIENT_ID'),
    client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
    user_agent=os.getenv('REDDIT_USER_AGENT')
)

try:
    subreddit = reddit.subreddit('technology')
    for post in subreddit.hot(limit=5):
        print(f"✅ {post.title}")
except Exception as e:
    print(f"❌ 연결 실패: {e}")
```

#### API 제한사항

- **Rate Limit**: 60 requests/분 (OAuth 인증)
- **User-Agent 필수**: 모든 요청에 고유한 User-Agent 포함 필수
- **공식 문서**: [Reddit API 문서](https://www.reddit.com/dev/api/)

---

## 기여 가이드

1. 이슈를 만들거나 기존 이슈에 의견을 남깁니다.
2. Fork + 브랜치 생성 후 작업합니다.
3. 테스트를 작성하고 `pytest`로 통과시킵니다.
4. Pull Request를 제출합니다.

## 라이선스

MIT License – 자세한 내용은 [LICENSE](LICENSE)를 참고하세요.
