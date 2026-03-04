from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from mcp_server.tools import (
    handle_price_watch,
    handle_recent_updates,
    handle_search,
    handle_sql,
    handle_top_trends,
)

app = Server("trendradar")


def _db_path() -> Path:
    return Path(os.getenv("TRENDRADAR_DB_PATH", "data/trendradar.duckdb"))


def _search_db_path() -> Path:
    return Path(os.getenv("TRENDRADAR_SEARCH_DB_PATH", "data/search_index.db"))


def _as_int(value: Any, default: int) -> int:
    if isinstance(value, bool):
        return default
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return default
    return default


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="search",
            description="Search indexed keywords with natural-language query parsing.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="recent_updates",
            description="List recent trend_points ordered by collected_at.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "minimum": 1},
                    "limit": {"type": "integer", "minimum": 1},
                },
            },
        ),
        Tool(
            name="sql",
            description="Execute read-only SQL (SELECT/WITH/EXPLAIN only) on TrendRadar DuckDB.",
            inputSchema={
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
            },
        ),
        Tool(
            name="top_trends",
            description="Show top active spike keywords from trend data.",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "minimum": 1},
                    "limit": {"type": "integer", "minimum": 1},
                },
            },
        ),
        Tool(
            name="price_watch",
            description="Price watch stub for compatibility.",
            inputSchema={"type": "object", "properties": {}},
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
    args = arguments or {}

    if name == "search":
        result = handle_search(
            search_db_path=_search_db_path(),
            db_path=_db_path(),
            query=str(args.get("query", "")),
            limit=_as_int(args.get("limit"), 20),
        )
    elif name == "recent_updates":
        result = handle_recent_updates(
            db_path=_db_path(),
            days=_as_int(args.get("days"), 7),
            limit=_as_int(args.get("limit"), 20),
        )
    elif name == "sql":
        result = handle_sql(db_path=_db_path(), query=str(args.get("query", "")))
    elif name == "top_trends":
        result = handle_top_trends(
            db_path=_db_path(),
            days=_as_int(args.get("days"), 7),
            limit=_as_int(args.get("limit"), 10),
        )
    elif name == "price_watch":
        result = handle_price_watch()
    else:
        result = f"Unknown tool: {name}"

    return [TextContent(type="text", text=result)]


async def main() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
