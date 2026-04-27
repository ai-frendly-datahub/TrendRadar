# TrendRadar 아키텍처

## 개요

TrendRadar는 Google Trends와 네이버 데이터랩의 검색 트렌드 데이터를 수집, 저장, 분석하는 시스템입니다.

## 시스템 구성

```
┌─────────────────────────────────────────────────────────────┐
│                        TrendRadar                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │   main.py    │──────│   config/    │                     │
│  │  (CLI Entry) │      │keyword_sets  │                     │
│  └──────┬───────┘      └──────────────┘                     │
│         │                                                     │
│         ▼                                                     │
│  ┌─────────────────────────────────────┐                    │
│  │         collectors/                  │                    │
│  ├─────────────────────────────────────┤                    │
│  │  • NaverDataLabCollector             │                    │
│  │  • GoogleTrendsCollector             │                    │
│  └──────────┬──────────────────────────┘                    │
│             │                                                 │
│             ▼                                                 │
│  ┌─────────────────────────────────────┐                    │
│  │          storage/                    │                    │
│  ├─────────────────────────────────────┤                    │
│  │  • trend_store                       │                    │
│  │  • DuckDB (data/trendradar.duckdb)  │                    │
│  └──────────┬──────────────────────────┘                    │
│             │                                                 │
│             ▼                                                 │
│  ┌─────────────────────────────────────┐                    │
│  │         reporters/                   │                    │
│  ├─────────────────────────────────────┤                    │
│  │  • html_reporter                     │                    │
│  │  • Jinja2 Templates                  │                    │
│  └─────────────────────────────────────┘                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘

External Data Sources:
┌──────────────────┐         ┌──────────────────┐
│  Naver DataLab   │         │  Google Trends   │
│   (Official API) │         │ (pytrends/비공식)│
└──────────────────┘         └──────────────────┘
```

## 모듈 설명

### 1. main.py (Entry Point)

- CLI 인터페이스 제공
- 실행 모드 관리 (once, scheduler)
- 키워드 세트 로딩 및 수집 오케스트레이션

**주요 함수:**
- `run_once()`: 1회 수집 실행
- `run_scheduler()`: 정기 수집 스케줄러
- `collect_trends()`: 트렌드 데이터 수집 및 저장

### 2. collectors/ (데이터 수집)

#### NaverDataLabCollector
- 네이버 데이터랩 공식 API 호출
- 연령/성별/디바이스 필터 지원
- 최대 5개 키워드 동시 조회
- 일일 1,000회 호출 제한

**API 엔드포인트:**
```
POST https://openapi.naver.com/v1/datalab/search
Headers:
  X-Naver-Client-Id: {client_id}
  X-Naver-Client-Secret: {client_secret}
```

#### GoogleTrendsCollector
- pytrends 라이브러리 사용 (비공식 API)
- 글로벌 및 국가별 트렌드 조회
- Rate limit 주의 필요

### 3. storage/ (데이터 저장)

#### trend_store
- DuckDB를 사용한 경량 데이터베이스
- ACID 트랜잭션 지원
- SQL 쿼리 가능

**스키마:**
```sql
CREATE TABLE trend_points (
    source TEXT NOT NULL,           -- 'google' | 'naver'
    keyword TEXT NOT NULL,           -- 검색 키워드
    ts TIMESTAMP NOT NULL,           -- 타임스탬프
    value_normalized FLOAT NOT NULL, -- 정규화된 값 (0-100)
    meta_json TEXT,                  -- 메타데이터 JSON
    created_at TIMESTAMP,
    PRIMARY KEY (source, keyword, ts)
)
```

### 4. reporters/ (리포트 생성)

#### html_reporter
- Jinja2 템플릿 기반 HTML 생성
- 일일 트렌드 리포트
- 키워드 세트별 섹션 구성

### 5. config/ (설정)

#### keyword_sets.yaml
- 키워드 세트 정의
- 채널 선택 (naver, google)
- 필터 설정 (연령, 성별, 디바이스, 지역 등)

## 데이터 흐름

```
1. 키워드 세트 로드
   config/keyword_sets.yaml → main.py

2. 데이터 수집
   main.py → collectors → External APIs

3. 데이터 정규화 및 저장
   collectors → storage/trend_store → DuckDB

4. 리포트 생성
   storage/trend_store → reporters/html_reporter → HTML 파일
```

## 확장 계획

### Phase 1 (현재)
- ✅ 기본 수집 인프라
- ✅ DuckDB 저장소
- ✅ 간단한 HTML 리포트

### Phase 2 (예정)
- [ ] 급상승 키워드 탐지 (analyzers/)
- [ ] 트렌드 비교 분석
- [ ] 통계 대시보드

### Phase 3 (예정)
- [ ] FastAPI 백엔드
- [ ] React 프론트엔드
- [ ] 인터랙티브 차트 (Chart.js, Plotly)

### Phase 4 (예정)
- [ ] GitHub Actions 자동화
- [ ] 알림 채널 (Email, Telegram)
- [ ] MCP 서버 연동

## 기술 스택

| 레이어 | 기술 |
|--------|------|
| 언어 | Python 3.11+ |
| 데이터 수집 | pytrends, requests |
| 데이터 저장 | DuckDB |
| 데이터 처리 | pandas, numpy |
| 템플릿 | Jinja2 |
| 설정 | PyYAML |
| 테스트 | pytest |
| 코드 품질 | black, ruff, mypy |

## 설계 원칙

1. **단순성**: 최소한의 의존성, 명확한 모듈 경계
2. **확장성**: 새로운 데이터 소스 추가 용이
3. **신뢰성**: 에러 핸들링, 재시도 로직
4. **재사용성**: 모듈화된 컴포넌트
5. **테스트 가능성**: TDD 기반 개발

## 보안 고려사항

- 환경 변수로 API 키 관리
- .gitignore로 민감 정보 제외
- HTTPS 통신
- Rate limit 준수

## 성능 최적화

- DuckDB의 빠른 쿼리 성능
- 캐싱을 통한 중복 API 호출 방지
- 배치 처리로 DB 쓰기 최적화
- 스케줄러를 통한 분산 수집
