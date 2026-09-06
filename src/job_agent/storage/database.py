from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any

import structlog

from job_agent.exceptions import StorageError, MigrationError

logger = structlog.get_logger(__name__)


class DatabaseManager:
    """Manages SQLite database connections and migrations."""

    _instance = None
    _lock = threading.Lock()

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._local = threading.local()

    @classmethod
    def get_instance(cls, db_path: str | Path) -> DatabaseManager:
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls(db_path)
            return cls._instance

    def connect(self) -> sqlite3.Connection:
        if not hasattr(self._local, "connection") or self._local.connection is None:
            try:
                # Ensure parent directory exists
                self.db_path.parent.mkdir(parents=True, exist_ok=True)

                conn = sqlite3.connect(
                    self.db_path,
                    timeout=30.0,
                    detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
                )
                conn.row_factory = sqlite3.Row
                
                # Enable WAL mode and set busy timeout
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA busy_timeout=5000;")
                conn.execute("PRAGMA synchronous=NORMAL;")
                conn.execute("PRAGMA foreign_keys=ON;")
                
                self._local.connection = conn
            except sqlite3.Error as e:
                logger.error("failed_to_connect", error=str(e), path=str(self.db_path))
                raise StorageError(f"Failed to connect to database: {e}") from e
        return self._local.connection

    def get_connection(self) -> sqlite3.Connection:
        return self.connect()

    def close(self) -> None:
        if hasattr(self._local, "connection") and self._local.connection is not None:
            try:
                self._local.connection.close()
            except sqlite3.Error as e:
                logger.error("failed_to_close", error=str(e))
            finally:
                self._local.connection = None

    def execute(self, sql: str, params: tuple | dict = ()) -> sqlite3.Cursor:
        conn = self.get_connection()
        try:
            return conn.execute(sql, params)
        except sqlite3.Error as e:
            logger.error("execute_failed", error=str(e), sql=sql)
            raise StorageError(f"Database execution failed: {e}") from e

    def executemany(self, sql: str, params_list: list[tuple] | list[dict]) -> sqlite3.Cursor:
        conn = self.get_connection()
        try:
            return conn.executemany(sql, params_list)
        except sqlite3.Error as e:
            logger.error("executemany_failed", error=str(e), sql=sql)
            raise StorageError(f"Database batch execution failed: {e}") from e

    def __enter__(self) -> DatabaseManager:
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def run_migrations(self) -> None:
        conn = self.get_connection()
        migrations_dir = Path(__file__).parent / "migrations"
        
        if not migrations_dir.exists() or not migrations_dir.is_dir():
            logger.warning("migrations_dir_not_found", path=str(migrations_dir))
            return

        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        try:
            # Check if schema_migrations exists, to avoid failing on first run
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='schema_migrations'"
            )
            table_exists = cursor.fetchone() is not None
            
            applied_migrations = set()
            if table_exists:
                cursor = conn.execute("SELECT version FROM schema_migrations")
                applied_migrations = {row["version"] for row in cursor.fetchall()}

            for migration_file in migration_files:
                version = migration_file.stem
                if version in applied_migrations:
                    continue
                    
                logger.info("applying_migration", version=version)
                with open(migration_file, "r", encoding="utf-8") as f:
                    sql_script = f.read()

                with conn:
                    conn.executescript(sql_script)
                    conn.execute(
                        "INSERT INTO schema_migrations (version) VALUES (?)", (version,)
                    )
                logger.info("migration_applied", version=version)
                
        except sqlite3.Error as e:
            logger.error("migration_failed", error=str(e))
            raise MigrationError(f"Migration failed: {e}") from e
