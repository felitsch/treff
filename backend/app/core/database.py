"""Database configuration and session management."""

import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import StaticPool

from app.core.config import settings

logger = logging.getLogger(__name__)

if settings.TURSO_DATABASE_URL:
    import aiosqlite
    import libsql_experimental as libsql

    def _norm_params(params):
        """Convert list params to tuple (libsql only accepts tuples)."""
        if isinstance(params, list):
            return tuple(params)
        return params

    class _LibSQLCursorCompat:
        """Wraps libsql Cursor so parameters are always tuples."""
        def __init__(self, cursor):
            self._cursor = cursor
        def execute(self, sql, parameters=None):
            if parameters is not None:
                return self._cursor.execute(sql, _norm_params(parameters))
            return self._cursor.execute(sql)
        def executemany(self, sql, parameters):
            return self._cursor.executemany(sql, parameters)
        def fetchone(self):
            return self._cursor.fetchone()
        def fetchmany(self, size=None):
            return self._cursor.fetchmany(size) if size else self._cursor.fetchmany()
        def fetchall(self):
            return self._cursor.fetchall()
        def close(self):
            return self._cursor.close()
        @property
        def description(self):
            return self._cursor.description
        @property
        def lastrowid(self):
            return self._cursor.lastrowid
        @property
        def rowcount(self):
            return self._cursor.rowcount
        def __getattr__(self, name):
            return getattr(self._cursor, name)
        def __iter__(self):
            return iter(self._cursor)

    class _LibSQLCompat:
        """Wraps libsql Connection to look like sqlite3.Connection for aiosqlite."""
        def __init__(self, conn):
            self._conn = conn
            self.isolation_level = ""
        def cursor(self):
            return _LibSQLCursorCompat(self._conn.cursor())
        def commit(self):
            return self._conn.commit()
        def rollback(self):
            return self._conn.rollback()
        def close(self):
            return self._conn.close()
        def execute(self, sql, parameters=None):
            if parameters is not None:
                return _LibSQLCursorCompat(self._conn.execute(sql, _norm_params(parameters)))
            return _LibSQLCursorCompat(self._conn.execute(sql))
        def executemany(self, sql, parameters):
            return _LibSQLCursorCompat(self._conn.executemany(sql, parameters))
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
        def __getattr__(self, name):
            return getattr(self._conn, name)

    _url = settings.TURSO_DATABASE_URL
    _token = settings.TURSO_AUTH_TOKEN

    def _connector():
        return _LibSQLCompat(libsql.connect(_url, auth_token=_token))

    async def _async_creator():
        conn = aiosqlite.Connection(_connector, iter_chunk_size=64)
        await conn  # calls start() + _connect() via __await__
        return conn

    engine = create_async_engine(
        "sqlite+aiosqlite://",
        async_creator=_async_creator,
        poolclass=StaticPool,
    )
    logger.info("Using Turso database: %s", _url)
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.SQL_ECHO,
        connect_args={"check_same_thread": False},
    )
    logger.info("Using local SQLite database")

async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


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
