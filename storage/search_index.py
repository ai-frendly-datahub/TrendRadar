from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SearchResult:
    keyword: str
    platform: str
    context: str
    link: str
    score: float


class SearchIndex:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS keyword_documents (
                    link TEXT PRIMARY KEY,
                    keyword TEXT NOT NULL,
                    platform TEXT NOT NULL,
                    context TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS keyword_fts
                USING fts5(link UNINDEXED, keyword, context)
                """
            )

    def upsert(self, keyword: str, platform: str, context: str) -> None:
        """Index keyword for search. link = keyword|platform composite key."""
        link = f"{keyword}|{platform}"
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO keyword_documents (link, keyword, platform, context)
                VALUES (?, ?, ?, ?)
                """,
                (link, keyword, platform, context),
            )
            conn.execute("DELETE FROM keyword_fts WHERE link = ?", (link,))
            conn.execute(
                """
                INSERT INTO keyword_fts (link, keyword, context)
                VALUES (?, ?, ?)
                """,
                (link, keyword, context),
            )

    def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    d.keyword,
                    d.platform,
                    d.context,
                    d.link,
                    bm25(keyword_fts) AS score
                FROM keyword_fts
                JOIN keyword_documents AS d ON d.link = keyword_fts.link
                WHERE keyword_fts MATCH ?
                ORDER BY score ASC
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()

        return [
            SearchResult(
                keyword=row["keyword"],
                platform=row["platform"],
                context=row["context"],
                link=row["link"],
                score=float(row["score"]),
            )
            for row in rows
        ]
