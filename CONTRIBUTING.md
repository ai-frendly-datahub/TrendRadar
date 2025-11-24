# 기여 가이드

TrendRadar에 기여해 주셔서 감사합니다! 이 문서는 프로젝트에 효과적으로 기여하는 방법을 안내합니다.

---

## 🤝 기여 방법

TrendRadar는 다음과 같은 기여를 환영합니다:

1. **버그 리포트** - 문제 발견 시 Issue 생성
2. **기능 제안** - 새로운 아이디어 제안
3. **코드 기여** - 버그 수정, 기능 추가, 리팩토링
4. **문서 개선** - 오타 수정, 예제 추가, 번역
5. **테스트 추가** - 테스트 커버리지 향상

---

## 📋 기여 프로세스

### 1. Issue 생성

기여하기 전에 먼저 Issue를 생성하거나 기존 Issue를 확인하세요.

**새 Issue 생성 시 포함할 내용**:
- 명확한 제목
- 문제 상황 또는 제안 내용
- 재현 방법 (버그의 경우)
- 기대하는 동작
- 환경 정보 (OS, Python 버전 등)

### 2. Fork & Clone

```bash
# 1. GitHub에서 Repository Fork
# 2. 로컬에 Clone
git clone https://github.com/YOUR_USERNAME/TrendRadar.git
cd TrendRadar

# 3. Upstream 설정
git remote add upstream https://github.com/ORIGINAL_OWNER/TrendRadar.git
```

### 3. 브랜치 생성

```bash
# 최신 main 브랜치 pull
git checkout main
git pull upstream main

# 기능별 브랜치 생성
git checkout -b feature/your-feature-name
# 또는
git checkout -b fix/bug-description
```

**브랜치 명명 규칙**:
- `feature/` - 새 기능 추가
- `fix/` - 버그 수정
- `docs/` - 문서 수정
- `refactor/` - 리팩토링
- `test/` - 테스트 추가

### 4. 개발 환경 설정

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치 (개발용 포함)
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Pre-commit hooks 설정 (선택)
pip install pre-commit
pre-commit install
```

### 5. 코드 작성

**코드 스타일 준수**:
- **PEP 8** 준수
- **Type hints** 사용 (Python 3.11+)
- **Docstrings** 작성 (Google style)
- **변수명**: snake_case
- **클래스명**: PascalCase

**예시**:
```python
def calculate_spike_score(
    ratio: float,
    current: float,
    baseline: float,
) -> float:
    """급상승 점수를 계산합니다.

    Args:
        ratio: 증가율
        current: 현재 값
        baseline: 기준 값

    Returns:
        0-100 사이의 점수
    """
    ratio_score = min(50, (ratio - 1) * 20)
    absolute_score = min(30, current * 0.3)
    increase_score = min(20, (current - baseline) * 0.2)

    return min(100, max(0, ratio_score + absolute_score + increase_score))
```

### 6. 테스트 작성

모든 새 기능에는 테스트를 추가해야 합니다.

```python
# tests/unit/test_your_feature.py
import pytest
from your_module import your_function


def test_your_function_basic():
    """기본 동작 테스트."""
    result = your_function(input_data)
    assert result == expected_output


def test_your_function_edge_case():
    """엣지 케이스 테스트."""
    result = your_function(edge_case_input)
    assert result == expected_edge_output


@pytest.mark.integration
def test_your_function_integration():
    """통합 테스트 (API 키 필요)."""
    # API 키가 없으면 자동 skip
    api_key = os.getenv("YOUR_API_KEY")
    if not api_key:
        pytest.skip("API key not found")

    result = your_function_with_api(api_key)
    assert result is not None
```

### 7. 테스트 실행

```bash
# 전체 테스트
pytest tests/

# 특정 파일
pytest tests/unit/test_your_feature.py

# 커버리지 확인
pytest --cov=. --cov-report=html
open htmlcov/index.html

# Integration 테스트 제외
pytest -m "not integration"
```

### 8. 코드 포맷팅 & 린트

```bash
# Black 포맷터
black .

# Ruff 린터
ruff check .

# MyPy 타입 체크
mypy collectors/ analyzers/ storage/ reporters/
```

### 9. Commit

**Commit 메시지 규칙**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅 (기능 변경 없음)
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드, 설정 파일 수정

**예시**:
```bash
git add .
git commit -m "feat(analyzers): Add sentiment analysis for Reddit data

Implement sentiment analysis using VADER for Reddit posts and comments.
- Add SentimentAnalyzer class
- Integrate with RedditCollector
- Add unit tests

Closes #42"
```

### 10. Push & Pull Request

```bash
# 브랜치 push
git push origin feature/your-feature-name
```

**Pull Request 생성**:
1. GitHub에서 "Compare & pull request" 클릭
2. PR 템플릿 작성:
   ```markdown
   ## 변경 사항
   - 새 기능: XXX 추가
   - 버그 수정: YYY 해결

   ## 테스트
   - [x] Unit 테스트 추가
   - [x] Integration 테스트 추가
   - [x] 수동 테스트 완료

   ## 체크리스트
   - [x] 코드 스타일 준수 (black, ruff)
   - [x] 타입 힌트 추가
   - [x] Docstrings 작성
   - [x] 테스트 통과
   - [x] 문서 업데이트

   ## 관련 Issue
   Closes #42
   ```

---

## 🔍 Code Review 프로세스

### Reviewer 가이드라인

**체크 사항**:
- [ ] 코드가 PEP 8 준수
- [ ] Type hints 사용
- [ ] Docstrings 작성
- [ ] 테스트 추가 및 통과
- [ ] 문서 업데이트 (필요 시)
- [ ] 보안 취약점 없음
- [ ] 성능 문제 없음

**피드백 방법**:
- 구체적이고 건설적인 피드백
- 코드 라인에 직접 코멘트
- 필요 시 대안 제시
- 칭찬도 중요!

### Contributor 가이드라인

**피드백 받을 때**:
- 피드백을 환영하고 존중
- 질문이 있으면 명확히
- 필요 시 추가 설명
- 요청된 변경사항 반영

---

## 📝 문서 기여

### 문서 종류

1. **README.md** - 프로젝트 개요
2. **docs/*.md** - 상세 가이드
3. **Docstrings** - 코드 내 문서
4. **예제** - examples/ 디렉토리

### 문서 작성 가이드

**명확성**:
- 간결하고 명확한 문장
- 전문 용어 최소화
- 예제 코드 포함

**구조**:
- 제목 계층 구조 명확히
- 목차 추가 (긴 문서)
- 코드 블록에 언어 명시

**예시**:
````markdown
## 새 Collector 추가하기

새로운 데이터 소스를 추가하려면:

### 1. Collector 클래스 생성

`collectors/your_collector.py`:
```python
class YourCollector:
    """Your 데이터 소스 수집기."""

    def collect_trends(self, keywords: list[str]) -> list[dict]:
        """트렌드 데이터를 수집합니다."""
        pass
```

### 2. 테스트 추가

`tests/unit/test_collectors.py`:
```python
def test_your_collector():
    collector = YourCollector()
    result = collector.collect_trends(["test"])
    assert result is not None
```
````

---

## 🐛 버그 리포트

좋은 버그 리포트에는 다음이 포함되어야 합니다:

### 템플릿

```markdown
## 버그 설명
명확하고 간결한 버그 설명

## 재현 방법
1. '...'로 이동
2. '...'를 클릭
3. '...'로 스크롤
4. 에러 발생

## 기대하는 동작
어떻게 동작해야 하는지 설명

## 실제 동작
실제로 어떻게 동작하는지

## 스크린샷
가능하면 스크린샷 첨부

## 환경
- OS: [예: Ubuntu 22.04]
- Python 버전: [예: 3.11.5]
- TrendRadar 버전: [예: v1.0.0]
- 관련 API: [예: Naver DataLab]

## 추가 정보
기타 컨텍스트 정보
```

---

## 💡 기능 제안

새 기능을 제안할 때:

### 템플릿

```markdown
## 기능 설명
기능에 대한 명확한 설명

## 동기
왜 이 기능이 필요한가?

## 제안하는 해결책
어떻게 구현하면 좋을지

## 대안
고려한 다른 방법들

## 추가 정보
관련 리소스, 레퍼런스 등
```

---

## 🎨 코딩 스타일

### Python 스타일

```python
# Good
def calculate_average(values: list[float]) -> float:
    """값들의 평균을 계산합니다."""
    if not values:
        return 0.0
    return sum(values) / len(values)


# Bad
def calc_avg(vals):
    return sum(vals)/len(vals) if vals else 0
```

### Import 순서

```python
# 1. 표준 라이브러리
from datetime import datetime
from pathlib import Path

# 2. 서드파티
import pandas as pd
from jinja2 import Template

# 3. 로컬 모듈
from collectors import GoogleTrendsCollector
from storage import trend_store
```

### Docstring 스타일 (Google)

```python
def complex_function(
    param1: str,
    param2: int,
    param3: bool = False,
) -> dict[str, Any]:
    """한 줄 요약.

    상세 설명이 필요한 경우 여기에 작성.
    여러 줄 가능.

    Args:
        param1: 첫 번째 파라미터 설명
        param2: 두 번째 파라미터 설명
        param3: 세 번째 파라미터 설명 (선택)

    Returns:
        반환값 설명. 딕셔너리 구조 설명:
        {
            "key1": value1 설명,
            "key2": value2 설명
        }

    Raises:
        ValueError: param2가 음수일 때
        RuntimeError: 처리 실패 시

    Example:
        >>> result = complex_function("test", 42)
        >>> print(result["key1"])
        'value'
    """
    pass
```

---

## 🧪 테스트 가이드라인

### 테스트 원칙

1. **Fast** - 빠르게 실행
2. **Independent** - 독립적으로 실행 가능
3. **Repeatable** - 반복 가능
4. **Self-validating** - 자동 검증
5. **Timely** - 적시에 작성

### 테스트 커버리지

최소 커버리지 목표:
- **Unit 테스트**: 80% 이상
- **Integration 테스트**: 주요 플로우 커버

### Fixture 사용

```python
@pytest.fixture
def sample_trend_data():
    """테스트용 샘플 데이터."""
    return [
        {"date": "2024-01-01", "value": 50},
        {"date": "2024-01-02", "value": 55},
    ]


def test_trend_storage(sample_trend_data):
    """저장소 테스트."""
    trend_store.save_trend_points(
        source="test",
        keyword="test",
        points=sample_trend_data
    )
    # assertions...
```

---

## 📦 새 Collector 추가하기

새 데이터 소스를 추가하는 전체 프로세스:

### 1. Collector 구현

```python
# collectors/new_source_collector.py
class NewSourceCollector:
    """New Source 트렌드 수집기."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def collect_trends(
        self,
        keywords: list[str],
        timeframe: str = "today 3-m",
    ) -> list[dict[str, Any]]:
        """트렌드 데이터를 수집합니다."""
        pass
```

### 2. 테스트 추가

```python
# tests/unit/test_collectors.py
def test_new_source_collector():
    collector = NewSourceCollector()
    # test implementation...
```

### 3. 문서 업데이트

- `docs/COLLECTORS.md`에 사용법 추가
- `README.md`의 기술 스택 업데이트

### 4. 예제 추가

```python
# examples/new_source_example.py
from collectors.new_source_collector import NewSourceCollector

collector = NewSourceCollector(api_key="YOUR_KEY")
data = collector.collect_trends(["keyword1", "keyword2"])
print(data)
```

---

## 📞 커뮤니케이션

### 질문하기

- **Issue**: 버그나 기능 제안
- **Discussions**: 일반 질문, 아이디어 논의
- **PR Comments**: 코드 리뷰 관련

### 예절

- 친절하고 존중하는 태도
- 명확하고 구체적인 질문
- 검색 먼저, 질문은 나중에
- 인내심 가지기 (자원봉사 프로젝트)

---

## 🙏 감사합니다!

모든 기여는 크든 작든 환영합니다. TrendRadar를 더 나은 프로젝트로 만드는 데 동참해 주셔서 감사합니다!

**주요 기여자 목록**: [CONTRIBUTORS.md](CONTRIBUTORS.md)

---

## 📚 참고 자료

- [PEP 8 - Python 스타일 가이드](https://pep8.org/)
- [Google Python 스타일 가이드](https://google.github.io/styleguide/pyguide.html)
- [pytest 문서](https://docs.pytest.org/)
- [Git Commit 메시지 가이드](https://www.conventionalcommits.org/)
