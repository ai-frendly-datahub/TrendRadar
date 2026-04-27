# Data Quality Plan

- 생성 시각: `2026-04-23T14:45:24.863320+00:00`
- 우선순위: `P1`
- 데이터 품질 점수: `90`
- 가장 약한 축: `추적성`
- Governance: `low`
- Primary Motion: `attention`

## 현재 이슈

- 현재 설정상 즉시 차단 이슈 없음. 운영 지표와 freshness SLA만 명시하면 됨

## 필수 신호

- 검색량·트렌딩·조회수 같은 선행 관심 신호
- 쇼핑·구매·가입·방문 같은 후행 conversion proxy
- vertical keyword pack과 카테고리 taxonomy

## 품질 게이트

- keyword pack 버전과 생성 기준을 추적
- 관심 신호와 전환 신호를 같은 점수로 병합하지 않음
- 플랫폼별 trend scale 차이를 정규화한 뒤 비교

## 다음 구현 순서

- 새 data_quality 계약을 기준으로 `docs/reports/trend_quality.json` 산출물을 매일 확인
- signup·visit 같은 conversion proxy 후보를 ToS와 개인정보 검토 후 단계적으로 활성화
- attention score와 conversion proxy score를 dashboard에서 별도 축으로 노출

## 운영 규칙

- 원문 URL, 수집일, 이벤트 발생일은 별도 필드로 유지한다.
- 공식 source와 커뮤니티/시장 source를 같은 신뢰 등급으로 병합하지 않는다.
- collector가 인증키나 네트워크 제한으로 skip되면 실패를 숨기지 말고 skip 사유를 기록한다.
- 이 문서는 `scripts/build_data_quality_review.py --write-repo-plans`로 재생성한다.
