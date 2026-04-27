from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType
from typing import cast


@dataclass(frozen=True)
class SearchResult:
    link: str
    title: str
    snippet: str
    rank: float
    keyword: str
    platform: str
    context: str
    score: float


class SearchIndex:
    db_path: Path

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = sqlite3.connect(str(self.db_path))
        self._initialize()

    def __enter__(self) -> SearchIndex:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        _ = (exc_type, exc_value, traceback)
        self.close()

    def _connect(self) -> sqlite3.Connection:
        if self._conn is None:
            raise sqlite3.ProgrammingError("SearchIndex connection is closed")
        return self._conn

    def _initialize(self) -> None:
        conn = self._connect()
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS documents (
                link TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                body TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                title, body, content='documents', content_rowid='rowid'
            );

            CREATE TRIGGER IF NOT EXISTS documents_ai AFTER INSERT ON documents BEGIN
                INSERT INTO documents_fts(rowid, title, body)
                VALUES (new.rowid, new.title, new.body);
            END;

            CREATE TRIGGER IF NOT EXISTS documents_ad AFTER DELETE ON documents BEGIN
                INSERT INTO documents_fts(documents_fts, rowid, title, body)
                VALUES ('delete', old.rowid, old.title, old.body);
            END;

            CREATE TRIGGER IF NOT EXISTS documents_au AFTER UPDATE ON documents BEGIN
                INSERT INTO documents_fts(documents_fts, rowid, title, body)
                VALUES ('delete', old.rowid, old.title, old.body);
                INSERT INTO documents_fts(rowid, title, body)
                VALUES (new.rowid, new.title, new.body);
            END;

            CREATE TABLE IF NOT EXISTS keyword_documents (
                link TEXT PRIMARY KEY,
                keyword TEXT NOT NULL,
                platform TEXT NOT NULL,
                context TEXT NOT NULL
            );

            CREATE VIRTUAL TABLE IF NOT EXISTS keyword_fts
            USING fts5(link UNINDEXED, keyword, context);
            """
        )
        conn.commit()

    def upsert(
        self,
        *args: str,
        link: str | None = None,
        title: str | None = None,
        body: str | None = None,
        keyword: str | None = None,
        platform: str | None = None,
        context: str | None = None,
    ) -> None:
        if keyword is not None or platform is not None or context is not None:
            self._upsert_keyword(
                keyword=str(keyword or ""),
                platform=str(platform or ""),
                context=str(context or ""),
            )
            return

        if link is not None or title is not None or body is not None:
            self._upsert_document(link=str(link or ""), title=str(title or ""), body=str(body or ""))
            return

        if len(args) != 3:
            raise TypeError("upsert expects either (link, title, body) or keyword/platform/context")

        link, title, body = args
        self._upsert_document(link=link, title=title, body=body)

    def _upsert_document(self, *, link: str, title: str, body: str) -> None:
        conn = self._connect()
        conn.execute("DELETE FROM documents WHERE link = ?", (link,))
        conn.execute(
            "INSERT INTO documents(link, title, body) VALUES (?, ?, ?)",
            (link, title, body),
        )
        conn.commit()

    def _upsert_keyword(self, *, keyword: str, platform: str, context: str) -> None:
        link = f"{keyword}|{platform}"
        conn = self._connect()
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
        conn.commit()

    def search(self, query: str, *, limit: int = 20) -> list[SearchResult]:
        if limit <= 0:
            return []

        conn = self._connect()
        doc_rows = cast(
            list[tuple[str, str, str, float]],
            conn.execute(
                """
                SELECT d.link, d.title,
                       snippet(documents_fts, 1, '<b>', '</b>', '...', 32) AS snippet,
                       bm25(documents_fts) AS rank
                FROM documents_fts
                JOIN documents AS d ON d.rowid = documents_fts.rowid
                WHERE documents_fts MATCH ?
                ORDER BY rank ASC
                LIMIT ?
                """,
                (query, limit),
            ).fetchall(),
        )

        results = [
            SearchResult(
                link=str(link),
                title=str(title),
                snippet=str(snippet),
                rank=float(rank),
                keyword=str(title),
                platform="",
                context=str(snippet),
                score=float(rank),
            )
            for link, title, snippet, rank in doc_rows
        ]

        if len(results) >= limit:
            return results[:limit]

        keyword_rows = cast(
            list[tuple[str, str, str, str, float]],
            conn.execute(
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
                (query, limit - len(results)),
            ).fetchall(),
        )

        results.extend(
            SearchResult(
                link=str(link),
                title=str(keyword),
                snippet=str(context),
                rank=float(score),
                keyword=str(keyword),
                platform=str(platform),
                context=str(context),
                score=float(score),
            )
            for keyword, platform, context, link, score in keyword_rows
        )
        return results

    def close(self) -> None:
        if self._conn is None:
            return
        self._conn.close()
        self._conn = None
