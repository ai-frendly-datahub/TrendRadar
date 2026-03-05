# TRENDRADAR

다채널 트렌드 수집·분석 레이더. Google Trends, Naver DataLab, Reddit, YouTube, Wikipedia 등 7개 외부 API → 스파이크 감지 + 크로스채널 분석 → DuckDB 저장.

## STRUCTURE

```
TrendRadar/
├── collectors/
│   ├── google_collector.py           # Google Trends API
│   ├── google_trending_collector.py  # Google Trending Searches
│   ├── naver_collector.py            # Naver DataLab API
│   ├── naver_shopping_collector.py   # Naver Shopping Insight
│   ├── reddit_collector.py           # Reddit API
│   ├── wikipedia_collector.py        # Wikipedia Pageviews
│   └── youtube_collector.py          # YouTube Data API
├── analyzers/
│   ├── spike_detector.py             # 트렌드 급등 감지 (UNIQUE)
│   └── cross_channel_analyzer.py     # 채널 간 상관 분석 (UNIQUE)
├── storage/
│   ├── trend_store.py                # TrendStore — DuckDB trend_points 테이블
│   └── search_index.py               # 전문 검색
├── reporters/
│   ├── html_reporter.py              # 일반 HTML 리포트
│   └── spike_reporter.py             # 스파이크 전용 리포트
├── mcp_server/                       # MCP 서버
├── examples/                         # 분석 예제 스크립트 5종
├── config/
│   ├── keyword_sets.yaml             # 기본 키워드 세트
│   ├── keyword_sets_google_trending.yaml
│   └── keyword_sets_wikipedia.yaml
└── main.py                           # --mode once|scheduler
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| 새 채널 추가 | `collectors/` | API별 전용 collector 생성 |
| 키워드 세트 관리 | `config/keyword_sets*.yaml` | 채널별 키워드 분리 |
| 스파이크 감지 | `analyzers/spike_detector.py` | 임계값 기반 급등 탐지 |
| 채널 상관 분석 | `analyzers/cross_channel_analyzer.py` | 멀티채널 교차 분석 |
| API 키 설정 | `.env.example` | NAVER_CLIENT_ID, YOUTUBE_API_KEY, REDDIT_CLIENT_ID 등 |

## DEVIATIONS FROM TEMPLATE

- **7개 전용 collector**: 각 외부 API마다 독립 collector 모듈
- **Storage 분리**: `storage/trend_store.py`로 자체 DuckDB 래퍼 (RadarStorage 아님)
- **Config 구조**: `categories/` 대신 `keyword_sets*.yaml` (채널별 키워드)
- **분석 모듈**: `spike_detector` + `cross_channel_analyzer` — 템플릿의 단순 keyword matching과 다름
- **환경변수**: `.env.example`에 Naver/YouTube/Reddit API 키 필수
- **리포터 2종**: 일반 + 스파이크 전용

## COMMANDS

```bash
python main.py --mode once
python main.py --mode scheduler

# API 키 필요
export NAVER_CLIENT_ID=xxx NAVER_CLIENT_SECRET=xxx
export YOUTUBE_API_KEY=xxx
export REDDIT_CLIENT_ID=xxx REDDIT_CLIENT_SECRET=xxx

pytest tests/unit -m unit
pytest tests/ -m "not network"
```
