"""DuckDB read-only connection for the analytics service.

The analytics service opens the same DuckDB file created by the data service,
but in read_only mode so reads never block the writer and vice-versa.
"""

from collections.abc import Generator
from contextlib import contextmanager

import duckdb

from analytics.config import settings


@contextmanager
def get_duck_conn() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Yield a read-only DuckDB connection; close it on exit."""
    conn = duckdb.connect(settings.duck_db_path, read_only=True)
    try:
        yield conn
    finally:
        conn.close()
