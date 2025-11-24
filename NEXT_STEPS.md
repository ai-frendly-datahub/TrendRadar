# 🎉 TrendRadar GitHub Push 완료!

## ✅ 완료된 작업

- ✅ 로컬 Git 저장소 초기화
- ✅ 6개 커밋 생성
- ✅ GitHub에 Push 완료

---

## 🚀 다음 단계: GitHub Actions 설정

### Step 1: GitHub Secrets 설정 (필수)

**Repository > Settings > Secrets and variables > Actions > New repository secret**

#### 1-1. NAVER_CLIENT_ID 추가
- Name: `NAVER_CLIENT_ID`
- Value: 네이버 개발자센터에서 발급받은 Client ID
- "Add secret" 클릭

#### 1-2. NAVER_CLIENT_SECRET 추가
- Name: `NAVER_CLIENT_SECRET`
- Value: 네이버 개발자센터에서 발급받은 Client Secret
- "Add secret" 클릭

**네이버 API 키 발급 방법**:
1. https://developers.naver.com 접속
2. 로그인 > "Application 등록"
3. 애플리케이션 이름: `TrendRadar`
4. 사용 API: **검색** > **데이터랩(검색어 트렌드)** 체크
5. 등록 완료 후 Client ID, Client Secret 복사

---

### Step 2: GitHub Pages 활성화

**Repository > Settings > Pages**

1. **Source 설정**:
   - Source: `Deploy from a branch` 선택
   - Branch: `gh-pages` 선택
   - Folder: `/ (root)` 선택
   - "Save" 클릭

2. **확인**:
   - 페이지 상단에 URL이 표시됨
   - 예: `https://YOUR_USERNAME.github.io/TrendRadar/`

**주의**: 첫 배포는 워크플로 실행 후 자동 생성됨

---

### Step 3: 첫 워크플로 실행

**Repository > Actions 탭**

1. **"Daily Trend Collection" 워크플로 선택**
   - 왼쪽 사이드바에서 클릭

2. **수동 실행**:
   - 오른쪽 "Run workflow" 드롭다운 클릭
   - Branch: `main` 선택
   - "Run workflow" 녹색 버튼 클릭

3. **실행 확인**:
   - 🟡 노란 원: 진행 중 (2-5분 소요)
   - 🟢 녹색 체크: 완료
   - 🔴 빨간 X: 실패 (로그 확인 필요)

4. **로그 확인**:
   - 워크플로 이름 클릭
   - "collect-trends" job 클릭
   - 각 단계별 로그 확인

---

### Step 4: 결과 확인

#### 4-1. Artifacts 다운로드 (선택)

**Actions > 완료된 워크플로 > Artifacts 섹션**
- `trendradar-db-XXX`: DuckDB 데이터베이스 파일
- 다운로드하여 로컬에서 분석 가능

#### 4-2. GitHub Pages 리포트 확인

**URL**: `https://YOUR_USERNAME.github.io/TrendRadar/reports/`

**생성된 파일**:
- `trend_YYYY-MM-DD.html` - 일일 트렌드 리포트
- `spike_YYYY-MM-DD.html` - 급상승 키워드 리포트

**첫 실행 시 참고**:
- 데이터가 1일치만 있으므로 급상승 신호가 적거나 없을 수 있음
- 30일 이상 데이터 축적 후 정확한 분석 가능
- 매일 자동 실행되면서 데이터가 쌓임

---

## ⏰ 자동 실행 확인

### 매일 자동 수집

설정된 스케줄: **매일 오전 9시 (KST)**

**Actions 탭에서 확인**:
- 매일 자동으로 워크플로 실행
- 실행 히스토리 확인 가능
- 실패 시 이메일 알림 (GitHub 설정에서 활성화)

### 실행 시간 변경 (선택)

시간을 변경하고 싶다면:

1. `.github/workflows/daily_trends.yml` 파일 편집
2. `cron` 값 수정:
   ```yaml
   schedule:
     # UTC 시간 기준
     # UTC 0:00 = KST 9:00
     # UTC 9:00 = KST 18:00 (오후 6시)
     - cron: '0 9 * * *'
   ```
3. Commit & Push

---

## 🎨 키워드 세트 커스터마이징

### 자신의 관심 키워드로 변경

1. **`config/keyword_sets.yaml` 편집**:

```yaml
keyword_sets:
  # 예시 1: 마케팅 키워드
  - name: "마케팅 트렌드"
    enabled: true
    keywords:
      - "디지털마케팅"
      - "SEO"
      - "SNS마케팅"
      - "인플루언서"
    channels:
      - naver
      - google
    time_range:
      start: "2024-01-01"
      end: "2025-12-31"
    filters:
      time_unit: date
      geo: KR

  # 예시 2: 기술 트렌드
  - name: "AI 트렌드"
    enabled: true
    keywords:
      - "ChatGPT"
      - "LLM"
      - "생성형AI"
      - "머신러닝"
    channels:
      - naver
      - google
    time_range:
      start: "2024-01-01"
      end: "2025-12-31"
```

2. **Commit & Push**:
```bash
git add config/keyword_sets.yaml
git commit -m "feat: Update keyword sets"
git push origin main
```

3. **다음 실행 시 자동 적용**

---

## 📊 데이터 축적 전략

### 추천 프로세스

#### 1주차: 초기 데이터 수집
- GitHub Actions가 매일 자동 실행
- 데이터 수집 모니터링
- API 키 정상 작동 확인

#### 2주차: 기준 데이터 확보
- 7일 데이터 축적
- 첫 Surge 감지 가능
- 리포트 패턴 확인

#### 3-4주차: 완전한 분석
- 30일 데이터 완성
- 정확한 급상승 감지
- Baseline 대비 Spike 분석

#### 30일 이후: 정상 운영
- 매일 자동 분석
- 급상승 트렌드 모니터링
- 리포트 기반 의사결정

---

## 🔍 모니터링 및 알림

### Actions 실행 모니터링

**GitHub 앱 (모바일)**:
- iOS/Android 앱 설치
- Push 알림으로 워크플로 상태 확인

**이메일 알림**:
- GitHub Settings > Notifications > Actions
- "Send notifications for failed workflows only" 체크

### Slack/Discord 통합 (고급)

워크플로에 웹훅 추가:
1. Slack/Discord 웹훅 URL 생성
2. GitHub Secrets에 `SLACK_WEBHOOK_URL` 추가
3. `.github/workflows/daily_trends.yml`에 알림 단계 추가

---

## 🐛 문제 해결

### 워크플로 실패 시

**1. Secrets 확인**
- Settings > Secrets에서 `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` 존재 확인
- 값이 정확한지 재확인

**2. 로그 확인**
- Actions > 실패한 워크플로 클릭
- 빨간색 X 표시된 단계 클릭
- 에러 메시지 확인

**3. 일반적인 에러**

**에러**: `401 Unauthorized`
**원인**: API 키가 잘못됨
**해결**: Secrets 업데이트 후 재실행

**에러**: `Rate Limit Exceeded`
**원인**: 너무 많은 키워드 또는 빈번한 실행
**해결**: 키워드 수 줄이기 (10-20개 권장)

**에러**: `No module named 'pytrends'`
**원인**: 의존성 설치 실패
**해결**: 워크플로에서 자동 해결 (재실행)

---

## 📈 성능 최적화

### 키워드 수 권장사항

- **10-20개**: 최적 (빠른 수집, 정확한 분석)
- **20-50개**: 양호 (약간 느림)
- **50개 이상**: 주의 (Rate Limit 위험)

### 채널 선택

- **Naver + Google**: 기본 (무료, 안정적)
- **+YouTube**: 추가 인사이트 (API 키 필요)
- **+Reddit**: SNS 트렌드 (API 키 필요)

---

## 🎯 단기 목표 (첫 30일)

### Week 1: 설정 및 검증
- [ ] GitHub Actions 첫 실행 성공
- [ ] Secrets 설정 완료
- [ ] GitHub Pages 활성화
- [ ] 첫 리포트 생성 확인

### Week 2: 데이터 축적
- [ ] 7일 연속 성공적인 수집
- [ ] 첫 Surge 신호 확인
- [ ] 키워드 세트 최적화

### Week 3-4: 분석 시작
- [ ] 30일 데이터 완성
- [ ] Baseline vs Recent 비교 분석
- [ ] 급상승 파라미터 튜닝

### Week 4+: 운영 및 활용
- [ ] 정기적인 리포트 리뷰
- [ ] 트렌드 기반 의사결정
- [ ] 추가 기능 탐색 (크로스 채널 분석 등)

---

## 📚 참고 문서

### 시작 가이드
- [QUICKSTART_GITHUB.md](QUICKSTART_GITHUB.md) - GitHub Actions 5분 배포
- [GITHUB_SETUP.md](GITHUB_SETUP.md) - GitHub 저장소 설정

### 사용 가이드
- [README.md](README.md) - 프로젝트 개요
- [docs/ANALYZERS.md](docs/ANALYZERS.md) - 급상승 감지 알고리즘
- [docs/COLLECTORS.md](docs/COLLECTORS.md) - 데이터 수집기 가이드

### 배포 및 운영
- [DEPLOYMENT.md](DEPLOYMENT.md) - 전체 배포 가이드
- [STATUS.md](STATUS.md) - 프로젝트 현황

---

## ✅ 체크리스트

지금 바로 확인:

- [ ] GitHub Repository 확인: https://github.com/YOUR_USERNAME/TrendRadar
- [ ] Secrets 설정 (NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)
- [ ] GitHub Pages 활성화
- [ ] Daily Trend Collection 워크플로 수동 실행
- [ ] 5분 후 결과 확인
- [ ] 리포트 URL 북마크

---

**축하합니다! TrendRadar가 이제 자동으로 실행됩니다!** 🎉

**리포트 URL**: `https://YOUR_USERNAME.github.io/TrendRadar/reports/`

매일 오전 9시에 자동으로 새로운 트렌드 데이터를 수집하고 리포트를 생성합니다.
