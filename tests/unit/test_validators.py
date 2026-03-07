from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from trendradar.common.validators import (
    detect_duplicate_articles,
    is_similar_url,
    normalize_title,
    validate_article,
    validate_keyword,
    validate_score,
    validate_url_format,
)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("raw_title", "expected"),
    [
        ("AI Trend Report", "ai trend report"),
        ("  AI   Trend  ", "ai trend"),
        ("Topic (2026)", "topic 2026"),
        ("", ""),
        ("트렌드 키워드", "트렌드 키워드"),
    ],
)
def test_normalize_title(raw_title: str, expected: str) -> None:
    assert normalize_title(raw_title) == expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://example.com/post/1", True),
        ("http://example.com/post/1", True),
        ("example.com/post/1", False),
        ("", False),
        (None, False),
    ],
)
def test_validate_url_format(url: str, expected: bool) -> None:
    assert validate_url_format(url) is expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("url1", "url2", "threshold", "expected"),
    [
        ("https://example.com/a/1", "https://example.com/a/1", 0.8, True),
        ("https://example.com/a/1", "https://example.com/a/1?utm=1", 0.8, True),
        ("https://example.com/a/1", "https://other.com/a/1", 0.8, False),
        ("https://example.com/a/1", "https://example.com/a/2", 0.95, False),
        ("https://example.com/a/1", "https://example.com/a/2", 0.5, True),
    ],
)
def test_is_similar_url(url1: str, url2: str, threshold: float, expected: bool) -> None:
    assert is_similar_url(url1, url2, threshold=threshold) is expected


@pytest.mark.unit
def test_detect_duplicate_articles() -> None:
    assert (
        detect_duplicate_articles(
            "AI market outlook",
            "https://example.com/a/1",
            "AI market outlook",
            "https://example.com/a/1?ref=x",
        )
        is True
    )


@pytest.mark.unit
def test_validate_article_valid_dict() -> None:
    article = {
        "title": "AI 시장",
        "url": "https://example.com/1",
        "summary": "요약",
        "source": "google",
        "category": "trend",
    }
    is_valid, errors = validate_article(article)
    assert is_valid is True
    assert errors == []


@pytest.mark.unit
@pytest.mark.parametrize(
    "article",
    [
        {"title": "", "url": "https://example.com", "summary": "x", "source": "s", "category": "c"},
        {"title": "t", "url": "bad", "summary": "x", "source": "s", "category": "c"},
        {"title": "t", "url": "https://example.com", "summary": "", "source": "s", "category": "c"},
        {"title": "t", "url": "https://example.com", "summary": "x", "source": "", "category": "c"},
        {"title": "t", "url": "https://example.com", "summary": "x", "source": "s", "category": ""},
    ],
)
def test_validate_article_invalid_cases(article: dict[str, str]) -> None:
    is_valid, errors = validate_article(article)
    assert is_valid is False
    assert errors


@pytest.mark.unit
@pytest.mark.parametrize(
    ("score", "expected"),
    [
        (None, True),
        (0.0, True),
        (1.0, True),
        (99.9, True),
        (-0.0001, False),
    ],
)
def test_validate_score(score: float | None, expected: bool) -> None:
    assert validate_score(score) is expected


@pytest.mark.unit
@pytest.mark.parametrize(
    ("keyword", "expected"),
    [
        ("A", True),
        ("AI", True),
        ("인공지능", True),
        ("", False),
        ("x" * 100, True),
        ("x" * 101, False),
    ],
)
def test_validate_keyword(keyword: str, expected: bool) -> None:
    assert validate_keyword(keyword) is expected
