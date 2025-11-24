# TrendRadar GitHub Actions 빠른 시작 가이드

이 가이드는 **5분 안에** TrendRadar를 GitHub Actions로 배포하는 방법을 설명합니다.

---

## ✅ 사전 준비

### 1. GitHub 계정
- GitHub 계정이 필요합니다 (무료)
- [github.com](https://github.com)에서 가입

### 2. API 키 발급 (최소 1개)

**필수: Naver DataLab**
1. [네이버 개발자센터](https://developers.naver.com) 접속
2. 로그인 > "Application 등록"
3. 애플리케이션 이름: `TrendRadar`
4. 사용 API: **검색** > **데이터랩(검색어 트렌드)** 선택
5. 등록 완료 후 **Client ID**, **Client Secret** 복사

**선택: YouTube (추가 데이터 수집 시)**
1. [Google Cloud Console](https://console.cloud.google.com) 접속
2. 프로젝트 생성 > API 라이브러리에서 "YouTube Data API v3" 활성화
3. 사용자 인증 정보 > API 키 생성 > 복사

---

## 🚀 5분 배포 가이드

### Step 1: Repository 생성 (1분)

**옵션 A: 기존 프로젝트 Push**
```bash
cd D:\TrendRadar

# GitHub에서 새 repository 생성 (브라우저)
# repository 이름: TrendRadar
# Public 또는 Private 선택

# Remote 추가 및 Push
git remote add origin https://github.com/YOUR_USERNAME/TrendRadar.git
git branch -M main
git push -u origin main
```

**옵션 B: GitHub에서 Import**
1. GitHub 홈 > "New repository"
2. "Import a repository" 선택
3. 로컬 경로를 압축 후 업로드

---

### Step 2: GitHub Secrets 설정 (2분)

1. **Repository > Settings > Secrets and variables > Actions**

2. **"New repository secret" 클릭**

3. **필수 Secrets 추가**:

   **Secret 1: NAVER_CLIENT_ID**
   - Name: `NAVER_CLIENT_ID`
   - Value: `발급받은_클라이언트_ID`
   - "Add secret" 클릭

   **Secret 2: NAVER_CLIENT_SECRET**
   - Name: `NAVER_CLIENT_SECRET`
   - Value: `발급받은_클라이언트_시크릿`
   - "Add secret" 클릭

4. **선택 Secrets (필요 시)**:

   **YouTube API**:
   - Name: `YOUTUBE_API_KEY`
   - Value: `유튜브_API_키`

   **Reddit API**:
   - Name: `REDDIT_CLIENT_ID`
   - Value: `레딧_클라이언트_ID`
   - Name: `REDDIT_CLIENT_SECRET`
   - Value: `레딧_클라이언트_시크릿`

---

### Step 3: GitHub Pages 활성화 (1분)

1. **Repository > Settings > Pages**

2. **Source 설정**:
   - Source: **Deploy from a branch**
   - Branch: **gh-pages** 선택
   - Folder: **/ (root)** 선택
   - "Save" 클릭

3. **확인**:
   - 페이지 상단에 URL 표시됨
   - 예: `https://YOUR_USERNAME.github.io/TrendRadar/`

---

### Step 4: 첫 실행 (1분)

#### 수동 워크플로 실행

1. **Repository > Actions 탭**

2. **왼쪽 사이드바에서 "Daily Trend Collection" 선택**

3. **"Run workflow" 드롭다운 클릭**
   - Branch: `main` 선택
   - "Run workflow" 버튼 클릭

4. **실행 확인**:
   - 워크플로가 즉시 시작됨
   - 노란색 원 (진행 중) → 녹색 체크 (완료)
   - 약 2-5분 소요

5. **로그 확인**:
   - 워크플로 이름 클릭 > "collect-trends" 클릭
   - 각 단계별 로그 확인 가능

---

### Step 5: 결과 확인 (30초)

#### 리포트 URL 접속

```
https://YOUR_USERNAME.github.io/TrendRadar/reports/
```

**생성된 리포트**:
- `trend_YYYY-MM-DD.html` - 일일 트렌드 리포트
- `spike_YYYY-MM-DD.html` - 급상승 키워드 리포트

**첫 실행 시**:
- 데이터가 부족하여 급상승 신호가 적을 수 있음
- 30일 이상 데이터 축적 후 정확한 분석 가능

---

## ⏰ 자동 실행 설정

### 매일 자동 수집

워크플로가 이미 설정되어 있습니다!

**실행 시간**: 매일 오전 9시 (KST)
- UTC 0:00 = KST 9:00

**수정 방법** (시간 변경 시):
```yaml
# .github/workflows/daily_trends.yml
on:
  schedule:
    # 오후 6시로 변경 (UTC 9:00 = KST 18:00)
    - cron: '0 9 * * *'
```

### 수동 실행

언제든지 수동 실행 가능:
1. Actions 탭
2. Daily Trend Collection 선택
3. Run workflow 클릭

---

## 📊 모니터링

### 실행 상태 확인

**Actions 탭에서**:
- 🟢 녹색 체크: 성공
- 🔴 빨간 X: 실패
- 🟡 노란 원: 진행 중

**실패 시 확인사항**:
1. Secrets가 올바른지 확인
2. API 키가 유효한지 확인
3. 로그 확인하여 에러 메시지 파악

### 이메일 알림

GitHub 설정에서 워크플로 실패 시 이메일 수신 가능:
- Settings > Notifications > Actions

---

## 🎨 키워드 세트 커스터마이징

자신만의 키워드 세트로 변경:

1. **로컬에서 `config/keyword_sets.yaml` 편집**:

```yaml
keyword_sets:
  - name: "내 관심 키워드"
    enabled: true
    keywords:
      - "키워드1"
      - "키워드2"
      - "키워드3"
    channels:
      - naver
      - google
    time_range:
      start: "2024-01-01"
      end: "2025-11-24"
    filters:
      time_unit: date
      geo: KR
```

2. **Commit & Push**:
```bash
git add config/keyword_sets.yaml
git commit -m "feat: Update keyword sets"
git push origin main
```

3. **자동 적용**:
   - 다음 자동 실행 시 적용됨
   - 또는 수동으로 "Run workflow" 실행

---

## 🔧 문제 해결

### 1. 워크플로가 실행되지 않음

**원인**: Secrets 누락
**해결**: Settings > Secrets에서 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` 확인

### 2. API 에러 (401 Unauthorized)

**원인**: API 키가 잘못됨
**해결**:
1. 네이버 개발자센터에서 키 재확인
2. Secrets 업데이트
3. 워크플로 재실행

### 3. 리포트가 보이지 않음

**원인**: GitHub Pages가 활성화되지 않음
**해결**:
1. Settings > Pages 확인
2. Source가 "gh-pages" branch인지 확인
3. 첫 배포는 수 분 소요

### 4. Rate Limit 초과

**원인**: 너무 많은 키워드 또는 잦은 실행
**해결**:
1. `config/keyword_sets.yaml`에서 키워드 수 줄이기 (10-20개 권장)
2. 실행 간격 늘리기 (cron 수정)

---

## 📈 데이터 축적 전략

### 첫 30일 (백필 단계)

**목표**: 기준 데이터 확보

```bash
# 로컬에서 과거 데이터 백필 (선택)
python main.py --mode once --generate-report
# 매일 또는 일주일에 3-4회 실행
```

### 30일 이후 (정상 운영)

**자동 수집**: GitHub Actions가 매일 자동 실행
**급상승 감지**: 30일 이상 데이터로 정확한 분석

---

## 🎯 다음 단계

### 단계 1: 데이터 확인 (1주일)
- 매일 리포트 확인
- 데이터 수집이 정상적으로 되는지 검증

### 단계 2: 파라미터 튜닝 (2주차)
- 급상승 감지 파라미터 조정
- 키워드 세트 최적화

### 단계 3: 고급 기능 활용 (3주차+)
- 크로스 채널 분석
- 채널 격차 분석
- 커스텀 리포트

---

## 📚 추가 문서

- [DEPLOYMENT.md](DEPLOYMENT.md) - 전체 배포 옵션
- [ANALYZERS.md](docs/ANALYZERS.md) - 급상승 감지 알고리즘
- [COLLECTORS.md](docs/COLLECTORS.md) - 데이터 수집기 가이드

---

## ✅ 체크리스트

배포 완료 확인:

- [ ] GitHub repository 생성
- [ ] Secrets 설정 (NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)
- [ ] GitHub Pages 활성화
- [ ] 워크플로 첫 실행 성공
- [ ] 리포트 URL 접속 가능
- [ ] 키워드 세트 커스터마이징

**모두 완료하면 TrendRadar가 자동으로 매일 실행됩니다!** 🎉

---

## 💡 프로 팁

### 1. 배지 추가
README에 워크플로 상태 배지 추가:
```markdown
![Daily Trends](https://github.com/YOUR_USERNAME/TrendRadar/workflows/Daily%20Trend%20Collection/badge.svg)
```

### 2. 알림 설정
Slack/Discord 웹훅으로 완료 알림:
- Secrets에 `SLACK_WEBHOOK_URL` 추가
- 워크플로에 알림 단계 추가

### 3. 데이터 백업
주기적으로 DuckDB 파일 다운로드:
- Actions > Artifacts에서 다운로드
- 90일 보관

---

**Happy Automating! 🚀**
