from __future__ import annotations

import pytest

from nl_query import parse_query


@pytest.mark.unit
def test_parse_query_extracts_korean_time_and_limit():
    parsed = parse_query("최근 7일 인공지능 트렌드 5개")

    assert parsed.days == 7
    assert parsed.limit == 5
    assert parsed.search_text == "인공지능 트렌드"


@pytest.mark.unit
def test_parse_query_extracts_english_time_and_limit():
    parsed = parse_query("show bitcoin trends for last 14 days limit 3")

    assert parsed.days == 14
    assert parsed.limit == 3
    assert parsed.search_text == "show bitcoin trends for"


@pytest.mark.unit
def test_parse_query_keeps_plain_text_when_no_filters():
    parsed = parse_query("chatgpt spike")

    assert parsed.days is None
    assert parsed.limit == 20
    assert parsed.search_text == "chatgpt spike"
