# TrendRadar 테스트 가이드

## 테스트 구조

```
tests/
├── unit/                  # 단위 테스트
│   └── test_collectors.py # Collector 단위 테스트
└── integration/           # 통합 테스트 (예정)

examples/                  # 실사용 예제 스크립트
├── test_all_collectors.py # 전체 Collector 통합 테스트
├── youtube_example.py     # YouTube 예제
├── reddit_example.py      # Reddit 예제
└── naver_shopping_example.py  # 네이버 쇼핑 예제
```

## 🧪 단위 테스트 실행

### 전체 테스트

```bash
pytest tests/
```

### 단위 테스트만

```bash
pytest tests/unit/
```

### 특정 Collector 테스트

```bash
# Google Trends만
pytest tests/unit/test_collectors.py::TestGoogleTrendsCollector

# YouTube만
pytest tests/unit/test_collectors.py::TestYouTubeTrendingCollector

# Reddit만
pytest tests/unit/test_collectors.py::TestRedditCollector
```

### 통합 테스트 제외 (API 호출 없이)

```bash
pytest tests/ -m "not integration"
```

### 통합 테스트만 (실제 API 호출)

```bash
pytest tests/ -m integration
```

## 🔑 API 키 설정

통합 테스트를 실행하려면 환경 변수가 필요합니다:

### Windows (PowerShell)

```powershell
$env:NAVER_CLIENT_ID="your_client_id"
$env:NAVER_CLIENT_SECRET="your_client_secret"
$env:YOUTUBE_API_KEY="your_youtube_key"
$env:REDDIT_CLIENT_ID="your_reddit_id"      # 선택
$env:REDDIT_CLIENT_SECRET="your_reddit_secret"  # 선택
```

### Linux/Mac

```bash
export NAVER_CLIENT_ID="your_client_id"
export NAVER_CLIENT_SECRET="your_client_secret"
export YOUTUBE_API_KEY="your_youtube_key"
export REDDIT_CLIENT_ID="your_reddit_id"      # 선택
export REDDIT_CLIENT_SECRET="your_reddit_secret"  # 선택
```

### .env 파일 사용

```bash
# .env 파일 생성
cat > .env << 'EOF'
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret
YOUTUBE_API_KEY=your_youtube_key
REDDIT_CLIENT_ID=your_reddit_id
REDDIT_CLIENT_SECRET=your_reddit_secret
EOF

# .env 로드 (python-dotenv 필요)
pip install python-dotenv
```

## 📝 통합 테스트 스크립트

### 전체 Collector 테스트

모든 Collector를 한 번에 테스트:

```bash
python examples/test_all_collectors.py
```

**출력 예시:**
```
🎯 TrendRadar Collectors 통합 테스트
============================================================

============================================================
🔍 Google Trends Collector 테스트
============================================================
📊 키워드: 파이썬, 자바스크립트
📅 기간: 최근 3개월
  ✅ 파이썬: 90개 데이터 포인트
     최신 값: 78 (2024-11-23)
  ✅ 자바스크립트: 90개 데이터 포인트
     최신 값: 65 (2024-11-23)
✅ Google Trends 테스트 성공!

============================================================
📊 테스트 결과 요약
============================================================
  Google Trends: ✅ 성공
  네이버 데이터랩: ✅ 성공
  YouTube Trending: ✅ 성공
  Reddit: ✅ 성공
  네이버 쇼핑: ⚠️  건너뜀 (API 키 없음)

  총 5개 중:
  • 성공: 4개
  • 실패: 0개
  • 건너뜀: 1개
```

## 🎯 개별 예제 스크립트

### YouTube 예제

```bash
python examples/youtube_example.py
```

**기능:**
- 한국 인기 Music 영상 Top 10
- 전체 인기 영상
- 트렌딩 키워드 분석
- 카테고리 목록 조회

### Reddit 예제

```bash
python examples/reddit_example.py
```

**기능:**
- r/python 인기 게시글
- r/popular 전체 인기 게시글
- 여러 서브레딧 트렌딩 키워드
- 지난 주 Top 게시글

### 네이버 쇼핑 예제

```bash
python examples/naver_shopping_example.py
```

**기능:**
- 인기 카테고리 목록
- 패션의류 카테고리 트렌드
- 인기 검색어 분석
- 타겟 고객층별 트렌드 (여성 20-30대 등)

## 🐛 문제 해결

### 1. ImportError

```
ModuleNotFoundError: No module named 'collectors'
```

**해결:**
```bash
# 프로젝트 루트에서 실행
cd D:\TrendRadar
python examples/test_all_collectors.py
```

### 2. API 키 에러

```
ValueError: YOUTUBE_API_KEY 환경 변수를 설정해주세요
```

**해결:**
환경 변수가 올바르게 설정되었는지 확인:

```powershell
# Windows
echo $env:YOUTUBE_API_KEY

# Linux/Mac
echo $YOUTUBE_API_KEY
```

### 3. Rate Limit 에러

**Google Trends:**
```
pytrends.exceptions.ResponseError: The request failed: Google returned a response with code 429
```

**해결:** 잠시 기다린 후 재시도

**Reddit:**
```
Too Many Requests (60 requests per minute)
```

**해결:**
- 인증 사용 (더 높은 한도)
- 요청 간 대기 시간 추가

### 4. Naver API 에러

```
401 Unauthorized
```

**해결:**
- Client ID/Secret이 올바른지 확인
- 네이버 개발자센터에서 애플리케이션 상태 확인
- API 사용 허가 여부 확인

## ✅ 테스트 체크리스트

배포 전 확인사항:

- [ ] 모든 단위 테스트 통과 (`pytest tests/unit/`)
- [ ] Google Trends 수집 성공
- [ ] 네이버 데이터랩 수집 성공 (API 키 있을 때)
- [ ] YouTube 수집 성공 (API 키 있을 때)
- [ ] Reddit 수집 성공
- [ ] 네이버 쇼핑 수집 성공 (API 키 있을 때)
- [ ] 통합 테스트 스크립트 실행 성공
- [ ] 예제 스크립트 3개 모두 실행 성공

## 📊 커버리지

테스트 커버리지 확인:

```bash
pytest tests/ --cov=collectors --cov-report=html
```

HTML 리포트:
```bash
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

## 🚀 CI/CD 통합 (예정)

GitHub Actions에서 자동 테스트:

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          pip install -r requirements-dev.txt
      - name: Run unit tests
        run: |
          pytest tests/unit/ -v
      - name: Run integration tests
        env:
          NAVER_CLIENT_ID: ${{ secrets.NAVER_CLIENT_ID }}
          NAVER_CLIENT_SECRET: ${{ secrets.NAVER_CLIENT_SECRET }}
        run: |
          pytest tests/ -m integration -v
```

## 📚 참고 자료

- [pytest 공식 문서](https://docs.pytest.org/)
- [pytest-cov 사용법](https://pytest-cov.readthedocs.io/)
- [TrendRadar Collectors 가이드](COLLECTORS.md)
