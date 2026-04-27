# TrendRadar 프로젝트 구조

WineRadar를 참고하여 구성한 TrendRadar 프로젝트의 전체 구조입니다.

## 📁 디렉토리 구조

```
TrendRadar/
├── 📄 main.py                      # 메인 실행 스크립트 (CLI)
├── 📄 pyproject.toml               # 프로젝트 설정 (Python 3.11+)
├── 📄 requirements.txt             # 핵심 의존성
├── 📄 requirements-dev.txt         # 개발 의존성
├── 📄 README.md                    # 프로젝트 개요 및 사용법
├── 📄 LICENSE                      # MIT License
├── 📄 .gitignore                   # Git 제외 파일
│
├── 📂 collectors/                  # 데이터 수집기
│   ├── __init__.py
│   ├── naver_collector.py         # 네이버 데이터랩 API
│   └── google_collector.py        # Google Trends (pytrends)
│
├── 📂 storage/                     # 데이터 저장소
│   ├── __init__.py
│   └── trend_store.py             # DuckDB 저장/조회
│
├── 📂 analyzers/                   # 트렌드 분석 (예정)
│   └── __init__.py
│
├── 📂 reporters/                   # 리포트 생성
│   ├── __init__.py
│   ├── html_reporter.py           # HTML 리포트 생성
│   └── templates/                 # Jinja2 템플릿
│       └── daily_report.html      # 일일 리포트 템플릿
│
├── 📂 config/                      # 설정 파일
│   ├── keyword_sets.yaml          # 키워드 세트 정의
│   └── .gitkeep
│
├── 📂 data/                        # 데이터 저장소 (gitignore)
│   ├── .gitkeep
│   └── trendradar.duckdb          # DuckDB 파일 (생성됨)
│
├── 📂 docs/                        # 문서
│   ├── ARCHITECTURE.md            # 아키텍처 설계
│   ├── QUICKSTART.md              # 빠른 시작 가이드
│   └── reports/                   # HTML 리포트 출력
│       ├── .gitkeep
│       └── YYYY-MM-DD.html        # 일일 리포트 (생성됨)
│
├── 📂 tests/                       # 테스트
│   ├── __init__.py
│   ├── unit/                      # 단위 테스트 (예정)
│   └── integration/               # 통합 테스트 (예정)
│
└── 📂 venv/                        # 가상환경 (gitignore)
```

## 🔑 핵심 모듈

### 1️⃣ collectors/ - 데이터 수집

**NaverDataLabCollector** ([collectors/naver_collector.py](collectors/naver_collector.py))
- 네이버 데이터랩 공식 API 호출
- 연령/성별/디바이스 필터 지원
- 일일 1,000회 호출 제한

**GoogleTrendsCollector** ([collectors/google_collector.py](collectors/google_collector.py))
- pytrends 라이브러리 사용 (비공식)
- 글로벌 및 국가별 트렌드
- Rate limit 주의

### 2️⃣ storage/ - 데이터 저장

**trend_store** ([storage/trend_store.py](storage/trend_store.py))
- DuckDB 기반 경량 데이터베이스
- `trend_points` 테이블 관리
- SQL 쿼리 지원

**테이블 스키마:**
```sql
CREATE TABLE trend_points (
    source TEXT NOT NULL,           -- 'google' | 'naver'
    keyword TEXT NOT NULL,
    ts TIMESTAMP NOT NULL,
    value_normalized FLOAT NOT NULL,
    meta_json TEXT,
    PRIMARY KEY (source, keyword, ts)
)
```

### 3️⃣ reporters/ - 리포트 생성

**html_reporter** ([reporters/html_reporter.py](reporters/html_reporter.py))
- Jinja2 템플릿 기반
- 키워드 세트별 섹션
- Chart.js 차트 (예정)

### 4️⃣ config/ - 설정

**keyword_sets.yaml** ([config/keyword_sets.yaml](config/keyword_sets.yaml))
```yaml
keyword_sets:
  - name: "키워드 세트 이름"
    enabled: true
    keywords: ["키워드1", "키워드2"]
    channels: ["naver", "google"]
    time_range:
      start: "2024-01-01"
      end: "2025-11-24"
    filters:
      time_unit: date
      geo: KR
```

## 🚀 실행 방법

### 기본 실행
```bash
python main.py --mode once --generate-report
```

### 스케줄러 모드
```bash
python main.py --mode scheduler --interval 24
```

### 옵션
| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--mode` | once / scheduler | once |
| `--interval` | 수집 간격 (시간) | 24 |
| `--source` | naver / google | 둘 다 |
| `--generate-report` | HTML 리포트 생성 | False |
| `--dry-run` | 설정만 확인 | False |

## 📊 데이터 흐름

```
1. 키워드 세트 로드
   config/keyword_sets.yaml
        ↓
2. 데이터 수집
   collectors/ → Naver/Google API
        ↓
3. 데이터 저장
   storage/trend_store → DuckDB
        ↓
4. 리포트 생성
   reporters/html_reporter → HTML
```

## 🔧 기술 스택

| 카테고리 | 기술 |
|----------|------|
| 언어 | Python 3.11+ |
| 데이터 수집 | pytrends, requests |
| 데이터 저장 | DuckDB |
| 데이터 처리 | pandas, numpy |
| 템플릿 | Jinja2 |
| 설정 | PyYAML |
| 테스트 | pytest |

## 📝 WineRadar와의 차이점

| 항목 | WineRadar | TrendRadar |
|------|-----------|------------|
| 데이터 소스 | RSS, HTML 크롤링 | Google Trends, Naver DataLab API |
| 저장소 | DuckDB (그래프 모델) | DuckDB (시계열 데이터) |
| 분석 | 엔티티 추출, 스코어링 | 트렌드 비교, 급상승 감지 |
| 리포트 | 일일 뉴스 카드 | 트렌드 차트 및 통계 |
| 주요 사용자 | 와인 업계 관계자 | 마케터, PM, 콘텐츠 기획자 |

## 📌 다음 단계

### Phase 1: 기본 인프라 ✅
- [x] 프로젝트 구조 설계
- [x] 데이터 수집기 (Naver, Google)
- [x] DuckDB 저장소
- [x] 기본 HTML 리포트

### Phase 2: 분석 기능
- [ ] 급상승 키워드 탐지
- [ ] 트렌드 비교 분석
- [ ] 통계 대시보드

### Phase 3: 시각화
- [ ] Chart.js 인터랙티브 차트
- [ ] 필터링 UI
- [ ] 키워드 세트 관리

### Phase 4: 자동화
- [ ] GitHub Actions 워크플로
- [ ] 알림 채널 (Telegram, Email)
- [ ] MCP 서버 연동

## 📚 문서

- [README.md](README.md) - 프로젝트 개요
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - 아키텍처 설계
- [docs/QUICKSTART.md](docs/QUICKSTART.md) - 빠른 시작 가이드
