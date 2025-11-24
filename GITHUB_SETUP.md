# GitHub 저장소 생성 및 Push 가이드

## 📋 현재 상태

- ✅ 로컬 Git 저장소 초기화 완료
- ✅ 모든 파일 커밋 완료 (4 commits)
- ⏳ GitHub 원격 저장소 생성 필요

---

## 🚀 Step-by-Step 가이드

### Step 1: GitHub에서 저장소 생성

1. **[GitHub.com](https://github.com)에 로그인**

2. **새 저장소 생성**
   - 오른쪽 상단 "+" 클릭 > "New repository"
   - 또는 직접 URL: https://github.com/new

3. **저장소 설정**
   ```
   Repository name: TrendRadar
   Description: 트렌드를 레이더처럼 계속 보여주는 도구 - 급상승 키워드 자동 감지

   ⚪ Public (추천) - GitHub Actions 무료
   ⚪ Private - 비공개 (Actions는 제한적 무료)

   ❌ Add a README file (체크 해제 - 이미 있음)
   ❌ Add .gitignore (체크 해제 - 이미 있음)
   ❌ Choose a license (체크 해제 - 이미 있음)
   ```

4. **"Create repository" 클릭**

---

### Step 2: 로컬 저장소와 연결

GitHub가 보여주는 화면에서 **"...or push an existing repository from the command line"** 섹션의 명령어 사용:

```bash
cd D:\TrendRadar

# 원격 저장소 설정 (이미 설정되어 있음)
git remote add origin https://github.com/zzragida/TrendRadar.git

# 브랜치 이름 확인/변경
git branch -M main

# Push
git push -u origin main
```

**인증 요구 시**:
- Username: `zzragida`
- Password: **Personal Access Token** (비밀번호 아님!)

---

### Step 3: Personal Access Token 생성 (필요 시)

**비밀번호 대신 토큰 필요**:

1. **GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)**
   - 직접 URL: https://github.com/settings/tokens

2. **"Generate new token (classic)" 클릭**

3. **토큰 설정**:
   ```
   Note: TrendRadar Token
   Expiration: 90 days (또는 원하는 기간)

   Select scopes:
   ✅ repo (전체 선택)
   ✅ workflow
   ```

4. **"Generate token" 클릭**

5. **토큰 복사** (한 번만 표시됨!)
   ```
   ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```

6. **토큰을 비밀번호로 사용**:
   ```bash
   git push -u origin main
   Username: zzragida
   Password: [토큰_붙여넣기]
   ```

---

### Step 4: Push 성공 확인

**터미널 출력 예시**:
```
Enumerating objects: 65, done.
Counting objects: 100% (65/65), done.
Delta compression using up to 8 threads
Compressing objects: 100% (60/60), done.
Writing objects: 100% (65/65), 250.00 KiB | 5.00 MiB/s, done.
Total 65 (delta 10), reused 0 (delta 0)
To https://github.com/zzragida/TrendRadar.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

**GitHub에서 확인**:
- https://github.com/zzragida/TrendRadar
- 모든 파일과 커밋 히스토리 확인

---

## ✅ Push 완료 후 다음 단계

### 1. GitHub Secrets 설정 (2분)

**Repository > Settings > Secrets and variables > Actions**

**필수 Secrets**:
- `NAVER_CLIENT_ID`: 네이버 개발자센터에서 발급
- `NAVER_CLIENT_SECRET`: 네이버 개발자센터에서 발급

**발급 방법**:
1. https://developers.naver.com 접속
2. Application 등록
3. 검색 > 데이터랩(검색어 트렌드) 선택
4. Client ID, Secret 복사

### 2. GitHub Pages 활성화 (1분)

**Repository > Settings > Pages**
- Source: Deploy from a branch
- Branch: **gh-pages** / **/ (root)**
- Save

### 3. 첫 워크플로 실행 (1분)

**Repository > Actions 탭**
1. "Daily Trend Collection" 선택
2. "Run workflow" 클릭
3. Branch: main 선택
4. "Run workflow" 버튼 클릭

### 4. 결과 확인 (5분 후)

**리포트 URL**:
```
https://zzragida.github.io/TrendRadar/reports/
```

---

## 🔧 문제 해결

### Push 실패: Authentication failed

**원인**: Personal Access Token 필요

**해결**:
1. GitHub Settings > Developer settings > Personal access tokens
2. 새 토큰 생성 (repo, workflow 권한)
3. 토큰을 비밀번호로 사용

### Push 실패: Repository not found

**원인**: GitHub에 저장소가 없음

**해결**:
1. https://github.com/new에서 저장소 생성
2. 이름: `TrendRadar`
3. Public 선택
4. README 등 체크 해제
5. Create repository

### Push 실패: Permission denied

**원인**: SSH 키 미설정 또는 권한 없음

**해결**:
1. HTTPS URL 사용 확인: `https://github.com/zzragida/TrendRadar.git`
2. SSH 사용 시: SSH 키 설정 필요

---

## 📊 현재 커밋 히스토리

```bash
# 로컬 커밋 확인
cd D:\TrendRadar
git log --oneline --graph
```

**예상 출력**:
```
* 752b385 docs: Add GitHub Actions quick start guide
* a8302d6 docs: Update STATUS and README with deployment documentation
* 8fd0467 docs: Add deployment and contribution guides
* 8c3e680 feat: Complete Phase 1-2 implementation with analyzers and GitHub Actions
* e419dea Initial commit
```

**총 5개 커밋**, 모두 push될 예정

---

## 💡 Pro Tips

### 1. SSH 대신 HTTPS 사용 (권장)
```bash
# HTTPS (Personal Access Token)
git remote set-url origin https://github.com/zzragida/TrendRadar.git
```

### 2. 자격 증명 저장 (Windows)
```bash
# Git Credential Manager 사용
git config --global credential.helper manager-core

# 또는 일시 저장 (15분)
git config --global credential.helper cache
```

### 3. Force Push 피하기
```bash
# ❌ 절대 사용하지 말 것
git push --force

# ✅ 대신 이렇게
git pull origin main
git push origin main
```

---

## 📞 도움이 필요하신가요?

### GitHub 공식 문서
- [Creating a repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/creating-a-new-repository)
- [Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)
- [GitHub Actions](https://docs.github.com/en/actions)

### TrendRadar 문서
- [QUICKSTART_GITHUB.md](QUICKSTART_GITHUB.md) - GitHub Actions 빠른 시작
- [DEPLOYMENT.md](DEPLOYMENT.md) - 전체 배포 가이드
- [README.md](README.md) - 프로젝트 개요

---

## ✅ 체크리스트

완료한 항목에 체크:

- [ ] GitHub 계정 로그인
- [ ] TrendRadar 저장소 생성 (Public 권장)
- [ ] Personal Access Token 생성 (필요 시)
- [ ] `git push origin main` 성공
- [ ] GitHub에서 파일 확인
- [ ] GitHub Secrets 설정
- [ ] GitHub Pages 활성화
- [ ] 첫 워크플로 실행

**모두 완료하면 자동화 시작!** 🎉

---

**다음 문서**: [QUICKSTART_GITHUB.md](QUICKSTART_GITHUB.md)
