"""TrendRadar 메인 실행 스크립트."""

from __future__ import annotations

import argparse
import os
import time
from datetime import UTC, datetime
from pathlib import Path

import yaml

from analyzers.spike_detector import SpikeDetector
from collectors.browser_collector import BrowserCollector
from collectors.devto_collector import DevtoCollector
from collectors.google_collector import GoogleTrendsCollector
from collectors.google_trending_collector import GoogleTrendingCollector
from collectors.hackernews_collector import HackerNewsCollector
from collectors.naver_collector import NaverDataLabCollector
from collectors.naver_shopping_collector import NaverShoppingCollector
from collectors.producthunt_collector import ProductHuntCollector
from collectors.reddit_collector import RedditCollector
from collectors.stackexchange_collector import StackExchangeCollector
from collectors.wikipedia_collector import WikipediaPageviewsCollector
from collectors.youtube_collector import YouTubeTrendingCollector
from config_loader import load_notification_config
from notifier import Notifier, PipelineNotifier, detect_trend_notifications
from raw_logger import RawLogger
from reporters.html_reporter import generate_daily_report
from reporters.spike_reporter import generate_spike_report
from storage import trend_store
from storage.search_index import SearchIndex
from trendradar.common.validators import validate_keyword, validate_score
from trendradar.models import (
    ContentItem,
    KeywordSet,
    TrendCollectionResult,
    TrendPoint,
    TrendRadarSettings,
)


CONFIG_ENV_VAR = "TRENDRADAR_CONFIG_PATH"
PROJECT_ROOT = Path(__file__).resolve().parent
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "keyword_sets.yaml"
DEFAULT_SETTINGS = TrendRadarSettings()
DEFAULT_REPORT_DIR = PROJECT_ROOT / DEFAULT_SETTINGS.report_dir
DEFAULT_RAW_DIR = PROJECT_ROOT / DEFAULT_SETTINGS.raw_data_dir
DEFAULT_SEARCH_DB_PATH = PROJECT_ROOT / DEFAULT_SETTINGS.search_db_path
DEFAULT_NOTIFICATION_CONFIG_PATH = PROJECT_ROOT / DEFAULT_SETTINGS.notification_config_path
DEFAULT_DB_PATH = PROJECT_ROOT / DEFAULT_SETTINGS.database_path

CORE_SOURCE_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "naver": ("NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"),
    "google": (),
    "google_trending": (),
    "wikipedia": (),
    "reddit": ("REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET"),
    "youtube": ("YOUTUBE_API_KEY",),
    "naver_shopping": ("NAVER_CLIENT_ID", "NAVER_CLIENT_SECRET"),
}
CORE_SOURCE_LABELS: dict[str, str] = {
    "naver": "Naver DataLab",
    "google": "Google Trends",
    "google_trending": "Google Trending",
    "wikipedia": "Wikipedia Pageviews",
    "reddit": "Reddit Trending",
    "youtube": "YouTube Trending",
    "naver_shopping": "Naver Shopping",
}
TOTAL_CORE_SOURCES = len(CORE_SOURCE_REQUIREMENTS)


def _missing_required_env_vars(env_vars: tuple[str, ...]) -> list[str]:
    return [env_var for env_var in env_vars if not os.environ.get(env_var)]


def get_core_source_availability() -> dict[str, tuple[bool, list[str]]]:
    availability: dict[str, tuple[bool, list[str]]] = {}
    for source_name, env_vars in CORE_SOURCE_REQUIREMENTS.items():
        missing_env_vars = _missing_required_env_vars(env_vars)
        availability[source_name] = (len(missing_env_vars) == 0, missing_env_vars)
    return availability


def _print_core_source_availability_report(
    source_availability: dict[str, tuple[bool, list[str]]],
) -> None:
    print(f"  - 소스 준비 상태 (핵심 {TOTAL_CORE_SOURCES}개):")
    for source_name in CORE_SOURCE_REQUIREMENTS:
        source_label = CORE_SOURCE_LABELS.get(source_name, source_name)
        is_available, missing_env_vars = source_availability[source_name]
        if is_available:
            print(f"    - {source_label}: ready")
            continue

        missing_vars_text = ", ".join(missing_env_vars)
        print(f"    - {source_label}: skipped (missing env: {missing_vars_text})")


def _is_source_available(
    source_name: str,
    source_availability: dict[str, tuple[bool, list[str]]] | None,
) -> tuple[bool, list[str]]:
    if source_availability is None:
        return True, []
    return source_availability.get(source_name, (True, []))


def _filter_valid_points(
    *,
    keyword: str,
    points: list[TrendPoint],
    source: str,
    errors: list[str],
) -> list[TrendPoint]:
    if not validate_keyword(keyword):
        errors.append(f"{source}: invalid keyword '{keyword}'")
        return []

    valid_points: list[TrendPoint] = []
    for point in points:
        date_str = point.timestamp.date().isoformat()
        if not date_str:
            errors.append(f"{source}: missing date for keyword '{keyword}'")
            continue

        try:
            score = float(point.value)
        except (TypeError, ValueError):
            errors.append(f"{source}: invalid score for keyword '{keyword}'")
            continue

        if not validate_score(score):
            errors.append(f"{source}: negative score for keyword '{keyword}'")
            continue

        valid_points.append(
            TrendPoint(
                keyword=keyword,
                source=source,
                timestamp=point.timestamp,
                value=score,
                metadata=point.metadata,
            )
        )

    return valid_points


def _build_raw_records(
    *,
    keyword: str,
    source: str,
    points: list[TrendPoint],
) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for point in points:
        date_str = point.timestamp.date().isoformat()
        if not date_str:
            continue
        records.append(
            {
                "keyword": keyword,
                "platform": source,
                "value": float(point.value),
                "timestamp": date_str,
            }
        )
    return records


def _build_content_raw_record(
    *,
    keyword: str,
    source: str,
    score: float,
    timestamp: str,
) -> dict[str, object]:
    return {
        "keyword": keyword,
        "platform": source,
        "value": score,
        "timestamp": timestamp,
    }


def _sync_keyword_to_search_index(
    *,
    search_index: SearchIndex,
    keyword: str,
    source: str,
    keyword_set: KeywordSet,
) -> None:
    related_keywords = [k for k in keyword_set.keywords if k != keyword]
    set_name = keyword_set.name
    context_parts = [
        f"set:{set_name}",
        f"source:{source}",
        f"related:{', '.join(related_keywords[:10])}" if related_keywords else "related:",
    ]
    search_index.upsert(keyword=keyword, platform=source, context=" | ".join(context_parts))


def load_keyword_sets_config(path: Path | None = None) -> list[KeywordSet]:
    """keyword_sets.yaml 로드."""
    config_path = Path(path or os.environ.get(CONFIG_ENV_VAR, DEFAULT_CONFIG_PATH))
    with config_path.open(encoding="utf-8") as fp:
        config = yaml.safe_load(fp)

    if not isinstance(config, dict):
        return []

    keyword_sets = config.get("keyword_sets", [])
    if not isinstance(keyword_sets, list):
        return []

    return [KeywordSet.from_dict(item) for item in keyword_sets if isinstance(item, dict)]


def collect_trends(
    keyword_set: KeywordSet,
    *,
    db_path: Path | None = None,
    source_filter: str | None = None,
    raw_logger: RawLogger | None = None,
    search_index: SearchIndex | None = None,
    source_availability: dict[str, tuple[bool, list[str]]] | None = None,
    successful_core_sources: set[str] | None = None,
) -> tuple[int, int, list[str]]:
    """Collect trend data from configured sources and persist them."""
    total_points = 0
    sources_succeeded = 0
    errors: list[str] = []

    def mark_core_source_success(source_name: str) -> None:
        if successful_core_sources is not None and source_name in CORE_SOURCE_REQUIREMENTS:
            successful_core_sources.add(source_name)

    keywords = keyword_set.keywords
    channels = keyword_set.channels or ["naver", "google"]
    time_range = keyword_set.time_range
    filters = keyword_set.filters
    start_date = time_range.get("start") or str(datetime.now(UTC).date())
    end_date = time_range.get("end") or str(datetime.now(UTC).date())

    # Naver DataLab
    if "naver" in channels and (source_filter is None or source_filter == "naver"):
        source_ready, missing_env_vars = _is_source_available("naver", source_availability)
        if not source_ready:
            missing_vars_text = ", ".join(missing_env_vars)
            print(f"  - Naver DataLab skipped: missing env vars ({missing_vars_text})")
        else:
            try:
                naver_collector = NaverDataLabCollector(
                    client_id=os.environ.get("NAVER_CLIENT_ID"),
                    client_secret=os.environ.get("NAVER_CLIENT_SECRET"),
                )

                naver_data = naver_collector.collect(
                    keywords=keywords,
                    start_date=start_date,
                    end_date=end_date,
                    time_unit=filters.get("time_unit", "date"),
                    device=filters.get("device"),
                    gender=filters.get("gender"),
                    ages=filters.get("ages"),
                )

                naver_raw_records: list[dict[str, object]] = []
                for keyword, points in naver_data.items():
                    valid_points = _filter_valid_points(
                        keyword=keyword,
                        points=points,
                        source="naver",
                        errors=errors,
                    )
                    if not valid_points:
                        continue

                    trend_store.save_trend_points(
                        source="naver",
                        keyword=keyword,
                        points=valid_points,
                        metadata={
                            "set_name": keyword_set.name,
                            "filters": filters,
                        },
                        db_path=db_path,
                    )
                    total_points += len(valid_points)
                    naver_raw_records.extend(
                        _build_raw_records(keyword=keyword, source="naver", points=valid_points)
                    )
                    if search_index is not None:
                        _sync_keyword_to_search_index(
                            search_index=search_index,
                            keyword=keyword,
                            source="naver",
                            keyword_set=keyword_set,
                        )

                if raw_logger is not None and naver_raw_records:
                    raw_path = raw_logger.log(naver_raw_records, source_name="naver")
                    print(f"  - Raw JSONL logged: {raw_path}")

                sources_succeeded += 1
                mark_core_source_success("naver")
                print(f"  - Naver DataLab: {len(naver_data)} keywords, {total_points} points")

            except Exception as e:
                errors.append(f"Naver DataLab: {str(e)[:100]}")
                print(f"  - Naver DataLab failed: {e}")

    # Google Trends
    if "google" in channels and (source_filter is None or source_filter == "google"):
        source_ready, missing_env_vars = _is_source_available("google", source_availability)
        if not source_ready:
            missing_vars_text = ", ".join(missing_env_vars)
            print(f"  - Google Trends skipped: missing env vars ({missing_vars_text})")
        else:
            try:
                google_collector = GoogleTrendsCollector()

                google_data = google_collector.collect(
                    keywords=keywords,
                    geo=filters.get("geo", "KR"),
                    timeframe=f"{start_date} {end_date}",
                )

                google_points = 0
                google_raw_records: list[dict[str, object]] = []
                for keyword, points in google_data.items():
                    valid_points = _filter_valid_points(
                        keyword=keyword,
                        source="google",
                        points=points,
                        errors=errors,
                    )
                    if not valid_points:
                        continue

                    trend_store.save_trend_points(
                        source="google",
                        keyword=keyword,
                        points=valid_points,
                        metadata={
                            "set_name": keyword_set.name,
                            "geo": filters.get("geo", "KR"),
                        },
                        db_path=db_path,
                    )
                    google_points += len(valid_points)
                    google_raw_records.extend(
                        _build_raw_records(keyword=keyword, source="google", points=valid_points)
                    )
                    if search_index is not None:
                        _sync_keyword_to_search_index(
                            search_index=search_index,
                            keyword=keyword,
                            source="google",
                            keyword_set=keyword_set,
                        )

                if raw_logger is not None and google_raw_records:
                    raw_path = raw_logger.log(google_raw_records, source_name="google")
                    print(f"  - Raw JSONL logged: {raw_path}")

                total_points += google_points
                sources_succeeded += 1
                mark_core_source_success("google")
                print(f"  - Google Trends: {len(google_data)} keywords, {google_points} points")

            except Exception as e:
                errors.append(f"Google Trends: {str(e)[:100]}")
                print(f"  - Google Trends failed: {e}")

    # Google Trending (daily/realtime)
    if "google_trending" in channels and (
        source_filter is None or source_filter == "google_trending"
    ):
        try:
            trending_collector = GoogleTrendingCollector()
            trending_data = trending_collector.collect(
                region=filters.get("google_trending_region", "south_korea"),
                mode=filters.get("google_trending_mode", "daily"),
                category=filters.get("google_trending_category"),
                top_n=filters.get("google_trending_top_n", 20),
                date_override=end_date or start_date,
            )

            trending_points = 0
            trending_raw_records: list[dict[str, object]] = []
            for keyword, points in trending_data.items():
                valid_points = _filter_valid_points(
                    keyword=keyword,
                    points=points,
                    source="google_trending",
                    errors=errors,
                )
                if not valid_points:
                    continue

                trend_store.save_trend_points(
                    source="google_trending",
                    keyword=keyword,
                    points=valid_points,
                    metadata={
                        "set_name": keyword_set.name,
                        "region": filters.get("google_trending_region", "south_korea"),
                        "mode": filters.get("google_trending_mode", "daily"),
                        "category": filters.get("google_trending_category"),
                    },
                    db_path=db_path,
                )
                trending_points += len(valid_points)
                trending_raw_records.extend(
                    _build_raw_records(
                        keyword=keyword, source="google_trending", points=valid_points
                    )
                )
                if search_index is not None:
                    _sync_keyword_to_search_index(
                        search_index=search_index,
                        keyword=keyword,
                        source="google_trending",
                        keyword_set=keyword_set,
                    )

            if raw_logger is not None and trending_raw_records:
                raw_path = raw_logger.log(trending_raw_records, source_name="google_trending")
                print(f"  - Raw JSONL logged: {raw_path}")

            total_points += trending_points
            sources_succeeded += 1
            mark_core_source_success("google_trending")
            print(f"  - Google Trending: {len(trending_data)} keywords, {trending_points} points")

        except Exception as e:
            errors.append(f"Google Trending: {str(e)[:100]}")
            print(f"  - Google Trending failed: {e}")

    # Wikipedia Pageviews
    if "wikipedia" in channels and (source_filter is None or source_filter == "wikipedia"):
        try:
            wiki_collector = WikipediaPageviewsCollector()
            wiki_data = wiki_collector.collect(
                keywords=keywords,
                start_date=start_date,
                end_date=end_date,
                project=filters.get("wikipedia_project", "ko.wikipedia"),
                access=filters.get("wikipedia_access", "all-access"),
                agent=filters.get("wikipedia_agent", "user"),
                granularity=filters.get("wikipedia_granularity", "daily"),
            )

            wiki_points = 0
            wiki_raw_records: list[dict[str, object]] = []
            for keyword, points in wiki_data.items():
                valid_points = _filter_valid_points(
                    keyword=keyword,
                    points=points,
                    source="wikipedia",
                    errors=errors,
                )
                if not valid_points:
                    continue

                trend_store.save_trend_points(
                    source="wikipedia",
                    keyword=keyword,
                    points=valid_points,
                    metadata={
                        "set_name": keyword_set.name,
                        "project": filters.get("wikipedia_project", "ko.wikipedia"),
                        "access": filters.get("wikipedia_access", "all-access"),
                        "agent": filters.get("wikipedia_agent", "user"),
                        "granularity": filters.get("wikipedia_granularity", "daily"),
                    },
                    db_path=db_path,
                )
                wiki_points += len(valid_points)
                wiki_raw_records.extend(
                    _build_raw_records(keyword=keyword, source="wikipedia", points=valid_points)
                )
                if search_index is not None:
                    _sync_keyword_to_search_index(
                        search_index=search_index,
                        keyword=keyword,
                        source="wikipedia",
                        keyword_set=keyword_set,
                    )

            if raw_logger is not None and wiki_raw_records:
                raw_path = raw_logger.log(wiki_raw_records, source_name="wikipedia")
                print(f"  - Raw JSONL logged: {raw_path}")

            total_points += wiki_points
            sources_succeeded += 1
            mark_core_source_success("wikipedia")
            print(f"  - Wikipedia Pageviews: {len(wiki_data)} keywords, {wiki_points} points")

        except Exception as e:
            errors.append(f"Wikipedia Pageviews: {str(e)[:100]}")
            print(f"  - Wikipedia Pageviews failed: {e}")

    # Reddit Trending
    if "reddit" in channels and (source_filter is None or source_filter == "reddit"):
        source_ready, missing_env_vars = _is_source_available("reddit", source_availability)
        if not source_ready:
            missing_vars_text = ", ".join(missing_env_vars)
            print(f"  - Reddit Trending skipped: missing env vars ({missing_vars_text})")
        else:
            try:
                reddit_collector = RedditCollector(
                    client_id=os.environ.get("REDDIT_CLIENT_ID"),
                    client_secret=os.environ.get("REDDIT_CLIENT_SECRET"),
                )

                reddit_keywords = reddit_collector.collect_trending_keywords(
                    subreddits=filters.get(
                        "reddit_subreddits", ["worldnews", "technology", "science"]
                    ),
                    time_filter=filters.get("reddit_time_filter", "day"),
                    limit=filters.get("reddit_limit", 25),
                )

                reddit_points = 0
                reddit_raw_records: list[dict[str, object]] = []
                for keyword, count in reddit_keywords.items():
                    points = [
                        TrendPoint(
                            keyword=keyword,
                            source="reddit",
                            timestamp=datetime.now(UTC),
                            value=float(count),
                        )
                    ]
                    valid_points = _filter_valid_points(
                        keyword=keyword,
                        points=points,
                        source="reddit",
                        errors=errors,
                    )
                    if not valid_points:
                        continue

                    trend_store.save_trend_points(
                        source="reddit",
                        keyword=keyword,
                        points=valid_points,
                        metadata={
                            "set_name": keyword_set.name,
                            "subreddits": filters.get(
                                "reddit_subreddits", ["worldnews", "technology", "science"]
                            ),
                            "time_filter": filters.get("reddit_time_filter", "day"),
                        },
                        db_path=db_path,
                    )
                    reddit_points += 1
                    reddit_raw_records.extend(
                        _build_raw_records(keyword=keyword, source="reddit", points=valid_points)
                    )
                    if search_index is not None:
                        _sync_keyword_to_search_index(
                            search_index=search_index,
                            keyword=keyword,
                            source="reddit",
                            keyword_set=keyword_set,
                        )

                if raw_logger is not None and reddit_raw_records:
                    raw_path = raw_logger.log(reddit_raw_records, source_name="reddit")
                    print(f"  - Raw JSONL logged: {raw_path}")

                total_points += reddit_points
                sources_succeeded += 1
                mark_core_source_success("reddit")
                print(
                    f"  - Reddit Trending: {len(reddit_keywords)} keywords, {reddit_points} points"
                )

            except Exception as e:
                errors.append(f"Reddit Trending: {str(e)[:100]}")
                print(f"  - Reddit Trending failed: {e}")

    # YouTube Trending
    if "youtube" in channels and (source_filter is None or source_filter == "youtube"):
        source_ready, missing_env_vars = _is_source_available("youtube", source_availability)
        if not source_ready:
            missing_vars_text = ", ".join(missing_env_vars)
            print(f"  - YouTube Trending skipped: missing env vars ({missing_vars_text})")
        else:
            try:
                youtube_collector = YouTubeTrendingCollector(
                    api_key=os.environ.get("YOUTUBE_API_KEY"),
                )

                youtube_keywords = youtube_collector.collect_trending_keywords(
                    region_code=filters.get("youtube_region", "KR"),
                    max_results=filters.get("youtube_max_results", 50),
                )

                youtube_points = 0
                youtube_raw_records: list[dict[str, object]] = []
                for keyword, count in youtube_keywords.items():
                    points = [
                        TrendPoint(
                            keyword=keyword,
                            source="youtube",
                            timestamp=datetime.now(UTC),
                            value=float(count),
                        )
                    ]
                    valid_points = _filter_valid_points(
                        keyword=keyword,
                        points=points,
                        source="youtube",
                        errors=errors,
                    )
                    if not valid_points:
                        continue

                    trend_store.save_trend_points(
                        source="youtube",
                        keyword=keyword,
                        points=valid_points,
                        metadata={
                            "set_name": keyword_set.name,
                            "region_code": filters.get("youtube_region", "KR"),
                        },
                        db_path=db_path,
                    )
                    youtube_points += 1
                    youtube_raw_records.extend(
                        _build_raw_records(keyword=keyword, source="youtube", points=valid_points)
                    )
                    if search_index is not None:
                        _sync_keyword_to_search_index(
                            search_index=search_index,
                            keyword=keyword,
                            source="youtube",
                            keyword_set=keyword_set,
                        )

                if raw_logger is not None and youtube_raw_records:
                    raw_path = raw_logger.log(youtube_raw_records, source_name="youtube")
                    print(f"  - Raw JSONL logged: {raw_path}")

                total_points += youtube_points
                sources_succeeded += 1
                mark_core_source_success("youtube")
                print(
                    f"  - YouTube Trending: {len(youtube_keywords)} keywords, {youtube_points} points"
                )

            except Exception as e:
                errors.append(f"YouTube Trending: {str(e)[:100]}")
                print(f"  - YouTube Trending failed: {e}")

    # Naver Shopping
    if "naver_shopping" in channels and (
        source_filter is None or source_filter == "naver_shopping"
    ):
        source_ready, missing_env_vars = _is_source_available("naver_shopping", source_availability)
        if not source_ready:
            missing_vars_text = ", ".join(missing_env_vars)
            print(f"  - Naver Shopping skipped: missing env vars ({missing_vars_text})")
        else:
            try:
                naver_shopping_collector = NaverShoppingCollector(
                    client_id=os.environ.get("NAVER_CLIENT_ID"),
                    client_secret=os.environ.get("NAVER_CLIENT_SECRET"),
                )

                shopping_category = filters.get("naver_shopping_category", "50000000")
                shopping_trends: list[TrendCollectionResult] = (
                    naver_shopping_collector.collect_category_trends(
                        category=shopping_category,
                        start_date=start_date,
                        end_date=end_date,
                        time_unit=filters.get("naver_shopping_time_unit", "date"),
                        device=filters.get("naver_shopping_device", ""),
                        gender=filters.get("naver_shopping_gender", ""),
                        ages=filters.get("naver_shopping_ages"),
                    )
                )

                shopping_points = 0
                shopping_raw_records: list[dict[str, object]] = []
                for trend_item in shopping_trends:
                    category_name = trend_item.keyword
                    points = trend_item.points
                    valid_points = _filter_valid_points(
                        keyword=category_name,
                        points=points,
                        source="naver_shopping",
                        errors=errors,
                    )
                    if not valid_points:
                        continue

                    trend_store.save_trend_points(
                        source="naver_shopping",
                        keyword=category_name,
                        points=valid_points,
                        metadata={
                            "set_name": keyword_set.name,
                            "category": shopping_category,
                            "device": filters.get("naver_shopping_device", ""),
                            "gender": filters.get("naver_shopping_gender", ""),
                        },
                        db_path=db_path,
                    )
                    shopping_points += len(valid_points)
                    shopping_raw_records.extend(
                        _build_raw_records(
                            keyword=category_name,
                            source="naver_shopping",
                            points=valid_points,
                        )
                    )
                    if search_index is not None:
                        _sync_keyword_to_search_index(
                            search_index=search_index,
                            keyword=category_name,
                            source="naver_shopping",
                            keyword_set=keyword_set,
                        )

                if raw_logger is not None and shopping_raw_records:
                    raw_path = raw_logger.log(shopping_raw_records, source_name="naver_shopping")
                    print(f"  - Raw JSONL logged: {raw_path}")

                total_points += shopping_points
                sources_succeeded += 1
                mark_core_source_success("naver_shopping")
                print(
                    f"  - Naver Shopping: {len(shopping_trends)} categories, {shopping_points} points"
                )

            except Exception as e:
                errors.append(f"Naver Shopping: {str(e)[:100]}")
                print(f"  - Naver Shopping failed: {e}")

    # HackerNews
    if "hackernews" in channels and (source_filter is None or source_filter == "hackernews"):
        try:
            hn_collector = HackerNewsCollector()
            hn_stories: list[ContentItem] = hn_collector.collect(limit=30)

            hn_raw_records: list[dict[str, object]] = []
            for story in hn_stories:
                keyword = story.title
                score = story.score
                if not validate_keyword(keyword) or not validate_score(score):
                    errors.append("hackernews: invalid keyword/score")
                    continue

                story_record = _build_content_raw_record(
                    keyword=keyword,
                    source="hackernews",
                    score=score,
                    timestamp=str(story.metadata.get("time", 0)),
                )
                hn_raw_records.append(story_record)

            if raw_logger is not None and hn_raw_records:
                raw_path = raw_logger.log(hn_raw_records, source_name="hackernews")
                print(f"  - Raw JSONL logged: {raw_path}")

            total_points += len(hn_raw_records)
            sources_succeeded += 1
            print(f"  - HackerNews: {len(hn_raw_records)} stories")

        except Exception as e:
            errors.append(f"HackerNews: {str(e)[:100]}")
            print(f"  - HackerNews failed: {e}")

    # Dev.to
    if "devto" in channels and (source_filter is None or source_filter == "devto"):
        try:
            devto_collector = DevtoCollector()
            devto_articles: list[ContentItem] = devto_collector.collect(limit=30)

            devto_raw_records: list[dict[str, object]] = []
            for article in devto_articles:
                keyword = article.title
                score = article.score
                if not validate_keyword(keyword) or not validate_score(score):
                    errors.append("devto: invalid keyword/score")
                    continue

                article_record = _build_content_raw_record(
                    keyword=keyword,
                    source="devto",
                    score=score,
                    timestamp=str(article.metadata.get("published_at", "")),
                )
                devto_raw_records.append(article_record)

            if raw_logger is not None and devto_raw_records:
                raw_path = raw_logger.log(devto_raw_records, source_name="devto")
                print(f"  - Raw JSONL logged: {raw_path}")

            total_points += len(devto_raw_records)
            sources_succeeded += 1
            print(f"  - Dev.to: {len(devto_raw_records)} articles")

        except Exception as e:
            errors.append(f"Dev.to: {str(e)[:100]}")
            print(f"  - Dev.to failed: {e}")

    # Stack Exchange
    if "stackexchange" in channels and (source_filter is None or source_filter == "stackexchange"):
        try:
            se_collector = StackExchangeCollector()
            se_questions: list[ContentItem] = se_collector.collect(limit=30)

            se_raw_records: list[dict[str, object]] = []
            for question in se_questions:
                keyword = question.title
                score = question.score
                if not validate_keyword(keyword) or not validate_score(score):
                    errors.append("stackexchange: invalid keyword/score")
                    continue

                question_record = _build_content_raw_record(
                    keyword=keyword,
                    source="stackexchange",
                    score=score,
                    timestamp=str(question.metadata.get("creation_date", 0)),
                )
                se_raw_records.append(question_record)

            if raw_logger is not None and se_raw_records:
                raw_path = raw_logger.log(se_raw_records, source_name="stackexchange")
                print(f"  - Raw JSONL logged: {raw_path}")

            total_points += len(se_raw_records)
            sources_succeeded += 1
            print(f"  - Stack Exchange: {len(se_raw_records)} questions")

        except Exception as e:
            errors.append(f"Stack Exchange: {str(e)[:100]}")
            print(f"  - Stack Exchange failed: {e}")

    # Product Hunt
    if "producthunt" in channels and (source_filter is None or source_filter == "producthunt"):
        try:
            ph_collector = ProductHuntCollector()
            ph_products: list[ContentItem] = ph_collector.collect(limit=30)

            ph_raw_records: list[dict[str, object]] = []
            for product in ph_products:
                keyword = product.title
                score = product.score
                if not validate_keyword(keyword) or not validate_score(score):
                    errors.append("producthunt: invalid keyword/score")
                    continue

                product_record = _build_content_raw_record(
                    keyword=keyword,
                    source="producthunt",
                    score=score,
                    timestamp=str(product.metadata.get("created_at", "")),
                )
                ph_raw_records.append(product_record)

            if raw_logger is not None and ph_raw_records:
                raw_path = raw_logger.log(ph_raw_records, source_name="producthunt")
                print(f"  - Raw JSONL logged: {raw_path}")

            total_points += len(ph_raw_records)
            sources_succeeded += 1
            print(f"  - Product Hunt: {len(ph_raw_records)} products")

        except Exception as e:
            errors.append(f"Product Hunt: {str(e)[:100]}")
            print(f"  - Product Hunt failed: {e}")

    # Browser (Playwright)
    if "browser" in channels and (source_filter is None or source_filter == "browser"):
        try:
            browser_sources_config = filters.get("browser_sources")
            browser_sources: list[dict[str, object]] | None = (
                browser_sources_config if isinstance(browser_sources_config, list) else None
            )

            browser_collector = BrowserCollector(
                timeout_ms=int(filters.get("browser_timeout_ms", 20_000)),
                rate_limit=float(filters.get("browser_rate_limit", 3.0)),
            )
            browser_items: list[ContentItem] = browser_collector.collect(
                sources=browser_sources,
                limit=int(filters.get("browser_limit", 30)),
            )

            browser_raw_records: list[dict[str, object]] = []
            for item in browser_items:
                keyword = item.title
                score = item.score
                if not validate_keyword(keyword) or not validate_score(score):
                    errors.append("browser: invalid keyword/score")
                    continue

                item_record = _build_content_raw_record(
                    keyword=keyword,
                    source="browser",
                    score=score,
                    timestamp=str(item.metadata.get("collected_at", "")),
                )
                browser_raw_records.append(item_record)

            if raw_logger is not None and browser_raw_records:
                raw_path = raw_logger.log(browser_raw_records, source_name="browser")
                print(f"  - Raw JSONL logged: {raw_path}")

            total_points += len(browser_raw_records)
            sources_succeeded += 1
            print(f"  - Browser (Playwright): {len(browser_raw_records)} items")

        except Exception as e:
            errors.append(f"Browser: {str(e)[:100]}")
            print(f"  - Browser (Playwright) failed: {e}")

    return total_points, sources_succeeded, errors


def run_once(
    execute_collectors: bool = False,
    *,
    config_path: Path | None = None,
    db_path: Path | None = None,
    generate_report: bool = False,
    report_output_dir: Path | None = None,
    source_filter: str | None = None,
    notifier: Notifier | None = None,
) -> None:
    """트렌드 수집을 한 번 실행합니다."""
    start_time = time.time()
    now = datetime.now(UTC)

    print(f"[{now.isoformat()}] TrendRadar run_once 시작")

    if not execute_collectors:
        print("  - 실행 모드: dry-run (collectors 미실행)")
        return

    source_availability = get_core_source_availability()
    _print_core_source_availability_report(source_availability)

    # 키워드 세트 설정 로드
    keyword_sets = load_keyword_sets_config(config_path)

    if not keyword_sets:
        print("  - 경고: keyword_sets.yaml에 키워드 세트가 없습니다.")
        return

    print(f"  - 로드된 키워드 세트: {len(keyword_sets)}개")

    raw_logger = RawLogger(DEFAULT_RAW_DIR)
    search_index = SearchIndex(DEFAULT_SEARCH_DB_PATH)

    # 각 키워드 세트별로 수집
    total_points = 0
    total_sources_succeeded = 0
    successful_core_sources: set[str] = set()
    all_errors: list[str] = []

    for kw_set in keyword_sets:
        if not kw_set.enabled:
            continue

        set_name = kw_set.name or "Unknown"
        print(f"\n  [{set_name}] 수집 시작...")

        points, sources, errors = collect_trends(
            kw_set,
            db_path=db_path,
            source_filter=source_filter,
            raw_logger=raw_logger,
            search_index=search_index,
            source_availability=source_availability,
            successful_core_sources=successful_core_sources,
        )

        total_points += points
        total_sources_succeeded += sources
        all_errors.extend(errors)

    if notifier is not None and db_path is not None:
        events = detect_trend_notifications(db_path, notifier.config.rules)
        for event in events:
            notifier.send(
                title=event.title,
                message=event.message,
                priority=event.priority,
                metadata=event.metadata,
            )

    print(f"\n  - 총 수집 데이터 포인트: {total_points}개")
    print(f"  - collected from {len(successful_core_sources)}/{TOTAL_CORE_SOURCES} sources")
    print(f"  - 성공한 소스 실행 횟수: {total_sources_succeeded}개")

    # HTML 리포트 생성
    if generate_report:
        print("\n  - HTML 리포트 생성 중...")
        try:
            report_dir = report_output_dir or DEFAULT_REPORT_DIR
            report_dir.mkdir(parents=True, exist_ok=True)

            generate_daily_report(
                target_date=now.date(),
                keyword_sets=keyword_sets,
                db_path=db_path,
                output_dir=report_dir,
            )
            print(f"  ✓ 리포트 저장: {report_dir}")
            # Generate unified index.html
            try:
                from trendradar.reporter import generate_index_html

                generate_index_html(report_dir)
                print("  ✓ 인덱스 페이지 생성 완료 (radar-core)")
            except Exception as e_idx:
                print(f"  ✗ 인덱스 생성 실패: {e_idx}")
        except Exception as e:
            print(f"  ✗ 리포트 생성 실패: {e}")
            all_errors.append(f"Report generation: {str(e)[:100]}")

        # 급상승 키워드 감지 및 리포트 생성
        print("\n  - 급상승 키워드 감지 중...")
        try:
            detector = SpikeDetector(db_path=db_path, recent_days=7, baseline_days=30)
            all_spikes = detector.detect_all_spikes(source=None, top_n=10)

            total_spikes = sum(len(v) for v in all_spikes.values())
            if total_spikes > 0:
                print(f"  ✓ 급상승 신호 {total_spikes}개 감지")
                print(f"    - Surge: {len(all_spikes['surge'])}개")
                print(f"    - Emerging: {len(all_spikes['emerging'])}개")
                print(f"    - Viral: {len(all_spikes['viral'])}개")

                report_dir = report_output_dir or DEFAULT_REPORT_DIR
                generate_spike_report(
                    target_date=now.date(),
                    db_path=db_path,
                    output_dir=report_dir,
                )
                print(f"  ✓ 급상승 리포트 저장: {report_dir}")
            else:
                print("  ℹ️  급상승 신호 없음 (데이터 부족 가능)")
        except Exception as e:
            print(f"  ✗ 급상승 감지 실패: {e}")
            all_errors.append(f"Spike detection: {str(e)[:100]}")

    runtime_seconds = time.time() - start_time
    print(f"\n  - 실행 시간: {runtime_seconds:.1f}초")

    if all_errors:
        print(f"  - 오류 {len(all_errors)}건:")
        for err in all_errors[:5]:  # 최대 5개만 표시
            print(f"    - {err}")


def run_scheduler(
    interval_hours: int = 24,
    *,
    config_path: Path | None = None,
    db_path: Path | None = None,
    notifier: Notifier | None = None,
) -> None:
    """정기적으로 트렌드 데이터를 수집하는 스케줄러.

    Args:
        interval_hours: 수집 간격 (시간 단위, 기본 24시간)
        config_path: keyword_sets.yaml 경로
        db_path: DuckDB 파일 경로
    """
    print(f"TrendRadar 스케줄러 시작 (수집 간격: {interval_hours}시간)")
    print("중단하려면 Ctrl+C를 누르세요")

    while True:
        try:
            run_once(
                execute_collectors=True,
                config_path=config_path,
                db_path=db_path,
                generate_report=True,
                notifier=notifier,
            )
            print(f"\n다음 수집까지 {interval_hours}시간 대기 중...")
            time.sleep(interval_hours * 3600)

        except KeyboardInterrupt:
            print("\n스케줄러 종료")
            break
        except Exception as e:
            print(f"오류 발생: {e}")
            print("10분 후 재시도...")
            time.sleep(600)  # 10분 대기 후 재시도


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="TrendRadar 트렌드 데이터 수집")
    parser.add_argument(
        "--mode",
        choices=["once", "scheduler"],
        default="once",
        help="실행 모드: once (1회 실행) 또는 scheduler (정기 실행)",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=24,
        help="스케줄러 모드에서 수집 간격 (시간 단위, 기본 24)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry-run 모드 (수집 없이 설정만 확인)",
    )
    parser.add_argument(
        "--generate-report",
        action="store_true",
        help="HTML 리포트 생성 (기본값: False)",
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
        help=f"리포트 출력 디렉토리 (기본값: {DEFAULT_REPORT_DIR})",
    )
    parser.add_argument(
        "--source",
        choices=[
            "naver",
            "google",
            "google_trending",
            "wikipedia",
            "hackernews",
            "devto",
            "stackexchange",
            "producthunt",
            "browser",
        ],
        default=None,
        help="특정 소스만 수집 (기본값: 모두)",
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=DEFAULT_DB_PATH,
        help="DuckDB 파일 경로",
    )
    parser.add_argument(
        "--notifications-config",
        type=Path,
        default=DEFAULT_NOTIFICATION_CONFIG_PATH,
        help="알림 설정 파일 경로",
    )

    args = parser.parse_args()

    notification_config = load_notification_config(args.notifications_config)
    notifier = PipelineNotifier(notification_config)

    if args.mode == "once":
        run_once(
            execute_collectors=not args.dry_run,
            generate_report=args.generate_report,
            report_output_dir=args.report_dir,
            source_filter=args.source,
            db_path=args.db_path,
            notifier=notifier,
        )
    else:
        if args.dry_run:
            print("스케줄러 모드에서는 dry-run이 지원되지 않습니다")
        else:
            run_scheduler(
                interval_hours=args.interval,
                db_path=args.db_path,
                notifier=notifier,
            )
