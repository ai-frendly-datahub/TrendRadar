# TrendRadar API 키 발급 가이드

TrendRadar는 7개 외부 데이터 소스를 사용합니다. 이 중 **4개는 API 키가 필요**하고, **3개는 키 없이 사용 가능**합니다.

---

## 📋 API 키 필요 여부 요약

| 데이터 소스 | API 키 필요 | 우선순위 | 등록 URL |
|------------|------------|---------|---------|
| **Naver DataLab** | ✅ 필수 | 🔴 필수 | [등록하기](https://developers.naver.com/apps/#/register) |
| **YouTube Data API v3** | ✅ 필수 | 🟡 선택 | [등록하기](https://console.cloud.google.com) |
| **Reddit API** | ✅ 필수 | 🟡 선택 | [등록하기](https://www.reddit.com/prefs/apps) |
| **Naver Shopping Insight** | ✅ 필수 | 🟢 선택 | [등록하기](https://developers.naver.com/apps/#/register) |
| Google Trends | ❌ 불필요 | 🔴 필수 | pytrends 라이브러리 사용 |
| Google Trending Searches | ❌ 불필요 | 🟡 선택 | 웹 스크래핑 |
| Wikipedia Pageviews | ❌ 불필요 | 🟡 선택 | 공개 API |

**우선순위 설명**:
- 🔴 **필수**: 핵심 기능, 반드시 설정 필요
- 🟡 **선택**: 추가 데이터 소스, 필요에 따라 설정
- 🟢 **선택**: 특정 도메인(쇼핑)만 해당

---

## ✅ API 키 필요 (4개)

### 1. Naver DataLab API (🔴 필수)

**용도**: 네이버 검색 트렌드 데이터 수집 (국내 검색 동향 파악)

#### 📍 등록 페이지
- https://developers.naver.com/apps/#/register

#### 🔑 발급 단계

1. **네이버 계정 로그인**
   - https://developers.naver.com 접속

2. **애플리케이션 등록**
   - **애플리케이션 이름**: `TrendRadar-Collector` (또는 자유롭게)
   - **사용 API**: **데이터랩(검색어트렌드)** 선택
   - **서비스 환경**: **Web 설정**
   - **웹 서비스 URL**: `http://localhost`
   - **Callback URL**: `http://localhost`

3. **키 확인**
   - [내 애플리케이션] > [개요] 탭
   - `Client ID` (14-20자)
   - `Client Secret` (긴 문자열)

#### 📦 환경 변수

```bash
NAVER_CLIENT_ID=your_client_id_here
NAVER_CLIENT_SECRET=your_client_secret_here
```

#### ⚠️ 제한사항

| 항목 | 값 |
|------|-----|
| 일일 호출 한도 | 1,000회/일 |
| 데이터 형식 | 상대적 비율 (0-100) |
| 최소 조회 기간 | 2016년 1월 1일부터 |
| 인증 방식 | HTTP 헤더 (`X-Naver-Client-Id`, `X-Naver-Client-Secret`) |

#### 📚 참고 자료
- [공식 문서](https://developers.naver.com/docs/serviceapi/datalab/search/search.md)
- [API 레퍼런스](https://developers.naver.com/docs/serviceapi/datalab/search/search.md#%EA%B2%80%EC%83%89%EC%96%B4-%ED%8A%B8%EB%A0%8C%EB%93%9C)

---

### 2. YouTube Data API v3 (🟡 선택)

**용도**: YouTube 트렌딩 비디오, 검색 통계, 조회수 수집

#### 📍 등록 페이지
- https://console.cloud.google.com

#### 🔑 발급 단계

1. **Google Cloud 프로젝트 생성**
   - [Google Cloud Console](https://console.cloud.google.com) 접속
   - 상단 프로젝트 드롭다운 → **"새 프로젝트"**
   - 프로젝트 이름: `TrendRadar-YouTube`

2. **YouTube Data API v3 활성화**
   - **API 및 서비스** → **라이브러리**
   - 검색: `YouTube Data API v3`
   - **"사용"** 버튼 클릭

3. **API 키 생성**
   - **API 및 서비스** → **자격 증명**
   - **"자격 증명 만들기"** → **"API 키"**
   - API 키 복사

4. **API 키 제한 설정 (보안 필수!)**
   - **애플리케이션 제한**: IP 주소 또는 HTTP 리퍼러
   - **API 제한**: YouTube Data API v3만 허용

#### 📦 환경 변수

```bash
YOUTUBE_API_KEY=your_youtube_api_key_here
```

#### ⚠️ 제한사항

| 항목 | 값 |
|------|-----|
| 무료 할당량 | 10,000 units/일 |
| `search.list` 비용 | 100 units |
| `videos.list` 비용 | 1 unit |
| 리셋 시간 | 매일 태평양 시간 자정 |
| 인증 방식 | 쿼리 파라미터 (`?key=YOUR_KEY`) |

#### 📚 참고 자료
- [공식 문서](https://developers.google.com/youtube/v3/docs)
- [할당량 계산기](https://developers.google.com/youtube/v3/determine_quota_cost)
- [Python 퀵스타트](https://developers.google.com/youtube/v3/quickstart/python)

#### 🧪 테스트 명령어

```bash
# API 키 유효성 확인
curl "https://www.googleapis.com/youtube/v3/videos?key=YOUR_KEY&id=dQw4w9WgXcQ&part=statistics"
```

---

### 3. Reddit API (🟡 선택)

**용도**: Reddit subreddit의 인기 게시물 및 트렌드 토픽 수집

#### 📍 등록 페이지
- https://www.reddit.com/prefs/apps

#### 🔑 발급 단계

1. **Reddit 계정 로그인**
   - https://www.reddit.com/ 접속 및 로그인

2. **앱 생성**
   - https://www.reddit.com/prefs/apps 접속
   - **"create another app..."** 클릭

3. **앱 정보 입력**
   - **Name**: `TrendRadar-Collector`
   - **Type**: **script** 선택 ⚠️
   - **Description**: `TrendRadar용 Reddit 데이터 수집기` (선택)
   - **About URL**: (선택)
   - **Redirect URI**: `http://localhost:8080` ⚠️ 필수

4. **자격 증명 확인**
   - **Client ID**: 앱 이름 바로 아래 14자 문자열
   - **Client Secret**: 더 긴 시크릿 문자열

#### 📦 환경 변수

```bash
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=python:TrendRadar:1.0.0 (by /u/your_username)
```

#### ⚠️ User-Agent 형식 (매우 중요!)

Reddit API는 **고유하고 설명적인 User-Agent**를 필수로 요구합니다.

**형식**:
```
<platform>:<app_id>:<version> (by /u/<your_username>)
```

**예시**:
```
python:TrendRadar:1.0.0 (by /u/john_doe)
```

> 🚨 **경고**: User-Agent가 없거나 부적절하면 API 요청이 차단됩니다!

#### ⚠️ 제한사항

| 항목 | 값 |
|------|-----|
| Rate Limit | 60 requests/분 (OAuth 인증) |
| Rate Limit (비인증) | 10 requests/분 |
| User-Agent | 필수 포함 |
| 토큰 만료 시간 | 1시간 (3600초) |
| 인증 방식 | OAuth 2.0 (Password Grant) |

#### 📚 참고 자료
- [공식 문서](https://www.reddit.com/dev/api/)
- [PRAW 라이브러리](https://praw.readthedocs.io/)
- [API 규정](https://redditinc.com/policies/data-api-terms)

#### 🧪 테스트 명령어 (Python)

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

subreddit = reddit.subreddit('technology')
for post in subreddit.hot(limit=5):
    print(post.title)
```

---

### 4. Naver Shopping Insight API (🟢 선택)

**용도**: 네이버 쇼핑 검색량 및 상품 트렌드 데이터 수집

#### 📍 등록 페이지
- https://developers.naver.com/apps/#/register

#### 🔑 발급 단계

**Naver DataLab API와 동일한 절차**입니다. 애플리케이션 등록 시 **쇼핑인사이트** API를 추가로 선택하면 됩니다.

1. 네이버 개발자센터 접속
2. 애플리케이션 등록
3. **사용 API**: **쇼핑인사이트** 선택
4. Client ID/Secret 확인

#### 📦 환경 변수

```bash
# Naver DataLab과 동일한 키 사용 가능
NAVER_CLIENT_ID=your_client_id_here
NAVER_CLIENT_SECRET=your_client_secret_here
```

#### ⚠️ 제한사항

| 항목 | 값 |
|------|-----|
| 일일 호출 한도 | 1,000회/일 (DataLab과 공유) |
| 데이터 형식 | 상대적 비율 (0-100) |
| 인증 방식 | HTTP 헤더 |

#### 📚 참고 자료
- [공식 문서](https://developers.naver.com/docs/serviceapi/datalab/shopping/shopping.md)

---

## ❌ API 키 불필요 (3개)

### 1. Google Trends (pytrends)

**용도**: Google 검색 트렌드 데이터 수집 (글로벌 검색 동향)

**특징**:
- 비공식 Python 라이브러리 `pytrends` 사용
- API 키 불필요
- Rate limit 있음 (너무 자주 호출 시 차단 가능)

**설치**:
```bash
pip install pytrends
```

**사용 예시**:
```python
from pytrends.request import TrendReq

pytrends = TrendReq(hl='ko', tz=540)
pytrends.build_payload(['Python', 'JavaScript'], timeframe='today 3-m')
data = pytrends.interest_over_time()
```

**주의사항**:
- 공식 API가 아니므로 구조 변경 가능
- 호출 간격 관리 필요 (10초 이상 권장)
- 캐싱 활용 권장

---

### 2. Google Trending Searches

**용도**: Google 실시간 급상승 검색어 수집

**특징**:
- 웹 스크래핑 방식
- API 키 불필요
- 공개 RSS 피드 사용

**엔드포인트**:
```
https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR
```

**사용 예시**:
```python
import feedparser

feed = feedparser.parse('https://trends.google.com/trends/trendingsearches/daily/rss?geo=KR')
for entry in feed.entries:
    print(entry.title)
```

---

### 3. Wikipedia Pageviews API

**용도**: Wikipedia 페이지 조회수 수집 (토픽 관심도 측정)

**특징**:
- 공식 Wikimedia REST API
- API 키 불필요
- 무료, 무제한

**엔드포인트**:
```
https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/{project}/all-access/all-agents/{article}/daily/{start}/{end}
```

**사용 예시**:
```python
import requests

url = "https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/ko.wikipedia/all-access/all-agents/Python/daily/20240101/20240131"
response = requests.get(url)
data = response.json()
```

**참고 자료**:
- [공식 문서](https://wikimedia.org/api/rest_v1/)

---

## 🚀 빠른 설정 체크리스트

### 필수 설정 (최소 구성)

- [ ] **Naver DataLab API** 키 발급 및 `.env` 설정
- [ ] `pytrends` 라이브러리 설치
- [ ] TrendRadar 실행 테스트

### 권장 설정 (전체 기능)

- [ ] **Naver DataLab API** 키 발급
- [ ] **YouTube Data API v3** 키 발급
- [ ] **Reddit API** 키 발급 (User-Agent 설정 필수)
- [ ] **Naver Shopping Insight** 키 발급 (쇼핑 도메인만)
- [ ] 모든 키를 `.env` 파일에 추가
- [ ] `pytest tests/unit/` 실행하여 설정 검증

---

## 📝 .env 파일 템플릿

```bash
# ====================================
# Naver APIs (필수)
# ====================================
NAVER_CLIENT_ID=your_naver_client_id_here
NAVER_CLIENT_SECRET=your_naver_client_secret_here

# ====================================
# YouTube Data API v3 (선택)
# ====================================
YOUTUBE_API_KEY=your_youtube_api_key_here

# ====================================
# Reddit API (선택)
# ====================================
REDDIT_CLIENT_ID=your_reddit_client_id_here
REDDIT_CLIENT_SECRET=your_reddit_client_secret_here
REDDIT_USER_AGENT=python:TrendRadar:1.0.0 (by /u/your_username)
```

---

## 🆘 문제 해결

### Naver API: 401 Unauthorized
- **원인**: Client ID/Secret 오류
- **해결**: [내 애플리케이션](https://developers.naver.com/apps/#/list)에서 키 재확인

### YouTube API: 403 Quota Exceeded
- **원인**: 일일 할당량 10,000 units 초과
- **해결**: 다음 날까지 대기 또는 할당량 증가 요청

### Reddit API: 429 Too Many Requests
- **원인**: Rate limit 초과 (60 requests/분)
- **해결**: 요청 간 지연 시간 추가 (`time.sleep(1)`)

### Reddit API: Blocked or 403
- **원인**: User-Agent 누락 또는 부적절
- **해결**: `REDDIT_USER_AGENT` 환경 변수 확인 및 형식 준수

---

## 📞 추가 지원

- **TrendRadar 이슈**: [GitHub Issues](https://github.com/your-repo/TrendRadar/issues)
- **Naver 개발자 지원**: https://developers.naver.com/support
- **Google Cloud 지원**: https://console.cloud.google.com/support
- **Reddit API 지원**: https://www.reddit.com/r/redditdev

---

**마지막 업데이트**: 2026년 3월 5일

---

## 🆕 새로운 API 수집기 (4개)

### 1. HackerNews Collector (❌ 불필요)

**용도**: HackerNews 상위 스토리 수집 (기술 뉴스, 트렌드)

#### 특징
- **인증 불필요**: 공개 Firebase API 사용
- **Rate Limit**: 10,000 requests/hour
- **응답 시간**: 빠름 (캐시됨)

#### 사용 방법

```python
from collectors.hackernews_collector import HackerNewsCollector

collector = HackerNewsCollector()
stories = collector.collect(limit=30)
```

#### 데이터 필드
- `id`: 스토리 ID
- `title`: 제목
- `url`: 링크
- `score`: 점수
- `by`: 작성자
- `time`: 생성 시간 (Unix timestamp)
- `descendants`: 댓글 수

#### 📚 참고 자료
- [HackerNews API 문서](https://github.com/HackerNews/API)

---

### 2. Dev.to Collector (❌ 불필요)

**용도**: Dev.to 인기 기술 글 수집 (개발자 커뮤니티)

#### 특징
- **인증 불필요**: 공개 API 사용
- **Rate Limit**: 10 requests/second
- **응답 시간**: 빠름

#### 사용 방법

```python
from collectors.devto_collector import DevtoCollector

collector = DevtoCollector()
articles = collector.collect(limit=30, tag="python")
```

#### 데이터 필드
- `id`: 글 ID
- `title`: 제목
- `url`: 링크
- `positive_reactions_count`: 좋아요 수
- `comments_count`: 댓글 수
- `published_at`: 발행 시간
- `author`: 작성자 이름
- `tags`: 태그 리스트

#### 📚 참고 자료
- [Dev.to API 문서](https://developers.forem.com/api)

---

### 3. Stack Exchange Collector (✅ 권장)

**용도**: Stack Overflow 트렌딩 질문 수집 (기술 Q&A)

#### 특징
- **API 키 권장**: 더 높은 Rate Limit
- **Rate Limit**: 
  - 키 없음: 300 requests/day
  - 키 있음: 10,000 requests/day
- **응답 시간**: 중간

#### 📍 등록 페이지
- https://stackapps.com/apps/oauth/register

#### 🔑 발급 단계

1. **Stack Apps 계정 로그인**
   - https://stackapps.com 접속
   - Stack Overflow 계정으로 로그인

2. **애플리케이션 등록**
   - **Register your application**
   - **Application Name**: `TrendRadar-StackExchange`
   - **OAuth Domain**: `localhost`
   - **Application Website**: `http://localhost`

3. **API 키 확인**
   - 등록 후 **Client ID** 확인
   - API Key는 선택사항 (권장)

#### 📦 환경 변수

```bash
STACK_EXCHANGE_API_KEY=your_api_key_here
```

#### 사용 방법

```python
from collectors.stackexchange_collector import StackExchangeCollector

collector = StackExchangeCollector(api_key="your_key")
questions = collector.collect(site="stackoverflow", limit=30)
```

#### 데이터 필드
- `question_id`: 질문 ID
- `title`: 제목
- `link`: 링크
- `score`: 점수
- `view_count`: 조회수
- `answer_count`: 답변 수
- `is_answered`: 답변 여부
- `tags`: 태그 리스트

#### 📚 참고 자료
- [Stack Exchange API 문서](https://api.stackexchange.com/docs)
- [Stack Apps](https://stackapps.com)

---

### 4. Product Hunt Collector (✅ 권장)

**용도**: Product Hunt 신규 제품 수집 (스타트업, 신제품)

#### 특징
- **API 키 필수**: GraphQL API 사용
- **Rate Limit**: 500 requests/day (free tier)
- **응답 시간**: 중간

#### 📍 등록 페이지
- https://www.producthunt.com/api/oauth/authorize

#### 🔑 발급 단계

1. **Product Hunt 계정 로그인**
   - https://www.producthunt.com 접속
   - 계정 생성 또는 로그인

2. **API 토큰 생성**
   - [Settings](https://www.producthunt.com/settings) → **API**
   - **Generate Token** 클릭
   - 토큰 복사

3. **토큰 저장**
   - 환경 변수에 저장

#### 📦 환경 변수

```bash
PRODUCT_HUNT_API_KEY=your_api_token_here
```

#### 사용 방법

```python
from collectors.producthunt_collector import ProductHuntCollector

collector = ProductHuntCollector(api_key="your_key")
products = collector.collect(limit=30)
```

#### 데이터 필드
- `id`: 제품 ID
- `name`: 제품명
- `tagline`: 한 줄 설명
- `description`: 상세 설명
- `url`: 링크
- `votes_count`: 투표 수
- `comments_count`: 댓글 수
- `created_at`: 생성 시간
- `makers`: 제작자 정보

#### 📚 참고 자료
- [Product Hunt API 문서](https://api.producthunt.com/v2/docs)

---

## 📊 전체 API 키 요약 (업데이트)

| 데이터 소스 | API 키 필요 | 우선순위 | Rate Limit |
|------------|------------|---------|-----------|
| **Naver DataLab** | ✅ 필수 | 🔴 필수 | 1,000/day |
| **YouTube Data API v3** | ✅ 필수 | 🟡 선택 | 10,000/day |
| **Reddit API** | ✅ 필수 | 🟡 선택 | 60/min |
| **Naver Shopping Insight** | ✅ 필수 | 🟢 선택 | 1,000/day |
| **Stack Exchange API** | ✅ 권장 | 🟡 선택 | 10,000/day (with key) |
| **Product Hunt API** | ✅ 필수 | 🟡 선택 | 500/day |
| Google Trends | ❌ 불필요 | 🔴 필수 | - |
| Google Trending Searches | ❌ 불필요 | 🟡 선택 | - |
| Wikipedia Pageviews | ❌ 불필요 | 🟡 선택 | - |
| **HackerNews API** | ❌ 불필요 | 🟡 선택 | 10,000/hour |
| **Dev.to API** | ❌ 불필요 | 🟡 선택 | 10/sec |
