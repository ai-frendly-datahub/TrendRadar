# TrendRadar 데이터 소스 확장 전략

## 현재 구현된 소스

### ✅ Tier 1: 검색 트렌드 (구현 완료)
- **Google Trends** (비공식 API - pytrends)
- **네이버 데이터랩** (공식 API)

---

## 추가 가능한 데이터 소스

## 🌟 Tier 2: 글로벌 공식 API (우선순위 높음)

### 1. Google Trends API (공식 - Alpha)
**상태:** 2024년 7월 공식 API 출시 (Alpha)

**특징:**
- 최대 1800일(~5년) 데이터
- 일일/주간/월간/연간 집계
- 최대 수십 개 키워드 비교 (UI는 5개 제한)
- 2일 전까지의 데이터

**API 엔드포인트:**
```
https://trends.googleapis.com/trends/api/...
```

**참고:**
- [Google Trends API 공식 문서](https://developers.google.com/search/apis/trends)
- [공식 발표 블로그](https://developers.google.com/search/blog/2025/07/trends-api)

**구현 우선순위:** ⭐⭐⭐⭐⭐ (최우선)
- pytrends 대체 가능
- 안정성과 신뢰성 향상

### 2. YouTube Trending API
**상태:** 공식 API 제공

**특징:**
- 지역별 인기 동영상 (regionCode 파라미터)
- chart='mostPopular' 파라미터로 트렌드 조회
- 카테고리별 필터링
- 실시간 데이터

**API 엔드포인트:**
```python
# YouTube Data API v3
youtube.videos().list(
    part='snippet,statistics',
    chart='mostPopular',
    regionCode='KR',
    maxResults=50
)
```

**한국 시장 특징:**
- K-POP 콘텐츠 강세
- 2024년 Top 10: QWER "T.B.H", aespa "Supernova", ILLIT "Magnetic" 등

**참고:**
- [YouTube Trends API](https://www.searchapi.io/docs/youtube-trends)
- [실시간 한국 트렌드](https://youworldtop.com/kr)

**구현 우선순위:** ⭐⭐⭐⭐⭐ (최우선)
- 영상 콘텐츠 트렌드 파악 필수
- K-POP, 엔터테인먼트 시장 분석

---

## 🎯 Tier 3: 소셜미디어 트렌드 (중요)

### 3. Twitter/X Trends API
**상태:** 공식 API v1.1, v2 제공 (제한적)

**특징:**
- 지역별 상위 50개 트렌딩 토픽
- WOEID(Where On Earth ID) 기반 위치 지정
- 트윗 볼륨, 트렌드 순위 제공

**API 엔드포인트:**
```
GET /1.1/trends/place.json?id=1
GET /1.1/trends/available.json
```

**제약사항:**
- 2024년부터 무료 API 접근 제한
- 유료 플랜 필요 (기본 $100/월)

**대안:**
- [Apify Twitter Trends Scraper](https://apify.com/karamelo/twitter-trends-scraper/api)
- [Zyla API Hub](https://zylalabs.com/api-marketplace/news/twitter+trends+api/1858)

**참고:**
- [X Developer Platform](https://developer.x.com/en/docs/x-api/v1/trends/trends-for-location/api-reference/get-trends-place)

**구현 우선순위:** ⭐⭐⭐⭐ (높음)
- 실시간 이슈 파악
- 정치, 시사 트렌드 분석

### 4. Reddit API
**상태:** 공식 API 제공

**특징:**
- Subreddit별 인기 게시글
- hot, new, top, controversial 정렬
- 60 req/min, 최대 100개 아이템/요청
- 무료 (인증 없이도 가능)

**API 엔드포인트:**
```
GET /r/{subreddit}/hot.json
GET /r/{subreddit}/top.json?t=day
GET /r/popular.json
```

**2024년 성장 서브레딧:**
- /r/Renters/ (82.69% 성장)
- /r/DungeonMeshi/ (54.56% 성장)
- /r/CreditCardsIndia/ (47.31% 성장)

**참고:**
- [Reddit API 가이드](https://apidog.com/blog/reddit-api-guide/)
- [Apify Reddit Scraper](https://apify.com/trudax/reddit-scraper)

**구현 우선순위:** ⭐⭐⭐ (중간)
- 커뮤니티 기반 트렌드
- 해외 시장 분석

---

## 🇰🇷 Tier 4: 한국 특화 소스 (한국 시장 필수)

### 5. 네이버 쇼핑인사이트 API
**상태:** 공식 API 제공

**특징:**
- 카테고리별 클릭 추이
- 검색어 현황
- 상품 기획자/마케터용
- 네이버 클라우드: 1,000건/일 무료

**API 엔드포인트:**
```
POST https://openapi.naver.com/v1/datalab/shopping/...
```

**활용:**
- 이커머스 트렌드 분석
- 상품 기획, 재고 관리
- 계절별 수요 예측

**참고:**
- [네이버 쇼핑인사이트 API](https://velog.io/@sae0912/웹-크롤링-네이버-API-활용-2-데이터랩쇼핑인사이트)
- [Search Trend API 가이드](https://api.ncloud-docs.com/docs/ai-naver-searchtrend)

**구현 우선순위:** ⭐⭐⭐⭐ (높음)
- 한국 이커머스 필수
- 기존 네이버 데이터랩과 시너지

### 6. Sometrend (썸트렌드)
**상태:** 상용 서비스 (API 제공)

**특징:**
- SNS 빅데이터 분석
- 소비자 관심사 분석 ('갖고싶다', '불편하다', '필요하다' 등)
- 빠른 트렌드 접근
- API 연동 지원

**활용:**
- SNS 버즈 분석
- 브랜드 모니터링
- 경쟁사 분석

**참고:**
- [Sometrend 공식 사이트](https://some.co.kr/)

**구현 우선순위:** ⭐⭐⭐ (중간)
- 유료 서비스
- 한국 SNS 특화

---

## 📊 Tier 5: 서드파티 & 분석 플랫폼

### 7. Semrush Trends API
**특징:**
- 웹사이트 트래픽 분석
- 시장 평가, 경쟁사 분석
- 오디언스 인구통계
- CSV 형식 응답

**참고:**
- [Semrush Trends API](https://developer.semrush.com/api/v3/trends/welcome-to-trends-api/)

**구현 우선순위:** ⭐⭐ (낮음)
- SEO/마케팅 전문가용
- 유료 서비스

### 8. 소셜 리스닝 API

**Mention API**
- 브랜드 멘션 추적
- 시장 분석, 오디언스 참여

**Meltwater API**
- 1.3조 미디어 문서
- 1천만 콘텐츠 아웃렛

**Sprout Social API**
- 소셜미디어 퍼블리싱 및 리스닝
- 다중 플랫폼 지원

**참고:**
- [9 Best Social Listening APIs 2024](https://www.getphyllo.com/post/social-listening-analytics)

**구현 우선순위:** ⭐⭐ (낮음)
- 엔터프라이즈급
- 높은 비용

---

## 🗓️ 구현 로드맵

### Phase 1: 공식 API 우선 구현 (1-2주)
1. ✅ 네이버 데이터랩 (완료)
2. ✅ Google Trends pytrends (완료)
3. 🔄 **Google Trends 공식 API (Alpha)** - 최우선
4. 🔄 **YouTube Trending API** - 최우선

### Phase 2: 소셜미디어 트렌드 (2-3주)
1. **Twitter/X Trends API** (또는 Apify 스크래퍼)
2. **Reddit API** (무료, 쉬운 구현)

### Phase 3: 한국 특화 (3-4주)
1. **네이버 쇼핑인사이트 API**
2. **Sometrend API** (예산 확보 시)

### Phase 4: 고급 분석 (추후)
1. Semrush Trends API
2. 소셜 리스닝 플랫폼 통합

---

## 📋 구현 체크리스트

### 필수 구현 (Must Have)
- [ ] Google Trends 공식 API (Alpha)
- [ ] YouTube Trending API
- [ ] 네이버 쇼핑인사이트 API

### 권장 구현 (Should Have)
- [ ] Twitter/X Trends API
- [ ] Reddit API

### 선택 구현 (Nice to Have)
- [ ] Sometrend API
- [ ] Semrush Trends API
- [ ] 소셜 리스닝 API

---

## 🔐 API 키 관리

각 서비스별 필요한 인증 정보:

```bash
# Google
GOOGLE_TRENDS_API_KEY=...

# YouTube
YOUTUBE_API_KEY=...

# Twitter/X
TWITTER_BEARER_TOKEN=...

# Reddit
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...

# Naver (기존)
NAVER_CLIENT_ID=...
NAVER_CLIENT_SECRET=...

# Sometrend (선택)
SOMETREND_API_KEY=...
```

---

## 📈 예상 효과

### 데이터 커버리지
- **검색 트렌드**: Google, Naver (글로벌 + 한국)
- **영상 트렌드**: YouTube (K-POP, 엔터테인먼트)
- **SNS 트렌드**: Twitter/X, Reddit (실시간 이슈)
- **쇼핑 트렌드**: 네이버 쇼핑인사이트 (이커머스)

### 사용자 페르소나별 가치

**마케터:**
- 다채널 트렌드 한눈에 비교
- 캠페인 타이밍 최적화

**PM/기획자:**
- 제품 수요 예측
- 기능 우선순위 결정

**콘텐츠 크리에이터:**
- 핫한 주제 발굴
- 플랫폼별 전략 수립

---

## Sources

- [Google Trends API (Alpha)](https://developers.google.com/search/apis/trends)
- [YouTube Trends API](https://www.searchapi.io/docs/youtube-trends)
- [Twitter/X API Documentation](https://developer.x.com/en/docs/x-api/v1/trends/trends-for-location/api-reference/get-trends-place)
- [Reddit API Guide](https://apidog.com/blog/reddit-api-guide/)
- [네이버 쇼핑인사이트 API](https://api.ncloud-docs.com/docs/ai-naver-searchtrend)
- [Sometrend](https://some.co.kr/)
- [Semrush Trends API](https://developer.semrush.com/api/v3/trends/welcome-to-trends-api/)
- [Social Listening APIs 2024](https://www.getphyllo.com/post/social-listening-analytics)
