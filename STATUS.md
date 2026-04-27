# TrendRadar 프로젝트 현황

**최종 업데이트**: 2025-11-24

## 🎯 프로젝트 개요

**TrendRadar**는 Google Trends, Naver DataLab, YouTube, Reddit 등 다양한 소스에서 트렌드 데이터를 수집하고, 급상승 키워드를 자동으로 감지하여 리포트를 생성하는 트렌드 분석 자동화 도구입니다.

**핵심 가치**:
- 🔥 **급상승 신호 자동 감지** (Surge/Emerging/Viral)
- 📊 **크로스 채널 분석** (YouTube vs Google vs Naver)
- 🤖 **GitHub Actions 자동화**
- 📈 **시계열 데이터 저장 및 분석** (DuckDB)

---

## ✅ 완료된 기능 (Phase 1-2)

### 데이터 수집 (Collectors)
- [x] **GoogleTrendsCollector** - pytrends 기반 Google Trends 수집
- [x] **NaverDataLabCollector** - 공식 API, 연령/성별 필터 지원
- [x] **YouTubeTrendingCollector** - YouTube Data API v3
- [x] **RedditCollector** - Reddit API (hot/top/popular)
- [x] **NaverShoppingCollector** - 쇼핑 인사이트 API

### 데이터 저장 (Storage)
- [x] **DuckDB 기반 저장소**
  - `trend_points` 테이블 자동 생성
  - 타임스탬프 기반 시계열 데이터
  - 메타데이터 JSON 저장
  - 쿼리 API (소스/키워드/날짜 필터)

### 분석 엔진 (Analyzers)
- [x] **SpikeDetector**
  - Surge Detection (1.5배 이상 급상승)
  - Emerging Detection (신규 등장 키워드)
  - Viral Detection (폭발적 증가)
  - 0-100 스코어링 시스템

- [x] **CrossChannelAnalyzer**
  - 채널 간 격차 분석
  - 독점 키워드 발견
  - 다중 채널 비교 통계

### 리포팅 (Reporters)
- [x] **HTML 일일 리포트** (html_reporter.py)
- [x] **HTML 급상승 리포트** (spike_reporter.py)
  - Gradient 디자인
  - 인터랙티브 카드 UI
  - 3가지 급상승 유형별 섹션

### 자동화 (GitHub Actions)
- [x] **Daily Trend Collection** (매일 오전 9시 KST)
  - 전체 소스 자동 수집
  - 리포트 자동 생성
  - GitHub Pages 자동 배포

- [x] **On-Demand Spike Analysis**
  - 수동 실행 워크플로
  - 분석 기간 커스터마이징

### 문서화
- [x] **README.md** - 프로젝트 전체 개요
- [x] **ANALYZERS.md** - 급상승 감지 알고리즘 상세
- [x] **COLLECTORS.md** - 5개 수집기 사용 가이드
- [x] **DATA_SOURCES.md** - 데이터 소스 리서치
- [x] **TESTING.md** - 테스트 실행 가이드
- [x] **ARCHITECTURE.md** - 시스템 아키텍처
- [x] **TESTING_RESULTS.md** - 테스트 결과 요약
- [x] **DEPLOYMENT.md** - 배포 가이드 (GitHub Actions, 로컬, 클라우드, Docker)
- [x] **CONTRIBUTING.md** - 기여 가이드 및 코딩 스타일
- [x] **CONTRIBUTORS.md** - 기여자 목록
- [x] **.env.example** - 환경 변수 템플릿

### 테스트
- [x] **Unit Tests** (pytest)
- [x] **Integration Tests** (API 키 필요 시 auto-skip)
- [x] **기본 기능 테스트** (test_basic.py)

---

## 📊 프로젝트 통계

| 항목 | 수량 |
|------|------|
| 데이터 수집기 | 5개 |
| 분석 알고리즘 | 6개 (Surge/Emerging/Viral + 3가지 채널 분석) |
| 리포트 템플릿 | 2개 (일일 + 급상승) |
| GitHub Actions 워크플로 | 2개 |
| 문서 파일 | 7개 |
| Python 모듈 | 15+ |
| 코드 라인 수 | ~3000+ |

---

## 🚀 시작 가이드

### 1. 설치
```bash
git clone https://github.com/<username>/TrendRadar.git
cd TrendRadar
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. API 키 설정
```bash
# Naver (필수)
export NAVER_CLIENT_ID="your_id"
export NAVER_CLIENT_SECRET="your_secret"

# YouTube (선택)
export YOUTUBE_API_KEY="your_key"

# Reddit (선택)
export REDDIT_CLIENT_ID="your_id"
export REDDIT_CLIENT_SECRET="your_secret"
```

### 3. 실행
```bash
# 1회 수집 + 리포트 생성
python main.py --mode once --generate-report

# 24시간 주기 자동 수집
python main.py --mode scheduler --interval 24

# 급상승 분석만 실행
python examples/analyzer_example.py
```

### 4. 결과 확인
- 일일 리포트: `docs/reports/trend_YYYY-MM-DD.html`
- 급상승 리포트: `docs/reports/spike_YYYY-MM-DD.html`
- 데이터베이스: `data/trendradar.duckdb`

---

## 📋 다음 단계 (Phase 3-4)

### 우선순위 1: 실제 데이터 검증
- [ ] 실제 API 키로 30일 데이터 수집
- [ ] 급상승 감지 파라미터 튜닝
- [ ] 실제 트렌드 케이스 스터디

### 우선순위 2: 고급 분석 기능
- [ ] 시계열 예측 (ARIMA/Prophet)
- [ ] 키워드 클러스터링 (토픽 모델링)
- [ ] 감성 분석 (Reddit/Twitter 데이터)
- [ ] 이상 탐지 (Anomaly Detection)

### 우선순위 3: 대시보드 UI
- [ ] FastAPI 백엔드 서버
- [ ] React 프론트엔드
- [ ] 인터랙티브 차트 (Chart.js)
- [ ] 실시간 업데이트
- [ ] 키워드 세트 관리 UI

### 우선순위 4: 알림 시스템
- [ ] 이메일 알림 (급상승 감지 시)
- [ ] Telegram 봇 통합
- [ ] Slack 웹훅
- [ ] 커스텀 알림 규칙

### 우선순위 5: 추가 데이터 소스
- [ ] Twitter/X API v2
- [ ] TikTok 트렌드
- [ ] Instagram Hashtags
- [ ] Sometrend API 통합

---

## 🏗️ 아키텍처 개요

```
TrendRadar
│
├── collectors/           # 데이터 수집 계층
│   ├── google_collector.py
│   ├── naver_collector.py
│   ├── youtube_collector.py
│   ├── reddit_collector.py
│   └── naver_shopping_collector.py
│
├── storage/              # 데이터 저장 계층
│   └── trend_store.py    # DuckDB 인터페이스
│
├── analyzers/            # 분석 엔진 계층
│   ├── spike_detector.py
│   └── cross_channel_analyzer.py
│
├── reporters/            # 리포팅 계층
│   ├── html_reporter.py
│   └── spike_reporter.py
│
├── .github/workflows/    # 자동화 계층
│   ├── daily_trends.yml
│   └── spike_analysis.yml
│
└── main.py               # 오케스트레이션 계층
```

**데이터 플로우**:
1. **Collectors** → 외부 API에서 트렌드 데이터 수집
2. **Storage** → DuckDB에 시계열 데이터 저장
3. **Analyzers** → 저장된 데이터에서 패턴/급상승 감지
4. **Reporters** → 분석 결과를 HTML 리포트로 생성
5. **GitHub Actions** → 자동화된 워크플로 실행

---

## 💡 사용 사례

### 1. 마케팅 캠페인 모니터링
```python
# 브랜드 키워드 급상승 감지
detector = SpikeDetector(db_path=db_path)
surge = detector.detect_surge_keywords(source="naver")

for signal in surge:
    if signal.keyword in ["브랜드명", "제품명"]:
        print(f"🎉 {signal.keyword} 급상승! ({signal.spike_ratio:.2f}x)")
```

### 2. 채널별 콘텐츠 전략
```python
# YouTube vs 검색 격차 분석
analyzer = CrossChannelAnalyzer(db_path=db_path)
gaps = analyzer.find_channel_gaps("youtube", "google")

youtube_leads = [g for g in gaps if g.leading_channel == "youtube"]
print("📹 YouTube에서 선행 중인 트렌드:")
for gap in youtube_leads:
    print(f"  {gap.keyword} - SEO 기회!")
```

### 3. 신규 트렌드 조기 발견
```python
# Emerging + Viral 조합으로 강력한 신호 포착
emerging = detector.detect_emerging_keywords()
viral = detector.detect_viral_keywords()

hot_trends = set(s.keyword for s in emerging) & set(s.keyword for s in viral)
print("🔥 조기 발견된 강력한 트렌드:", hot_trends)
```

---

## 🔧 기술 스택

| 레이어 | 기술 |
|--------|------|
| 언어 | Python 3.11+ |
| 데이터베이스 | DuckDB |
| 데이터 수집 | pytrends, 공식 API (Naver, YouTube, Reddit) |
| 데이터 처리 | pandas, numpy |
| 템플릿 | Jinja2 |
| 테스트 | pytest |
| 자동화 | GitHub Actions |
| 배포 | GitHub Pages |

---

## 📈 성능 특성

### 처리 속도
- 키워드당 수집: ~2-5초 (API 응답 시간 의존)
- 급상승 감지: ~0.1초/키워드 (DuckDB 쿼리)
- 리포트 생성: ~0.5초

### 확장성
- 키워드 수: 무제한 (권장 100개 이하)
- 데이터 기간: 무제한 (DuckDB 효율성)
- 채널 수: 무제한

### 제약사항
- Google Trends: Rate limit (pytrends 비공식)
- Naver API: 1,000회/일
- YouTube API: 10,000 quota/일
- Reddit API: 60회/분 (인증 없이)

---

## 🤝 기여 가이드

### 개발 환경 설정
```bash
# 의존성 설치
pip install -r requirements.txt

# 테스트 실행
pytest tests/unit/ -v

# 코드 포맷팅
black .
ruff check .
```

### 기여 절차
1. Issue 생성 또는 기존 Issue 선택
2. Fork & 브랜치 생성 (`feature/your-feature`)
3. 코드 작성 & 테스트 추가
4. `pytest` 통과 확인
5. Pull Request 제출

### 코드 스타일
- **PEP 8** 준수
- **Type hints** 필수
- **Docstrings** 필수 (Google style)
- **Black** 포맷터 사용

---

## 📞 문의 및 지원

- **Issues**: [GitHub Issues](https://github.com/<username>/TrendRadar/issues)
- **Discussions**: [GitHub Discussions](https://github.com/<username>/TrendRadar/discussions)
- **Documentation**: [docs/](docs/)

---

## 📄 라이선스

MIT License - 자유롭게 사용, 수정, 배포 가능

---

## 🙏 감사의 글

이 프로젝트는 다음 오픈소스 프로젝트에 영감을 받았습니다:
- **WineRadar** - 프로젝트 구조 및 설계 패턴
- **pytrends** - Google Trends 비공식 API
- **DuckDB** - 빠르고 효율적인 분석용 데이터베이스

---

**TrendRadar** - 트렌드를 레이더처럼 계속 보여주는 도구 🎯
