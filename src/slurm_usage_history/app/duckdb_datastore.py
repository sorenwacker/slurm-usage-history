"""DuckDB-based DataStore for efficient querying of parquet files.

This implementation uses DuckDB to query parquet files directly without
loading all data into memory, providing much better performance and
scalability compared to the pandas-based approach.
"""

import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

logger = logging.getLogger(__name__)


class Singleton(type):
    """Metaclass to implement the Singleton pattern."""

    _instances: dict[type, Any] = {}
    _lock: threading.Lock = threading.Lock()

    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
            return cls._instances[cls]


class DuckDBDataStore(metaclass=Singleton):
    """DataStore implementation using DuckDB for efficient parquet querying.

    Advantages over PandasDataStore:
    - Low memory usage (queries parquet directly, no loading into RAM)
    - Fast aggregations (DuckDB is optimized for analytics)
    - Handles large datasets efficiently
    - Can work with all historical data without memory constraints
    """

    def __init__(
        self,
        directory: str | Path | None = None,
        auto_refresh_interval: int = 600,
        account_formatter: Any | None = None,
    ):
        """Initialize the DuckDBDataStore.

        Args:
            directory: Path to the data directory
            auto_refresh_interval: Refresh interval in seconds
            account_formatter: Formatter for account names
        """
        self.directory = Path(directory).expanduser() if directory else Path.cwd()
        self.auto_refresh_interval = auto_refresh_interval
        self.account_formatter = account_formatter
        self._refresh_thread: threading.Thread | None = None
        self._stop_refresh_flag: threading.Event = threading.Event()
        self._file_timestamps: dict[str, dict[Path, float]] = {}

        # Metadata cache (lightweight)
        self.hosts: dict[str, dict[str, Any]] = {}

        # DuckDB connection (thread-local for thread safety)
        self._local = threading.local()

        self._initialize_hosts()

        # Import account formatter if not provided
        if account_formatter is None:
            try:
                from .account_formatter import formatter as default_formatter

                self.account_formatter = default_formatter
            except ImportError:
                self.account_formatter = None

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get a thread-local DuckDB connection.

        DuckDB connections are not thread-safe, so we maintain one per thread.
        """
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = duckdb.connect(":memory:")
            # Install and load parquet extension
            self._local.conn.execute("INSTALL parquet")
            self._local.conn.execute("LOAD parquet")
        return self._local.conn

    def _initialize_hosts(self) -> None:
        """Scan directory for hostnames and initialize metadata."""
        for entry in self.directory.iterdir():
            if entry.is_dir():
                self.hosts[entry.name] = {
                    "max_date": None,
                    "min_date": None,
                    "partitions": None,
                    "accounts": None,
                    "users": None,
                    "qos": None,
                    "states": None,
                    "parquet_files": [],
                }

    def get_hostnames(self) -> list[str]:
        """Retrieve the list of hostnames."""
        return list(self.hosts.keys())

    def load_data(self) -> None:
        """Load metadata for all hosts.

        Unlike PandasDataStore, this doesn't load actual data into memory.
        It only scans parquet files to extract metadata like date ranges
        and unique values for filters.
        """
        for hostname in self.get_hostnames():
            logger.info(f"Loading metadata for {hostname}...")
            self._load_host_metadata(hostname)

    def _load_host_metadata(self, hostname: str) -> None:
        """Load metadata for a specific hostname.

        Args:
            hostname: The hostname to load metadata for
        """
        host_dir = self.directory / hostname / "weekly-data"
        if not host_dir.exists() or not host_dir.is_dir():
            logger.warning(f"Directory not found for hostname: {hostname}")
            return

        parquet_files = list(host_dir.glob("*.parquet"))
        if not parquet_files:
            logger.warning(f"No Parquet files found in directory: {host_dir}")
            return

        # Store file paths for this host
        self.hosts[hostname]["parquet_files"] = parquet_files

        # Store file timestamps for change detection
        self._file_timestamps[hostname] = {}
        for file_path in parquet_files:
            self._file_timestamps[hostname][file_path] = file_path.stat().st_mtime

        # Build file list for DuckDB query
        file_pattern = str(host_dir / "*.parquet")

        # Get connection
        conn = self._get_connection()

        try:
            # Query metadata from parquet files (fast, only scans metadata)
            # Get date ranges
            result = conn.execute(
                f"""
                SELECT
                    MIN(Submit) as min_date,
                    MAX(Submit) as max_date
                FROM read_parquet('{file_pattern}')
                """
            ).fetchone()

            if result:
                min_date, max_date = result
                self.hosts[hostname]["min_date"] = min_date.strftime("%Y-%m-%d") if min_date else None
                self.hosts[hostname]["max_date"] = max_date.strftime("%Y-%m-%d") if max_date else None

            # Get unique values for filters (this might be slow for large datasets)
            # We'll query each column separately to avoid loading everything
            for col, key in [
                ("Partition", "partitions"),
                ("Account", "accounts"),
                ("User", "users"),
                ("QOS", "qos"),
                ("State", "states"),
            ]:
                try:
                    unique_values = conn.execute(
                        f"""
                        SELECT DISTINCT {col}
                        FROM read_parquet('{file_pattern}')
                        WHERE {col} IS NOT NULL
                        ORDER BY {col}
                        """
                    ).fetchall()
                    self.hosts[hostname][key] = [val[0] for val in unique_values]
                except Exception as e:
                    logger.warning(f"Could not load unique values for {col}: {e}")
                    self.hosts[hostname][key] = []

            logger.info(f"Loaded metadata for {hostname}: {len(parquet_files)} files, date range {self.hosts[hostname]['min_date']} to {self.hosts[hostname]['max_date']}")

        except Exception as e:
            logger.error(f"Error loading metadata for {hostname}: {e}")
            # Set defaults
            self.hosts[hostname]["min_date"] = None
            self.hosts[hostname]["max_date"] = None
            for key in ["partitions", "accounts", "users", "qos", "states"]:
                self.hosts[hostname][key] = []

    def get_min_max_dates(self, hostname: str) -> tuple[str | None, str | None]:
        """Get minimum and maximum dates for the specified hostname."""
        return self.hosts[hostname]["min_date"], self.hosts[hostname]["max_date"]

    def get_partitions(self, hostname: str) -> list[str]:
        """Get available partitions for the specified hostname."""
        return self.hosts[hostname]["partitions"] or []

    def get_accounts(self, hostname: str) -> list[str]:
        """Get available accounts for the specified hostname."""
        return self.hosts[hostname]["accounts"] or []

    def get_users(self, hostname: str) -> list[str]:
        """Get available users for the specified hostname."""
        return self.hosts[hostname]["users"] or []

    def get_qos(self, hostname: str) -> list[str]:
        """Get available QOS options for the specified hostname."""
        return self.hosts[hostname]["qos"] or []

    def get_states(self, hostname: str) -> list[str]:
        """Get available states for the specified hostname."""
        return self.hosts[hostname]["states"] or []

    def filter(
        self,
        hostname: str,
        start_date: str | None = None,
        end_date: str | None = None,
        partitions: list[str] | None = None,
        accounts: list[str] | None = None,
        users: list[str] | None = None,
        qos: list[str] | None = None,
        states: list[str] | None = None,
        complete_periods_only: bool = False,
        period_type: str = "month",
        format_accounts: bool = True,
        account_segments: int | None = None,
    ) -> pd.DataFrame:
        """Filter data using DuckDB and return as pandas DataFrame.

        This method builds a SQL query to filter the parquet files directly,
        only loading the filtered results into memory.

        Args:
            hostname: The hostname to query
            start_date: Start date filter (YYYY-MM-DD)
            end_date: End date filter (YYYY-MM-DD)
            partitions: List of partitions to include
            accounts: List of accounts to include
            users: List of users to include
            qos: List of QOS values to include
            states: List of states to include
            complete_periods_only: Not used in DuckDB implementation (kept for compatibility)
            period_type: Not used in DuckDB implementation (kept for compatibility)
            format_accounts: Whether to format account names
            account_segments: Number of segments for account formatting

        Returns:
            Filtered DataFrame
        """
        host_dir = self.directory / hostname / "weekly-data"
        file_pattern = str(host_dir / "*.parquet")

        # Build WHERE clause
        where_clauses = []

        if start_date:
            where_clauses.append(f"Submit >= '{start_date}'")
        if end_date:
            where_clauses.append(f"Submit <= '{end_date}'")
        if partitions:
            partition_list = "', '".join(partitions)
            where_clauses.append(f"Partition IN ('{partition_list}')")
        if accounts:
            account_list = "', '".join(accounts)
            where_clauses.append(f"Account IN ('{account_list}')")
        if users:
            user_list = "', '".join(users)
            where_clauses.append(f"User IN ('{user_list}')")
        if qos:
            qos_values = "', '".join(qos)
            where_clauses.append(f"QOS IN ('{qos_values}')")
        if states:
            state_list = "', '".join(states)
            where_clauses.append(f"State IN ('{state_list}')")

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Build and execute query
        query = f"""
        SELECT *
        FROM read_parquet('{file_pattern}')
        WHERE {where_sql}
        """

        conn = self._get_connection()
        df = conn.execute(query).df()

        # Apply account formatting if requested and available
        if format_accounts and self.account_formatter and "Account" in df.columns:
            segments = account_segments if account_segments is not None else 3
            df["Account"] = df["Account"].apply(
                lambda x: self.account_formatter.format_account_name(x, segments=segments)
            )

        return df

    def start_auto_refresh(self, interval: int | None = None) -> None:
        """Start the background thread for automatic data refresh."""
        if interval is not None:
            if not isinstance(interval, int) or interval <= 0:
                msg = "Refresh interval must be a positive integer"
                raise ValueError(msg)
            self.auto_refresh_interval = interval

        if self._refresh_thread is not None and self._refresh_thread.is_alive():
            logger.info("Auto-refresh is already running")
            return

        self._stop_refresh_flag.clear()
        self._refresh_thread = threading.Thread(
            target=self._auto_refresh_worker, daemon=True, name="DuckDBDataStore-AutoRefresh"
        )
        self._refresh_thread.start()
        logger.info(f"Started auto-refresh thread (every {self.auto_refresh_interval} seconds)")

    def stop_auto_refresh(self) -> None:
        """Stop the background thread for automatic data refresh."""
        if self._refresh_thread is None or not self._refresh_thread.is_alive():
            logger.info("No auto-refresh thread is running")
            return

        logger.info("Stopping auto-refresh thread...")
        self._stop_refresh_flag.set()
        self._refresh_thread.join(timeout=5.0)
        if self._refresh_thread.is_alive():
            logger.warning("Warning: Auto-refresh thread did not terminate gracefully")
        else:
            logger.info("Auto-refresh thread stopped successfully")

    def _auto_refresh_worker(self) -> None:
        """Worker method for the auto-refresh thread."""
        while not self._stop_refresh_flag.is_set():
            try:
                updated = self.check_for_updates()
                if updated:
                    logger.info(f"Auto-refresh: Data was updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    logger.debug(f"Auto-refresh: No updates found at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                logger.error(f"Error during auto-refresh: {e!s}")

            # Sleep for the specified interval, but check periodically if we should stop
            check_interval = 2
            for _ in range(self.auto_refresh_interval // check_interval):
                if self._stop_refresh_flag.is_set():
                    break
                time.sleep(check_interval)

    def check_for_updates(self) -> bool:
        """Check all hosts for new or changed files and reload metadata if necessary."""
        updated = False

        for hostname in self.get_hostnames():
            host_updates = self._check_host_updates(hostname)
            if host_updates:
                logger.info(f"Updates detected for host {hostname}, reloading metadata...")
                try:
                    self._load_host_metadata(hostname)
                    updated = True
                except Exception as e:
                    logger.error(f"Error reloading metadata for {hostname}: {e!s}")

        return updated

    def _check_host_updates(self, hostname: str) -> bool:
        """Check if files for a specific host have been updated or new files added."""
        host_dir = self.directory / hostname / "weekly-data"
        if not host_dir.exists() or not host_dir.is_dir():
            return False

        # Get current files and their timestamps
        current_files = {}
        for file_path in host_dir.glob("*.parquet"):
            current_files[file_path] = file_path.stat().st_mtime

        # If this is our first check for this hostname, store timestamps and return
        if hostname not in self._file_timestamps:
            self._file_timestamps[hostname] = current_files
            return False

        # Check for changes or new files
        old_timestamps = self._file_timestamps[hostname]

        # New files
        new_files = set(current_files.keys()) - set(old_timestamps.keys())
        if new_files:
            return True

        # Deleted files
        deleted_files = set(old_timestamps.keys()) - set(current_files.keys())
        if deleted_files:
            return True

        # Modified files
        for file_path in current_files:
            if file_path in old_timestamps and current_files[file_path] != old_timestamps[file_path]:
                return True

        return False
