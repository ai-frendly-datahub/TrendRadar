# TrendRadar Collectors 가이드

## 개요

TrendRadar는 다양한 플랫폼에서 트렌드 데이터를 수집하는 Collector를 제공합니다.

## 📦 구현된 Collectors

### 1. Google Trends Collector
**파일:** [collectors/google_collector.py](../collectors/google_collector.py)

**데이터 소스:** Google Trends (비공식 API - pytrends)

**사용 예시:**
```python
from collectors.google_collector import GoogleTrendsCollector

collector = GoogleTrendsCollector(hl="ko", tz=540)

# 트렌드 데이터 수집
data = collector.collect(
    keywords=["파이썬", "자바스크립트"],
    geo="KR",
    timeframe="2024-01-01 2024-12-31"
)

# 결과
# {"파이썬": [{"date": "2024-01-01", "value": 85}, ...], ...}
```

**주의사항:**
- 비공식 API로 rate limit 있음
- 최대 5개 키워드 권장

---

### 2. 네이버 데이터랩 Collector
**파일:** [collectors/naver_collector.py](../collectors/naver_collector.py)

**데이터 소스:** 네이버 데이터랩 통합 검색어 트렌드 (공식 API)

**사용 예시:**
```python
import os
from collectors.naver_collector import NaverDataLabCollector

collector = NaverDataLabCollector(
    client_id=os.environ["NAVER_CLIENT_ID"],
    client_secret=os.environ["NAVER_CLIENT_SECRET"]
)

# 트렌드 데이터 수집
data = collector.collect(
    keywords=["파이썬", "자바스크립트"],
    start_date="2024-01-01",
    end_date="2024-12-31",
    time_unit="date",
    device="",  # "", "pc", "mo"
    gender="",  # "", "m", "f"
    ages=["20", "30"]  # 20대, 30대
)

# 결과
# {"파이썬": [{"date": "2024-01-01", "value": 85.2, "period": "2024-01-01"}, ...], ...}
```

**필터 옵션:**
| 옵션 | 설명 | 값 |
|------|------|-----|
| `device` | 디바이스 | "", "pc", "mo" |
| `gender` | 성별 | "", "m", "f" |
| `ages` | 연령대 | ["1", "2", "3", "4", "5", "6"] (10대~60대) |

---

### 3. YouTube Trending Collector ⭐ NEW
**파일:** [collectors/youtube_collector.py](../collectors/youtube_collector.py)

**데이터 소스:** YouTube Data API v3 (공식 API)

**사용 예시:**
```python
import os
from collectors.youtube_collector import YouTubeTrendingCollector

collector = YouTubeTrendingCollector(
    api_key=os.environ["YOUTUBE_API_KEY"]
)

# 인기 급상승 영상 수집
videos = collector.collect_trending_videos(
    region_code="KR",
    category_id="10",  # 10=Music
    max_results=50
)

# 결과
# [
#   {
#     "video_id": "abc123",
#     "title": "QWER - T.B.H",
#     "channel_title": "QWER Official",
#     "view_count": 1234567,
#     "like_count": 98765,
#     "tags": ["K-POP", "QWER", ...],
#     ...
#   },
#   ...
# ]

# 트렌딩 키워드 집계
keywords = collector.collect_trending_keywords(
    region_code="KR",
    max_results=50
)

# 결과: {"K-POP": 15, "아이돌": 12, ...}

# 카테고리 목록 조회
categories = collector.get_video_categories(region_code="KR")
```

**주요 카테고리:**
- 10: Music
- 20: Gaming
- 24: Entertainment
- 25: News & Politics
- 28: Science & Technology

---

### 4. Reddit Collector ⭐ NEW
**파일:** [collectors/reddit_collector.py](../collectors/reddit_collector.py)

**데이터 소스:** Reddit API (공식)

**사용 예시:**
```python
from collectors.reddit_collector import RedditCollector

# 인증 없이 사용 (제한적)
collector = RedditCollector()

# 또는 인증 사용 (더 많은 요청)
collector = RedditCollector(
    client_id=os.environ.get("REDDIT_CLIENT_ID"),
    client_secret=os.environ.get("REDDIT_CLIENT_SECRET")
)

# 특정 서브레딧의 인기 게시글
posts = collector.collect_subreddit_posts(
    subreddit="python",
    sort="hot",  # hot, new, top, rising, controversial
    time_filter="day",  # hour, day, week, month, year, all
    limit=25
)

# 결과
# [
#   {
#     "post_id": "xyz789",
#     "title": "Python 3.12 released",
#     "score": 9876,
#     "num_comments": 234,
#     "url": "...",
#     ...
#   },
#   ...
# ]

# r/popular에서 전체 인기 게시글
popular = collector.collect_popular_posts(
    time_filter="day",
    limit=50
)

# 트렌딩 키워드 집계
keywords = collector.collect_trending_keywords(
    subreddits=["python", "programming", "learnpython"],
    time_filter="day",
    limit=25
)

# 결과: {"python": 45, "tutorial": 23, ...}
```

**Rate Limit:**
- 인증 없이: 60 req/min
- 인증 시: 더 높은 한도

---

### 5. 네이버 쇼핑인사이트 Collector ⭐ NEW
**파일:** [collectors/naver_shopping_collector.py](../collectors/naver_shopping_collector.py)

**데이터 소스:** 네이버 쇼핑인사이트 API (공식)

**사용 예시:**
```python
import os
from collectors.naver_shopping_collector import NaverShoppingCollector

collector = NaverShoppingCollector(
    client_id=os.environ["NAVER_CLIENT_ID"],
    client_secret=os.environ["NAVER_CLIENT_SECRET"]
)

# 카테고리별 트렌드
trends = collector.collect_category_trends(
    category="50000000",  # 패션의류
    start_date="2024-01-01",
    end_date="2024-12-31",
    time_unit="month",
    device="mo",  # 모바일
    gender="f",   # 여성
    ages=["20", "30"]
)

# 결과
# [
#   {
#     "category": "패션의류",
#     "points": [{"date": "2024-01", "value": 78.5}, ...]
#   }
# ]

# 카테고리 내 인기 검색어
keywords = collector.collect_category_keywords(
    category="50000000",
    start_date="2024-11-01",
    end_date="2024-11-30",
    time_unit="date"
)

# 결과: {"후드티": [{...}], "패딩": [{...}], ...}

# 인기 카테고리 목록
categories = NaverShoppingCollector.get_popular_categories()
```

**주요 카테고리:**
| ID | 이름 |
|----|------|
| 50000000 | 패션의류 |
| 50000001 | 패션잡화 |
| 50000002 | 화장품/미용 |
| 50000003 | 디지털/가전 |
| 50000006 | 식품 |

---

## 🔑 API 키 설정

### 환경 변수 설정

**.env 파일 생성:**
```bash
# Google Trends (pytrends는 API 키 불필요)

# YouTube
YOUTUBE_API_KEY=your_youtube_api_key

# Naver
NAVER_CLIENT_ID=your_naver_client_id
NAVER_CLIENT_SECRET=your_naver_client_secret

# Reddit (선택)
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
```

### API 키 발급 방법

**YouTube API:**
1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 프로젝트 생성
3. "APIs & Services" > "Credentials"
4. "Create Credentials" > "API Key"
5. YouTube Data API v3 활성화

**네이버 API:**
1. [네이버 개발자센터](https://developers.naver.com) 접속
2. "Application > 애플리케이션 등록"
3. 사용 API 선택:
   - 데이터랩 (검색어 트렌드)
   - 데이터랩 (쇼핑인사이트)
4. Client ID/Secret 복사

**Reddit API:**
1. [Reddit Apps](https://www.reddit.com/prefs/apps) 접속
2. "Create App" 또는 "Create Another App"
3. 유형: script
4. Client ID/Secret 복사

---

## 📊 Collector 비교

| Collector | 데이터 유형 | API 상태 | 무료 사용 | 한국 특화 | 우선순위 |
|-----------|------------|---------|----------|-----------|---------|
| Google Trends | 검색 트렌드 | 비공식 | ✅ | ❌ | ⭐⭐⭐⭐ |
| 네이버 데이터랩 | 검색 트렌드 | 공식 | ✅ (1000/day) | ✅ | ⭐⭐⭐⭐⭐ |
| YouTube Trending | 영상 트렌드 | 공식 | ✅ (할당량) | ✅ | ⭐⭐⭐⭐⭐ |
| Reddit | 커뮤니티 트렌드 | 공식 | ✅ (60/min) | ❌ | ⭐⭐⭐ |
| 네이버 쇼핑 | 쇼핑 트렌드 | 공식 | ✅ (1000/day) | ✅ | ⭐⭐⭐⭐ |

---

## 🎯 사용 시나리오

### 시나리오 1: 종합 트렌드 분석
```python
# 검색 + 영상 + 쇼핑 트렌드 통합
keywords = ["파이썬", "자바스크립트"]

# 1. 검색 트렌드
naver_data = naver_collector.collect(keywords, ...)
google_data = google_collector.collect(keywords, ...)

# 2. 영상 트렌드
youtube_keywords = youtube_collector.collect_trending_keywords(...)

# 3. 쇼핑 트렌드
shopping_data = shopping_collector.collect_category_keywords(...)

# 통합 분석
```

### 시나리오 2: K-POP 트렌드 모니터링
```python
# YouTube에서 음악 카테고리 트렌딩
kpop_videos = youtube_collector.collect_trending_videos(
    region_code="KR",
    category_id="10",  # Music
    max_results=50
)

# 네이버에서 K-POP 검색 트렌드
kpop_search = naver_collector.collect(
    keywords=["케이팝", "아이돌", "걸그룹"],
    ...
)
```

### 시나리오 3: 이커머스 트렌드 파악
```python
# 네이버 쇼핑에서 패션 트렌드
fashion_trends = shopping_collector.collect_category_trends(
    category="50000000",  # 패션의류
    device="mo",  # 모바일
    gender="f",   # 여성
    ages=["20", "30"]
)

# 인기 검색어
fashion_keywords = shopping_collector.collect_category_keywords(
    category="50000000",
    ...
)
```

---

## 🚀 다음 단계

### 구현 예정 Collectors

1. **Google Trends 공식 API (Alpha)**
   - pytrends 대체
   - 더 안정적인 데이터

2. **Twitter/X Trends API**
   - 실시간 이슈
   - 정치, 시사 트렌드

3. **Instagram API** (Meta Graph API)
   - 해시태그 트렌드
   - 인플루언서 분석

4. **TikTok Trends**
   - 숏폼 콘텐츠 트렌드
   - Z세대 분석

---

## 📝 참고 자료

- [Google Trends pytrends](https://github.com/GeneralMills/pytrends)
- [네이버 데이터랩 API](https://developers.naver.com/docs/serviceapi/datalab/search/search.md)
- [YouTube Data API](https://developers.google.com/youtube/v3)
- [Reddit API](https://www.reddit.com/dev/api)
- [네이버 쇼핑인사이트 API](https://developers.naver.com/docs/serviceapi/datalab/shopping/shopping.md)
