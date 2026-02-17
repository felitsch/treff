"""Database configuration and session management."""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.core.config import settings

logger = logging.getLogger(__name__)

if settings.TURSO_DATABASE_URL:
    import aiosqlite
    import httpx
    import base64

    _base_url = settings.TURSO_DATABASE_URL.replace("libsql://", "https://")
    _token = settings.TURSO_AUTH_TOKEN

    def _val_to_hrana(v):
        """Python value -> Turso Hrana wire format."""
        if v is None:
            return {"type": "null"}
        if isinstance(v, bool):
            return {"type": "integer", "value": str(int(v))}
        if isinstance(v, int):
            return {"type": "integer", "value": str(v)}
        if isinstance(v, float):
            return {"type": "float", "value": v}
        if isinstance(v, bytes):
            return {"type": "blob", "base64": base64.b64encode(v).decode()}
        return {"type": "text", "value": str(v)}

    def _hrana_to_val(cell):
        """Turso Hrana cell -> Python value."""
        t = cell["type"]
        if t == "null":
            return None
        if t == "integer":
            return int(cell["value"])
        if t == "float":
            return cell["value"]
        if t == "blob":
            return base64.b64decode(cell["base64"])
        return cell["value"]  # text

    class _TursoHTTPCursor:
        """sqlite3 DBAPI-compatible cursor that talks to Turso via HTTP."""

        def __init__(self, client, base_url, token):
            self._client = client
            self._base_url = base_url
            self._token = token
            self._rows = []
            self._cols = []
            self._pos = 0
            self._lastrowid = None
            self._rowcount = -1

        def execute(self, sql, parameters=None):
            args = [_val_to_hrana(p) for p in (parameters or [])]
            body = {"requests": [
                {"type": "execute", "stmt": {"sql": sql, "args": args}},
                {"type": "close"},
            ]}
            resp = self._client.post(
                f"{self._base_url}/v2/pipeline",
                headers={"Authorization": f"Bearer {self._token}"},
                json=body,
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            result_obj = data["results"][0]
            if result_obj["type"] == "error":
                raise Exception(result_obj["error"]["message"])
            result = result_obj["response"]["result"]
            self._cols = result.get("cols", [])
            self._rows = [
                tuple(_hrana_to_val(c) for c in row)
                for row in result.get("rows", [])
            ]
            self._pos = 0
            self._rowcount = result.get("affected_row_count", -1)
            rid = result.get("last_insert_rowid")
            self._lastrowid = int(rid) if rid else None
            return self

        def executemany(self, sql, seq_of_parameters):
            for params in seq_of_parameters:
                self.execute(sql, params)
            return self

        def fetchone(self):
            if self._pos >= len(self._rows):
                return None
            row = self._rows[self._pos]
            self._pos += 1
            return row

        def fetchall(self):
            rows = self._rows[self._pos:]
            self._pos = len(self._rows)
            return rows

        def fetchmany(self, size=None):
            if size is None:
                size = 1
            end = min(self._pos + size, len(self._rows))
            rows = self._rows[self._pos:end]
            self._pos = end
            return rows

        def close(self):
            pass

        @property
        def description(self):
            if not self._cols:
                return None
            return [
                (col.get("name", ""), None, None, None, None, None, None)
                for col in self._cols
            ]

        @property
        def lastrowid(self):
            return self._lastrowid

        @property
        def rowcount(self):
            return self._rowcount

        def __iter__(self):
            return iter(self._rows)

    class _TursoHTTPConnection:
        """sqlite3 DBAPI-compatible connection that talks to Turso via HTTP."""

        def __init__(self, base_url, token):
            self._client = httpx.Client()
            self._base_url = base_url
            self._token = token
            self.isolation_level = ""

        def cursor(self):
            return _TursoHTTPCursor(self._client, self._base_url, self._token)

        def execute(self, sql, parameters=None):
            c = self.cursor()
            c.execute(sql, parameters)
            return c

        def executemany(self, sql, seq_of_parameters):
            c = self.cursor()
            c.executemany(sql, seq_of_parameters)
            return c

        def commit(self):
            pass  # HTTP API = autocommit

        def rollback(self):
            pass

        def close(self):
            self._client.close()

        def create_function(self, *a, **kw):
            pass

        def create_collation(self, *a, **kw):
            pass

        @property
        def in_transaction(self):
            return False

        @property
        def total_changes(self):
            return 0

    def _connector():
        return _TursoHTTPConnection(_base_url, _token)

    async def _async_creator():
        conn = aiosqlite.Connection(_connector, iter_chunk_size=64)
        await conn  # calls start() + _connect() via __await__
        return conn

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        async_creator=_async_creator,
        poolclass=StaticPool,
    )
    logger.info("Using Turso database (HTTP API): %s", _base_url)
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.SQL_ECHO,
        connect_args={"check_same_thread": False},
    )
    logger.info("Using local SQLite database")

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def turso_batch_execute(statements: list[str]) -> list[dict]:
    """Send multiple SQL statements in a single Turso pipeline request.

    Returns a list of per-statement results: {"type": "ok", ...} or {"type": "error", ...}.
    Falls back to sequential execution if Turso is not configured.
    """
    if not settings.TURSO_DATABASE_URL:
        # Local SQLite: execute sequentially via engine
        results = []
        from sqlalchemy import text
        async with engine.begin() as conn:
            for sql in statements:
                try:
                    await conn.execute(text(sql))
                    results.append({"type": "ok"})
                except Exception as e:
                    results.append({"type": "error", "error": str(e)})
        return results

    # Turso: batch via single HTTP pipeline request
    pipeline_requests = [{"type": "execute", "stmt": {"sql": s, "args": []}} for s in statements]
    pipeline_requests.append({"type": "close"})

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{_base_url}/v2/pipeline",
            headers={"Authorization": f"Bearer {_token}"},
            json={"requests": pipeline_requests},
            timeout=30.0,
        )
    resp.raise_for_status()
    data = resp.json()

    # Exclude the close response (last item) and validate count
    stmt_results = data.get("results", [])[:-1]
    if len(stmt_results) != len(statements):
        logger.warning(
            "Turso pipeline returned %d results for %d statements",
            len(stmt_results), len(statements),
        )

    results = []
    for r in stmt_results:
        if r.get("type") == "ok":
            results.append({"type": "ok"})
        else:
            results.append({"type": "error", "error": r.get("error", {}).get("message", "unknown")})
    return results


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db():
    """Dependency to get database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
