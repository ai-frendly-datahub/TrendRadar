# GitHub Secrets 설정 가이드

TrendRadar의 GitHub Actions 워크플로우가 API 키를 안전하게 사용하도록 GitHub Secrets를 설정합니다.

---

## 📋 설정 개요

GitHub Secrets는 리포지토리의 환경 변수를 암호화하여 저장하는 기능입니다. CI/CD 워크플로우에서 API 키, 비밀번호 등 민감한 정보를 안전하게 사용할 수 있습니다.

**장점**:
- ✅ 암호화된 저장소 (AES-256)
- ✅ 워크플로우 로그에서 자동 마스킹
- ✅ 특정 브랜치/환경에만 접근 제한 가능
- ✅ 공개 저장소에서도 안전하게 사용

---

## 🔐 필수 Secrets 목록

TrendRadar는 다음 Secrets가 필요합니다:

| Secret 이름 | 설명 | 우선순위 | 예시 값 |
|------------|------|---------|---------|
| `NAVER_CLIENT_ID` | Naver DataLab API Client ID | 🔴 필수 | `abc123xyz` |
| `NAVER_CLIENT_SECRET` | Naver DataLab API Client Secret | 🔴 필수 | `abcdefghijklmnop` |
| `YOUTUBE_API_KEY` | YouTube Data API v3 키 | 🟡 선택 | `AIzaSyDaGmWKa4Js...` |
| `REDDIT_CLIENT_ID` | Reddit API Client ID | 🟡 선택 | `abc123xyz456` |
| `REDDIT_CLIENT_SECRET` | Reddit API Client Secret | 🟡 선택 | `abc-def-ghi-...` |
| `REDDIT_USER_AGENT` | Reddit API User-Agent | 🟡 선택 | `python:TrendRadar:1.0.0 (by /u/username)` |

**우선순위**:
- 🔴 **필수**: Naver DataLab (핵심 기능)
- 🟡 **선택**: YouTube, Reddit (추가 데이터 소스)

---

## 🚀 설정 방법

### 1단계: GitHub 리포지토리 설정 페이지 접속

1. GitHub에서 TrendRadar 리포지토리 페이지 열기
2. 상단 메뉴에서 **Settings** 클릭
3. 왼쪽 사이드바에서 **Secrets and variables** → **Actions** 클릭

### 2단계: New repository secret 추가

#### Secret 1: NAVER_CLIENT_ID (필수)

1. **"New repository secret"** 버튼 클릭
2. **Name**: `NAVER_CLIENT_ID`
3. **Secret**: 네이버 개발자센터에서 발급받은 Client ID 입력
4. **"Add secret"** 클릭

#### Secret 2: NAVER_CLIENT_SECRET (필수)

1. **"New repository secret"** 버튼 클릭
2. **Name**: `NAVER_CLIENT_SECRET`
3. **Secret**: 네이버 개발자센터에서 발급받은 Client Secret 입력
4. **"Add secret"** 클릭

#### Secret 3: YOUTUBE_API_KEY (선택)

1. **"New repository secret"** 버튼 클릭
2. **Name**: `YOUTUBE_API_KEY`
3. **Secret**: Google Cloud Console에서 발급받은 API 키 입력
4. **"Add secret"** 클릭

#### Secret 4: REDDIT_CLIENT_ID (선택)

1. **"New repository secret"** 버튼 클릭
2. **Name**: `REDDIT_CLIENT_ID`
3. **Secret**: Reddit에서 발급받은 Client ID 입력
4. **"Add secret"** 클릭

#### Secret 5: REDDIT_CLIENT_SECRET (선택)

1. **"New repository secret"** 버튼 클릭
2. **Name**: `REDDIT_CLIENT_SECRET`
3. **Secret**: Reddit에서 발급받은 Client Secret 입력
4. **"Add secret"** 클릭

#### Secret 6: REDDIT_USER_AGENT (선택)

1. **"New repository secret"** 버튼 클릭
2. **Name**: `REDDIT_USER_AGENT`
3. **Secret**: `python:TrendRadar:1.0.0 (by /u/your_username)` 형식으로 입력
4. **"Add secret"** 클릭

### 3단계: 설정 완료 확인

Secrets 페이지에 다음과 같이 표시되어야 합니다:

```
Repository secrets

NAVER_CLIENT_ID          Updated 1 minute ago
NAVER_CLIENT_SECRET      Updated 1 minute ago
YOUTUBE_API_KEY          Updated 1 minute ago
REDDIT_CLIENT_ID         Updated 1 minute ago
REDDIT_CLIENT_SECRET     Updated 1 minute ago
REDDIT_USER_AGENT        Updated 1 minute ago
```

> ⚠️ **주의**: Secret 값은 한 번 저장하면 다시 볼 수 없습니다. 수정이 필요하면 **Update** 버튼으로 새 값을 입력해야 합니다.

---

## 🔧 워크플로우에서 Secrets 사용

TrendRadar의 GitHub Actions 워크플로우는 자동으로 Secrets를 환경 변수로 읽어옵니다.

### 워크플로우 파일 예시

`.github/workflows/daily_trends.yml`:

```yaml
name: Daily Trend Collection

on:
  schedule:
    - cron: '0 0 * * *'  # 매일 오전 9시 (KST)
  workflow_dispatch:

jobs:
  collect-trends:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run TrendRadar
        env:
          NAVER_CLIENT_ID: ${{ secrets.NAVER_CLIENT_ID }}
          NAVER_CLIENT_SECRET: ${{ secrets.NAVER_CLIENT_SECRET }}
          YOUTUBE_API_KEY: ${{ secrets.YOUTUBE_API_KEY }}
          REDDIT_CLIENT_ID: ${{ secrets.REDDIT_CLIENT_ID }}
          REDDIT_CLIENT_SECRET: ${{ secrets.REDDIT_CLIENT_SECRET }}
          REDDIT_USER_AGENT: ${{ secrets.REDDIT_USER_AGENT }}
        run: |
          python main.py --mode once --generate-report
```

**중요 포인트**:
- `${{ secrets.SECRET_NAME }}` 구문으로 Secret 참조
- `env:` 섹션에서 환경 변수로 주입
- 워크플로우 로그에서 자동으로 마스킹됨 (`***`)

---

## ✅ 검증 방법

### 방법 1: 워크플로우 수동 실행

1. GitHub 리포지토리 페이지에서 **Actions** 탭 클릭
2. 왼쪽에서 **Daily Trend Collection** 워크플로우 선택
3. 오른쪽 상단 **Run workflow** 버튼 클릭
4. **Run workflow** 확인
5. 실행 결과 확인:
   - ✅ 성공: Secrets가 올바르게 설정됨
   - ❌ 실패: 로그에서 API 인증 오류 확인

### 방법 2: 로컬에서 검증 스크립트 실행

**파일**: `scripts/verify_secrets.py`

```python
#!/usr/bin/env python3
"""GitHub Secrets 검증 스크립트"""

import os
import sys

def verify_secret(name: str, required: bool = True) -> bool:
    """환경 변수 존재 여부 확인"""
    value = os.getenv(name)
    
    if value:
        masked = value[:4] + '***' if len(value) > 4 else '***'
        print(f"✅ {name}: {masked} (설정됨)")
        return True
    elif required:
        print(f"❌ {name}: 설정되지 않음 (필수)")
        return False
    else:
        print(f"⚠️  {name}: 설정되지 않음 (선택)")
        return True

def main():
    print("=" * 50)
    print("TrendRadar GitHub Secrets 검증")
    print("=" * 50)
    
    results = []
    
    # 필수 Secrets
    print("\n🔴 필수 Secrets:")
    results.append(verify_secret('NAVER_CLIENT_ID', required=True))
    results.append(verify_secret('NAVER_CLIENT_SECRET', required=True))
    
    # 선택 Secrets
    print("\n🟡 선택 Secrets:")
    results.append(verify_secret('YOUTUBE_API_KEY', required=False))
    results.append(verify_secret('REDDIT_CLIENT_ID', required=False))
    results.append(verify_secret('REDDIT_CLIENT_SECRET', required=False))
    results.append(verify_secret('REDDIT_USER_AGENT', required=False))
    
    print("\n" + "=" * 50)
    if all(results):
        print("🎉 모든 검증 통과!")
        print("GitHub Actions에서 정상 작동합니다.")
        sys.exit(0)
    else:
        print("⚠️  일부 필수 Secret이 누락되었습니다.")
        print("GitHub 리포지토리 Settings > Secrets에서 추가하세요.")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

**실행 방법** (로컬 테스트):
```bash
# 환경 변수 설정 후 실행
export NAVER_CLIENT_ID="your_id"
export NAVER_CLIENT_SECRET="your_secret"
python scripts/verify_secrets.py
```

---

## 🔒 보안 모범 사례

### ✅ DO (권장 사항)

1. **Secret별 최소 권한 부여**
   - API 키는 필요한 권한만 부여
   - YouTube API는 읽기 전용 키 사용

2. **정기적 키 갱신**
   - 분기별 API 키 재발급
   - 기존 키 폐기 확인

3. **환경별 분리**
   - Production/Staging 환경별 별도 Secret 사용
   - Environment Secrets 활용

4. **접근 제한**
   - 특정 브랜치에만 Secret 접근 허용
   - Dependabot, Pull Request에서 Secret 접근 차단

5. **로그 확인**
   - 워크플로우 로그에서 Secret이 마스킹되는지 확인
   - 실수로 출력되지 않도록 주의

### ❌ DON'T (금지 사항)

1. **Secret 값을 코드에 하드코딩**
   ```python
   # ❌ 절대 금지
   API_KEY = "AIzaSyDaGmWKa4JsXZ..."
   ```

2. **Secret 값을 로그에 출력**
   ```python
   # ❌ 절대 금지
   print(f"API Key: {os.getenv('YOUTUBE_API_KEY')}")
   ```

3. **Secret 값을 커밋**
   ```bash
   # ❌ 절대 금지
   git add .env
   git commit -m "Add API keys"
   ```

4. **공개 저장소에 Secret 노출**
   - `.env` 파일을 `.gitignore`에 추가 필수

5. **Fork된 리포지토리에서 Secret 공유**
   - Fork는 원본 리포지토리의 Secret에 접근 불가 (의도된 동작)

---

## 🆘 문제 해결

### 문제 1: Secret이 설정되었는데 워크플로우에서 읽지 못함

**증상**:
```
KeyError: 'NAVER_CLIENT_ID'
```

**원인**:
- Secret 이름 오타
- 워크플로우 파일에서 `env:` 섹션 누락

**해결**:
1. Secret 이름 확인 (대소문자 구분)
2. 워크플로우 파일에 `env:` 섹션 추가:
   ```yaml
   - name: Run script
     env:
       NAVER_CLIENT_ID: ${{ secrets.NAVER_CLIENT_ID }}
     run: python main.py
   ```

### 문제 2: Fork된 리포지토리에서 워크플로우 실패

**증상**:
```
Error: API authentication failed
```

**원인**:
- Fork는 원본 리포지토리의 Secret에 접근 불가

**해결**:
- Fork된 리포지토리에 별도로 Secret 추가
- 또는 원본 리포지토리에 Pull Request 제출

### 문제 3: Secret 값이 로그에 노출됨

**증상**:
```
API Key: AIzaSyDaGmWKa4JsXZ...
```

**원인**:
- 코드에서 Secret 값을 직접 출력

**해결**:
1. 로그 출력 코드 제거
2. GitHub Support에 연락하여 로그 삭제 요청
3. 해당 API 키 즉시 폐기 및 재발급

### 문제 4: Secret 업데이트 후에도 워크플로우가 실패

**증상**:
- Secret을 업데이트했는데 여전히 인증 실패

**원인**:
- 워크플로우가 이전 실행의 캐시 사용

**해결**:
1. 워크플로우 재실행 (Re-run all jobs)
2. 또는 새 커밋 푸시하여 워크플로우 재트리거

---

## 📚 추가 참고 자료

### 공식 문서
- [GitHub Secrets 가이드](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [GitHub Actions 환경 변수](https://docs.github.com/en/actions/learn-github-actions/variables)
- [GitHub Actions 보안 강화](https://docs.github.com/en/actions/security-guides/security-hardening-for-github-actions)

### TrendRadar 관련 문서
- [API_KEYS.md](API_KEYS.md) - API 키 발급 가이드
- [DEPLOYMENT.md](../DEPLOYMENT.md) - 전체 배포 가이드
- [.env.example](../.env.example) - 환경 변수 템플릿

---

## ✅ 체크리스트

설정 완료 전 이 체크리스트를 확인하세요:

- [ ] GitHub 리포지토리 Settings > Secrets 페이지 확인
- [ ] 필수 Secret 추가 (`NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`)
- [ ] 선택 Secret 추가 (필요한 경우)
- [ ] 워크플로우 파일에서 Secret 참조 확인
- [ ] 워크플로우 수동 실행으로 검증
- [ ] 로그에서 Secret이 마스킹되는지 확인
- [ ] `.env` 파일이 `.gitignore`에 추가되었는지 확인

---

**마지막 업데이트**: 2026년 3월 5일
