"""
Database connection management
"""

import duckdb
from contextlib import contextmanager
from typing import Generator
from app.config import get_settings


@contextmanager
def get_db_connection() -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """
    Context manager for database connections
    
    Yields:
        DuckDB connection
        
    Example:
        with get_db_connection() as conn:
            result = conn.execute("SELECT * FROM table").fetchall()
    """
    settings = get_settings()
    conn = None
    try:
        conn = duckdb.connect(settings.database_path, read_only=True)
        yield conn
    finally:
        if conn:
            conn.close()


def execute_query(query: str, params: list = None):
    """
    Execute a query and return results
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        Query results
    """
    with get_db_connection() as conn:
        if params:
            return conn.execute(query, params).fetchall()
        return conn.execute(query).fetchall()


def execute_query_one(query: str, params: list = None):
    """
    Execute a query and return single result
    
    Args:
        query: SQL query string
        params: Query parameters
        
    Returns:
        Single query result or None
    """
    with get_db_connection() as conn:
        if params:
            return conn.execute(query, params).fetchone()
        return conn.execute(query).fetchone()