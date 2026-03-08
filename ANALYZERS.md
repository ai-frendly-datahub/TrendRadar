# TrendRadar Analyzers 가이드

## 개요

Analyzers는 수집된 트렌드 데이터를 분석하여 **급상승 키워드 감지**, **채널 간 비교**, **패턴 인식** 등의 인사이트를 제공합니다.

> "레이더처럼 계속 신호를 포착하는" TrendRadar의 핵심 기능입니다.

## 📦 구현된 Analyzers

### 1. Spike Detector (급상승 감지기)
**파일:** [analyzers/spike_detector.py](../analyzers/spike_detector.py)

트렌드가 급격히 상승하는 키워드를 자동으로 감지합니다.

#### 감지 유형

##### 🔥 Surge (급상승)
최근 7일 평균이 직전 30일 평균 대비 크게 증가

**알고리즘:**
```
spike_ratio = recent_avg / baseline_avg
if spike_ratio >= 1.5:
    → SURGE 신호 발생
```

**사용 사례:**
- 시즌성 이벤트 (블랙프라이데이, 크리스마스)
- 갑작스런 이슈 (뉴스, 사건)
- 마케팅 캠페인 효과

##### 🌟 Emerging (신규 등장)
과거에는 낮았지만 최근 갑자기 나타남

**알고리즘:**
```
if current_value >= 30 and baseline_value <= 5:
    → EMERGING 신호 발생
```

**사용 사례:**
- 새로운 제품/서비스 출시
- 신조어, 밈(Meme) 등장
- 새로운 트렌드 시작

##### 💥 Viral (바이럴)
짧은 기간 동안 폭발적으로 증가

**알고리즘:**
```
growth_rate = recent_3days_avg / early_3days_avg
if growth_rate >= 2.0:
    → VIRAL 신호 발생
```

**사용 사례:**
- 소셜미디어 바이럴
- 돌발 이슈
- 인플루언서 효과

#### 사용 예시

```python
from analyzers.spike_detector import SpikeDetector
from pathlib import Path

detector = SpikeDetector(
    db_path=Path("data/trendradar.duckdb"),
    recent_days=7,
    baseline_days=30
)

# 1. 급상승 키워드 감지
surge_signals = detector.detect_surge_keywords(
    source="naver",  # 또는 "google", None=전체
    min_ratio=1.5,   # 1.5배 이상
    min_baseline=10.0
)

for signal in surge_signals[:10]:
    print(f"{signal.keyword}: {signal.spike_ratio:.2f}x")
    print(f"  현재: {signal.current_value:.1f}")
    print(f"  기준: {signal.baseline_value:.1f}")
    print(f"  점수: {signal.spike_score:.1f}/100")

# 2. 신규 등장 키워드
emerging = detector.detect_emerging_keywords(
    min_current=30.0,
    max_baseline=5.0
)

# 3. 바이럴 키워드
viral = detector.detect_viral_keywords(
    window_days=3,
    min_growth_rate=2.0
)

# 4. 전체 통합 (한 번에)
all_spikes = detector.detect_all_spikes(
    source=None,
    top_n=20
)
# {'surge': [...], 'emerging': [...], 'viral': [...]}
```

#### Spike Score 계산

급상승 점수는 0-100점으로 계산됩니다:

```python
spike_score = (
    ratio_score     # 증가율 (최대 50점)
    + absolute_score  # 절대값 (최대 30점)
    + increase_score  # 증가량 (최대 20점)
)
```

**해석:**
- 90-100: 매우 강한 급상승
- 70-89: 강한 급상승
- 50-69: 중간 급상승
- 30-49: 약한 급상승

---

### 2. Cross-Channel Analyzer (크로스 채널 분석기)
**파일:** [analyzers/cross_channel_analyzer.py](../analyzers/cross_channel_analyzer.py)

여러 채널의 트렌드를 비교하여 격차와 패턴을 발견합니다.

#### 주요 기능

##### ⚖️ Channel Gap (채널 격차)
한 채널에서는 뜨는데 다른 채널에서는 안 뜨는 키워드

**사용 사례:**
- YouTube에서는 인기인데 검색은 안 되는 콘텐츠
- 글로벌(Google)은 뜨는데 한국(Naver)은 안 뜨는 트렌드
- 플랫폼별 사용자 특성 차이 파악

```python
from analyzers.cross_channel_analyzer import CrossChannelAnalyzer

analyzer = CrossChannelAnalyzer(db_path=Path("data/trendradar.duckdb"))

# Google vs Naver 격차
gaps = analyzer.find_channel_gaps(
    channel1="google",
    channel2="naver",
    days=30,
    min_gap=2.0  # 2배 이상 차이
)

for gap in gaps[:10]:
    print(f"{gap.keyword}:")
    print(f"  {gap.leading_channel}: {gap.leading_value:.1f}")
    print(f"  {gap.lagging_channel}: {gap.lagging_value:.1f}")
    print(f"  격차: {gap.gap_ratio:.2f}x")
    print(f"  💡 {gap.insight}")
```

##### 🔍 Exclusive Keywords (독점 키워드)
특정 채널에만 나타나는 키워드

```python
# YouTube에만 있는 키워드
exclusive = analyzer.find_exclusive_keywords(
    channel="youtube",
    exclude_channels=["google", "naver"],
    days=30,
    min_value=30.0
)

for kw in exclusive[:10]:
    print(f"{kw['keyword']}: {kw['value']:.1f}")
```

##### 📊 Multi-Channel Comparison (다중 채널 비교)

```python
comparison = analyzer.compare_channels(
    channels=["google", "naver", "youtube"],
    days=30
)

print(f"전체 유니크 키워드: {comparison['total_unique_keywords']}")
print(f"공통 키워드: {comparison['common_count']}")

for channel, data in comparison["channels"].items():
    print(f"\n{channel}:")
    print(f"  키워드 수: {data['total_keywords']}")
    print(f"  평균 값: {data['avg_value']:.1f}")
    print(f"  Top 5: {data['top_keywords'][:5]}")
```

---

## 🎯 실전 활용 시나리오

### 시나리오 1: 마케팅 캠페인 모니터링

```python
detector = SpikeDetector(db_path=db_path)

# 캠페인 키워드 급상승 감지
campaign_keywords = ["브랜드명", "제품명", "이벤트명"]

surge = detector.detect_surge_keywords(source="naver")

campaign_spikes = [
    s for s in surge
    if s.keyword in campaign_keywords
]

if campaign_spikes:
    print("🎉 캠페인 효과 감지!")
    for s in campaign_spikes:
        print(f"  {s.keyword}: {s.spike_ratio:.2f}x 증가")
```

### 시나리오 2: 채널별 콘텐츠 전략

```python
analyzer = CrossChannelAnalyzer(db_path=db_path)

# YouTube vs 검색 격차
gaps = analyzer.find_channel_gaps("youtube", "google")

youtube_leads = [g for g in gaps if g.leading_channel == "youtube"]

print("📹 YouTube에서 선행 중인 트렌드:")
for gap in youtube_leads[:5]:
    print(f"  {gap.keyword} - 검색보다 {gap.gap_ratio:.1f}배 높음")
    print(f"  → 검색 최적화(SEO) 기회!")
```

### 시나리오 3: 신규 트렌드 조기 발견

```python
detector = SpikeDetector(db_path=db_path)

# 신규 등장 + 바이럴 조합
emerging = detector.detect_emerging_keywords()
viral = detector.detect_viral_keywords()

# 두 조건 모두 만족하는 키워드 = 강력한 신호
emerging_keywords = {s.keyword for s in emerging}
viral_keywords = {s.keyword for s in viral}

hot_new_trends = emerging_keywords & viral_keywords

print("🔥 조기 발견된 강력한 신규 트렌드:")
for keyword in hot_new_trends:
    print(f"  • {keyword}")
```

---

## 📈 데이터 요구사항

Analyzer가 제대로 작동하려면:

### 최소 요구사항
- **데이터 수집 기간**: 최소 30일
- **데이터 포인트**: 키워드당 최소 20개 이상
- **키워드 수**: 10개 이상 권장

### 권장 사항
- **정기 수집**: 매일 또는 주 3회 이상
- **다중 채널**: 2개 이상 채널 (Google + Naver)
- **키워드 세트**: 관심 분야별로 구성

### 데이터 수집 예시

```bash
# 매일 자동 수집 (스케줄러)
python main.py --mode scheduler --interval 24

# 또는 GitHub Actions로 자동화
# .github/workflows/daily_collect.yml
```

---

## 🧪 테스트 및 예제

### 예제 실행

```bash
# Analyzer 데모
python examples/analyzer_example.py
```

**출력 예시:**
```
🔥 급상승 키워드 감지
=================================================
📈 1. 급상승 키워드 (Surge)
발견된 급상승 키워드: 15개

1. 크리스마스 (naver)
   📊 현재: 87.3 | 기준: 42.1 | 증가율: 2.07x
   ⭐ 급상승 점수: 78.5/100

2. 선물 (google)
   📊 현재: 65.8 | 기준: 38.2 | 증가율: 1.72x
   ⭐ 급상승 점수: 62.3/100
```

### 단위 테스트

```bash
pytest tests/unit/test_analyzers.py
```

---

## 🚀 다음 단계

### 구현 예정 기능

1. **시계열 예측**
   - ARIMA 모델로 미래 트렌드 예측
   - 계절성 패턴 자동 감지

2. **키워드 클러스터링**
   - 연관 키워드 그룹화
   - 토픽 모델링 (LDA)

3. **감성 분석** (SNS 데이터)
   - Reddit/Twitter 게시글 감성 분석
   - 긍정/부정 트렌드 파악

4. **이상 탐지**
   - 비정상적인 패턴 감지
   - 데이터 품질 모니터링

---

## 📚 참고 자료

- [Spike Detection Algorithm 논문](https://en.wikipedia.org/wiki/Anomaly_detection)
- [Time Series Analysis Best Practices](https://www.tensorflow.org/tutorials/structured_data/time_series)
- [TrendRadar 아키텍처](ARCHITECTURE.md)
- [데이터 소스 전략](DATA_SOURCES.md)
