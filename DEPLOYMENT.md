# TrendRadar 배포 가이드

이 문서는 TrendRadar를 실제 환경에 배포하고 운영하는 방법을 설명합니다.

---

## 🚀 배포 방법

TrendRadar는 여러 방식으로 배포할 수 있습니다:

1. **GitHub Actions** (권장) - 무료, 자동화
2. **로컬 서버** - 완전한 제어
3. **클라우드 VM** - AWS EC2, GCP, Azure
4. **Docker** - 컨테이너 배포

---

## 1️⃣ GitHub Actions 배포 (권장)

### 장점
- ✅ 완전 무료
- ✅ GitHub Pages로 자동 리포트 배포
- ✅ 매일 자동 실행
- ✅ 유지보수 불필요

### 단계별 설정

#### Step 1: Repository Fork/Clone
```bash
# GitHub에서 Fork 또는
git clone https://github.com/<username>/TrendRadar.git
cd TrendRadar
git push -u origin main
```

#### Step 2: GitHub Secrets 설정

**Settings > Secrets and variables > Actions > New repository secret**

필수 Secrets:
- `NAVER_CLIENT_ID`: 네이버 개발자센터에서 발급
- `NAVER_CLIENT_SECRET`: 네이버 개발자센터에서 발급

선택 Secrets (필요한 경우):
- `YOUTUBE_API_KEY`: Google Cloud Console
- `REDDIT_CLIENT_ID`: Reddit App Settings
- `REDDIT_CLIENT_SECRET`: Reddit App Settings

#### Step 3: GitHub Pages 활성화

**Settings > Pages**
- **Source**: Deploy from a branch
- **Branch**: `gh-pages` / `/ (root)`
- **Save**

#### Step 4: 워크플로 실행

**Actions 탭에서 확인**
- `Daily Trend Collection`: 매일 오전 9시(KST) 자동 실행
- `Spike Analysis`: 수동 실행 (Run workflow 버튼)

#### Step 5: 결과 확인

리포트 URL:
```
https://<username>.github.io/TrendRadar/reports/
```

개별 리포트:
- 일일 리포트: `https://<username>.github.io/TrendRadar/reports/trend_YYYY-MM-DD.html`
- 급상승 리포트: `https://<username>.github.io/TrendRadar/reports/spike_YYYY-MM-DD.html`

---

## 2️⃣ 로컬 서버 배포

### 환경 준비

```bash
# 1. Repository Clone
git clone https://github.com/<username>/TrendRadar.git
cd TrendRadar

# 2. 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt
```

### 환경 변수 설정

`.env` 파일 생성:
```bash
# Naver DataLab (필수)
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret

# YouTube (선택)
YOUTUBE_API_KEY=your_api_key

# Reddit (선택)
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
```

`.env` 파일 로드:
```bash
# Linux/Mac
export $(cat .env | xargs)

# Windows PowerShell
Get-Content .env | ForEach-Object {
    $name, $value = $_.split('=')
    Set-Item -Path "env:$name" -Value $value
}
```

### 수동 실행

```bash
# 1회 실행 + 리포트 생성
python main.py --mode once --generate-report

# 결과 확인
ls -la docs/reports/
```

### Cron 자동화 (Linux/Mac)

```bash
# crontab 편집
crontab -e

# 매일 오전 9시 실행
0 9 * * * cd /path/to/TrendRadar && /path/to/venv/bin/python main.py --mode once --generate-report >> /var/log/trendradar.log 2>&1
```

### Task Scheduler 자동화 (Windows)

1. **작업 스케줄러** 열기
2. **기본 작업 만들기**
3. **트리거**: 매일 오전 9시
4. **작업**: 프로그램 시작
   - 프로그램: `C:\path\to\TrendRadar\venv\Scripts\python.exe`
   - 인수: `main.py --mode once --generate-report`
   - 시작 위치: `C:\path\to\TrendRadar`

---

## 3️⃣ 클라우드 VM 배포

### AWS EC2 예시

#### Step 1: EC2 인스턴스 생성
- **AMI**: Ubuntu 22.04 LTS
- **인스턴스 타입**: t2.micro (프리티어)
- **보안 그룹**: SSH (22) 허용

#### Step 2: 서버 설정

```bash
# SSH 접속
ssh -i your-key.pem ubuntu@your-ec2-ip

# 업데이트
sudo apt update && sudo apt upgrade -y

# Python 3.11 설치
sudo apt install python3.11 python3.11-venv python3-pip -y

# TrendRadar 설치
git clone https://github.com/<username>/TrendRadar.git
cd TrendRadar
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Step 3: 환경 변수 설정

```bash
# .env 파일 생성
nano .env
# (API 키 입력 후 저장)

# 환경 변수 로드
export $(cat .env | xargs)
```

#### Step 4: Systemd 서비스 생성

`/etc/systemd/system/trendradar.service`:
```ini
[Unit]
Description=TrendRadar Daily Collection
After=network.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/TrendRadar
Environment="NAVER_CLIENT_ID=your_id"
Environment="NAVER_CLIENT_SECRET=your_secret"
ExecStart=/home/ubuntu/TrendRadar/venv/bin/python main.py --mode once --generate-report

[Install]
WantedBy=multi-user.target
```

#### Step 5: Systemd Timer 생성

`/etc/systemd/system/trendradar.timer`:
```ini
[Unit]
Description=TrendRadar Daily Timer
Requires=trendradar.service

[Timer]
OnCalendar=daily
OnCalendar=09:00
Persistent=true

[Install]
WantedBy=timers.target
```

#### Step 6: 서비스 활성화

```bash
sudo systemctl daemon-reload
sudo systemctl enable trendradar.timer
sudo systemctl start trendradar.timer

# 상태 확인
sudo systemctl status trendradar.timer
sudo systemctl list-timers
```

---

## 4️⃣ Docker 배포

### Dockerfile 생성

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스 코드 복사
COPY . .

# 환경 변수 (빌드 시 전달)
ENV NAVER_CLIENT_ID=""
ENV NAVER_CLIENT_SECRET=""

# 데이터 디렉토리
VOLUME ["/app/data", "/app/docs/reports"]

# 기본 명령
CMD ["python", "main.py", "--mode", "once", "--generate-report"]
```

### Docker Compose

`docker-compose.yml`:
```yaml
version: '3.8'

services:
  trendradar:
    build: .
    environment:
      - NAVER_CLIENT_ID=${NAVER_CLIENT_ID}
      - NAVER_CLIENT_SECRET=${NAVER_CLIENT_SECRET}
      - YOUTUBE_API_KEY=${YOUTUBE_API_KEY}
      - REDDIT_CLIENT_ID=${REDDIT_CLIENT_ID}
      - REDDIT_CLIENT_SECRET=${REDDIT_CLIENT_SECRET}
    volumes:
      - ./data:/app/data
      - ./docs/reports:/app/docs/reports
    restart: unless-stopped
```

### 실행

```bash
# 빌드
docker-compose build

# 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 수동 실행
docker-compose run --rm trendradar python main.py --mode once --generate-report
```

### Cron으로 Docker 스케줄링

```bash
# crontab -e
0 9 * * * cd /path/to/TrendRadar && docker-compose run --rm trendradar
```

---

## 📊 모니터링 및 운영

### 1. 로그 관리

#### GitHub Actions
- **Actions 탭** > 워크플로 선택 > 로그 확인

#### 로컬/서버
```bash
# 로그 파일로 출력
python main.py --mode once --generate-report > trendradar.log 2>&1

# 실시간 로그
tail -f trendradar.log
```

### 2. 데이터베이스 백업

```bash
# DuckDB 백업
cp data/trendradar.duckdb data/trendradar_backup_$(date +%Y%m%d).duckdb

# S3 백업 (AWS CLI)
aws s3 cp data/trendradar.duckdb s3://your-bucket/backups/trendradar_$(date +%Y%m%d).duckdb

# 자동 백업 스크립트 (cron)
0 2 * * * /path/to/backup_script.sh
```

`backup_script.sh`:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)
DB_PATH="/path/to/TrendRadar/data/trendradar.duckdb"
BACKUP_DIR="/path/to/backups"

# 로컬 백업
cp "$DB_PATH" "$BACKUP_DIR/trendradar_$DATE.duckdb"

# 7일 이상 된 백업 삭제
find "$BACKUP_DIR" -name "trendradar_*.duckdb" -mtime +7 -delete
```

### 3. 에러 알림

#### 이메일 알림 (Linux)

```bash
# mailutils 설치
sudo apt install mailutils -y

# 실행 시 에러 이메일 전송
python main.py --mode once --generate-report 2>&1 | mail -s "TrendRadar Error" your@email.com
```

#### Slack 웹훅

```python
# main.py에 추가
import requests

SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

def send_slack_alert(message):
    requests.post(SLACK_WEBHOOK, json={"text": message})

# 에러 발생 시
try:
    run_once(...)
except Exception as e:
    send_slack_alert(f"TrendRadar Error: {e}")
    raise
```

### 4. 성능 모니터링

```bash
# 실행 시간 측정
time python main.py --mode once

# 메모리 사용량
/usr/bin/time -v python main.py --mode once

# DuckDB 크기 확인
du -h data/trendradar.duckdb
```

---

## 🔧 트러블슈팅

### 문제 1: Rate Limit 초과

**증상**: `429 Too Many Requests` 에러

**해결**:
```python
# config/keyword_sets.yaml에서 키워드 수 줄이기
keywords:
  - "키워드1"
  - "키워드2"
  # 10-20개 권장

# 또는 수집 간격 늘리기
# cron: 0 */6 * * * (6시간마다)
```

### 문제 2: 메모리 부족

**증상**: `MemoryError` 또는 프로세스 종료

**해결**:
```bash
# swap 메모리 추가 (Linux)
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 또는 키워드 배치 처리
# config/keyword_sets.yaml을 여러 파일로 분할
```

### 문제 3: API 키 만료

**증상**: `401 Unauthorized` 에러

**해결**:
1. 네이버 개발자센터에서 키 재발급
2. GitHub Secrets 또는 .env 업데이트
3. 서비스 재시작

### 문제 4: 데이터베이스 손상

**증상**: `duckdb.IOException` 에러

**해결**:
```bash
# 백업에서 복구
cp data/trendradar_backup_YYYYMMDD.duckdb data/trendradar.duckdb

# 또는 재생성 (데이터 손실)
rm data/trendradar.duckdb
python main.py --mode once --generate-report
```

---

## 📈 스케일링

### 수평 확장 (여러 인스턴스)

```yaml
# docker-compose-scale.yml
version: '3.8'

services:
  trendradar-google:
    build: .
    environment:
      - NAVER_CLIENT_ID=${NAVER_CLIENT_ID}
    command: python main.py --mode once --source google
    volumes:
      - ./data:/app/data

  trendradar-naver:
    build: .
    environment:
      - NAVER_CLIENT_ID=${NAVER_CLIENT_ID}
    command: python main.py --mode once --source naver
    volumes:
      - ./data:/app/data
```

### 분산 처리

```python
# 키워드 세트 분할
# config/keyword_sets_1.yaml
# config/keyword_sets_2.yaml

# 각각 다른 시간에 실행
# Cron 1: 0 9 * * * (9시)
# Cron 2: 0 15 * * * (15시)
```

---

## 🔐 보안 권장사항

### 1. API 키 관리
- ❌ 코드에 하드코딩 금지
- ✅ 환경 변수 또는 Secrets 사용
- ✅ `.env` 파일을 `.gitignore`에 추가

### 2. 데이터베이스 보안
```bash
# 파일 권한 제한
chmod 600 data/trendradar.duckdb
chmod 600 .env
```

### 3. 서버 보안 (클라우드 배포 시)
- SSH 키 인증만 허용 (비밀번호 비활성화)
- 방화벽 설정 (UFW/Security Group)
- 정기 업데이트

---

## ✅ 배포 체크리스트

배포 전 확인사항:

- [ ] Python 3.11+ 설치
- [ ] `requirements.txt` 의존성 설치
- [ ] API 키 발급 및 설정
- [ ] `config/keyword_sets.yaml` 커스터마이징
- [ ] 테스트 실행 (`python test_basic.py`)
- [ ] 1회 수동 실행 확인
- [ ] 로그 파일 경로 설정
- [ ] 백업 스크립트 설정
- [ ] 모니터링 알림 설정 (선택)
- [ ] 문서 읽기 (`README.md`, `STATUS.md`)

GitHub Actions 배포:
- [ ] Repository Fork/Clone
- [ ] GitHub Secrets 설정
- [ ] GitHub Pages 활성화
- [ ] 워크플로 수동 실행 테스트
- [ ] 리포트 URL 확인

---

## 📞 지원

문제가 발생하면:
1. [TESTING_RESULTS.md](TESTING_RESULTS.md) 참고
2. [GitHub Issues](https://github.com/<username>/TrendRadar/issues) 생성
3. [Discussions](https://github.com/<username>/TrendRadar/discussions) 질문

---

**Happy Deploying! 🚀**
