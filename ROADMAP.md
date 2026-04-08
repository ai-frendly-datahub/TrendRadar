# TrendRadar 품질 개선 로드맵

> 트렌드 분석 레이더 아키텍처 결정 및 통합 계획
>
> 마지막 업데이트: 2026-04-08

---

## 1. 현재 상태 (Current Status)

| 지표 | 현재 값 | 목표 값 |
|------|---------|---------|
| 데이터 신선도 | N/A (아키텍처 미결정) | 24시간 이내 |
| 활성 소스 수 | 0개 (config만 존재) | 5개 이상 |
| 매칭률 | N/A | 60% 이상 |
| radar-core 통합 | 미통합 (별도 아키텍처) | 결정 필요 |

### 아키텍처 현황
TrendRadar는 다른 Radar 프로젝트들과 **다른 아키텍처**를 사용하고 있습니다:
- 자체 collector/analyzer/reporter 구조
- keyword_sets.yaml 기반 설정 (categories/ 아님)
- 자체 MCP 서버 구현
- 자체 storage 모듈

### 주요 모듈
| 모듈 | 설명 | 상태 |
|------|------|------|
| collectors/ | 12개 플랫폼 수집기 | 구현됨 |
| analyzers/ | 스파이크 감지, 크로스 분석 | 구현됨 |
| reporters/ | HTML, 상관관계, 예측 | 구현됨 |
| mcp_server/ | Claude Desktop 연동 | 구현됨 |
| storage/ | DuckDB 저장소 | 구현됨 |

### 지원 플랫폼 (12개)
- 네이버 검색/쇼핑, 구글 트렌드, 유튜브
- Reddit, HackerNews, StackExchange, Dev.to
- Product Hunt, Wikipedia, Threads, Daum 뉴스, 브라우저

---

## 2. P0 긴급 (This Week)

> 즉시 수정해야 할 이슈 - 아키텍처 결정

### P0-1: 아키텍처 방향 결정
- [ ] radar-core 통합 vs 독립 유지 결정
- [ ] 장단점 분석 문서 작성
- [ ] 팀 리뷰 및 최종 결정

#### Option A: radar-core 통합
- 장점: 일관된 코드베이스, 공통 기능 재사용
- 단점: 마이그레이션 비용, 기능 손실 가능성

#### Option B: 독립 유지 + 문서화
- 장점: 현재 기능 유지, 마이그레이션 비용 없음
- 단점: 코드 중복, 별도 유지보수 필요

### P0-2: 현재 상태 문서화
- [ ] ARCHITECTURE.md 작성
- [ ] 각 모듈 역할 및 의존성 정리
- [ ] API 문서화 (collectors, analyzers)

### P0-3: 기본 테스트 수행
- [ ] 각 collector 동작 테스트
- [ ] 에러 발생 소스 비활성화
- [ ] 테스트 결과 문서화

---

## 3. P1 중요 (2 Weeks)

> 중요하지만 긴급하지 않은 개선사항 - 통합 또는 안정화

### P1-1: Option A 선택 시 - radar-core 통합
- [ ] TrendRadar collector를 radar-core 포맷으로 변환
- [ ] keyword_sets.yaml을 categories/ 구조로 마이그레이션
- [ ] 기존 analyzer 기능을 radar-core에 포팅
- [ ] reporter를 radar-core 템플릿 기반으로 전환

### P1-2: Option B 선택 시 - 독립 고도화
- [ ] ARCHITECTURE.md 완성
- [ ] 자체 CI/CD 워크플로우 설정
- [ ] 데일리 수집 파이프라인 구축
- [ ] 리포트 자동 생성 설정

### P1-3: 공통 - 소스 활성화
- [ ] 네이버 검색 트렌드 API 키 설정
- [ ] 구글 트렌드 collector 테스트
- [ ] Reddit API 키 설정
- [ ] 최소 5개 소스 활성화

---

## 4. P2 개선 (1 Month)

> 장기 개선 과제 - 고급 분석 기능

### P2-1: 크로스-레이더 트렌드 분석
- [ ] 다른 Radar들의 entity와 TrendRadar 트렌드 연계
- [ ] 상관관계 분석 모듈 개발
- [ ] 예측 모델 고도화

### P2-2: 실시간 트렌드 감지
- [ ] 스파이크 감지 알고리즘 개선
- [ ] 실시간 알림 시스템 구축
- [ ] 트렌드 예측 정확도 향상

### P2-3: 시각화 고도화
- [ ] 트렌드 히트맵 개선
- [ ] 크로스-플랫폼 비교 차트
- [ ] 인터랙티브 대시보드

---

## 5. 체크리스트

### P0 완료 기준 (This Week)
- [ ] 아키텍처 방향 결정 (A 또는 B)
- [ ] 결정 근거 문서화
- [ ] 기존 코드 동작 상태 확인
- [ ] 다음 단계 계획 수립

### P1 완료 기준 (2 Weeks)
- [ ] 선택한 방향에 따른 초기 구현
- [ ] 최소 5개 소스 활성화
- [ ] 일일 수집 파이프라인 가동
- [ ] 기본 리포트 생성

### P2 완료 기준 (1 Month)
- [ ] 크로스-레이더 분석 가능
- [ ] 트렌드 예측 기능 동작
- [ ] 시각화 대시보드 완성

---

## 기술 부채 (Tech Debt)

### 높은 우선순위
1. 중복 코드 정리 (collectors 간 공통 로직)
2. 테스트 커버리지 향상
3. 에러 핸들링 표준화

### 중간 우선순위
1. 타입 힌트 추가
2. 로깅 표준화
3. 설정 파일 구조 통일

---

## 관련 문서
- [config/keyword_sets.yaml](./config/keyword_sets.yaml)
- [main.py](./main.py)
- [collectors/](./collectors/)
