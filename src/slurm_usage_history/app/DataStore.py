# /src/slurm_usage_history/app/DataStore.py

import functools
import threading
import time
from abc import ABC, abstractmethod
from datetime import datetime
from functools import lru_cache
from pathlib import Path

import pandas as pd

from .account_formatter import formatter


# Decorator for measuring execution time
def timeit(func):
    """Measure execution time of a function."""

    @functools.wraps(func)
    def wrapper_timeit(*args, **kwargs):
        start_time = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed_time = time.perf_counter() - start_time
        print(f"Function '{func.__name__}' executed in {elapsed_time:.4f} seconds")
        return result

    return wrapper_timeit


# Abstract base class for data storage implementations
class DataStore(ABC):
    """Abstract base class for DataStore implementations."""

    def __init__(self, directory: str | None = None, auto_refresh_interval: int = 600):
        """
        Initialize the DataStore with a directory path.

        Args:
            directory: Path to the data directory
            auto_refresh_interval: Refresh interval in seconds (default: 600 seconds/10 minutes)
        """
        self.directory = Path(directory).expanduser() if directory else Path.cwd()
        self.hosts = {}
        self.auto_refresh_interval = auto_refresh_interval
        self._refresh_thread = None
        self._stop_refresh_flag = threading.Event()

    @abstractmethod
    def get_hostnames(self):
        """Retrieve the list of hostnames."""

    @abstractmethod
    def load_data(self):
        """Load data into the datastore."""

    @abstractmethod
    def check_for_updates(self):
        """Check for updated or new files and reload if necessary."""

    @abstractmethod
    def filter(self, start_date=None, end_date=None, partitions=None, states=None):
        """Filter data based on the given criteria."""

    def start_auto_refresh(self, interval=None):
        """
        Start the background thread for automatic data refresh.

        Args:
            interval: Optional refresh interval in seconds. If provided, overrides
                     the interval set during initialization.
        """
        if interval is not None:
            if not isinstance(interval, int) or interval <= 0:
                raise ValueError("Refresh interval must be a positive integer")
            self.auto_refresh_interval = interval

        if self._refresh_thread is not None and self._refresh_thread.is_alive():
            print("Auto-refresh is already running")
            return

        self._stop_refresh_flag.clear()
        self._refresh_thread = threading.Thread(target=self._auto_refresh_worker, daemon=True, name="DataStore-AutoRefresh")
        self._refresh_thread.start()
        print(f"Started auto-refresh thread (every {self.auto_refresh_interval} seconds)")

    def stop_auto_refresh(self):
        """Stop the background thread for automatic data refresh."""
        if self._refresh_thread is None or not self._refresh_thread.is_alive():
            print("No auto-refresh thread is running")
            return

        print("Stopping auto-refresh thread...")
        self._stop_refresh_flag.set()
        self._refresh_thread.join(timeout=5.0)
        if self._refresh_thread.is_alive():
            print("Warning: Auto-refresh thread did not terminate gracefully")
        else:
            print("Auto-refresh thread stopped successfully")

    def _auto_refresh_worker(self):
        """Worker method for the auto-refresh thread."""
        while not self._stop_refresh_flag.is_set():
            try:
                updated = self.check_for_updates()
                if updated:
                    print(f"Auto-refresh: Data was updated at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    print(f"Auto-refresh: No updates found at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                print(f"Error during auto-refresh: {e!s}")

            # Sleep for the specified interval, but check periodically if we should stop
            # Check every 2 seconds if we should terminate
            check_interval = 2
            for _ in range(self.auto_refresh_interval // check_interval):
                if self._stop_refresh_flag.is_set():
                    break
                time.sleep(check_interval)

    def set_refresh_interval(self, interval):
        """
        Change the auto-refresh interval.

        Args:
            interval: New refresh interval in seconds

        Returns:
            bool: True if the interval was updated, False if auto-refresh is not running
        """
        if not isinstance(interval, int) or interval <= 0:
            raise ValueError("Refresh interval must be a positive integer")

        self.auto_refresh_interval = interval
        print(f"Auto-refresh interval set to {interval} seconds")

        # Return status based on whether auto-refresh is running
        return self._refresh_thread is not None and self._refresh_thread.is_alive()


# Concrete implementation using Pandas
class PandasDataStore(DataStore):
    """DataStore implementation using Pandas with enhanced filtering capabilities."""

    def __init__(self, directory=None, auto_refresh_interval=600):
        """
        Initialize the PandasDataStore.

        Args:
            directory: Path to the data directory
            auto_refresh_interval: Refresh interval in seconds (default: 600 seconds/10 minutes)
        """
        super().__init__(directory, auto_refresh_interval)
        self._initialize_hosts()
        self._file_timestamps = {}  # Track file timestamps for change detection

    def _initialize_hosts(self):
        """Populate the `hosts` dictionary with subdirectories."""
        for entry in self.directory.iterdir():
            if entry.is_dir():
                self.hosts[entry.name] = {
                    "max_date": None,
                    "min_date": None,
                    "data": None,
                    "partitions": None,  # Will store available partitions
                    "accounts": None,  # Will store available accounts
                    "users": None,  # Will store available users
                    "qos": None,  # Will store available QOS options
                    "states": None,  # Will store available states
                }

    def get_hostnames(self):
        """Retrieve the list of hostnames."""
        return list(self.hosts.keys())

    def get_min_max_dates(self, hostname):
        """Get minimum and maximum dates for the specified hostname."""
        min_date = self.hosts[hostname]["min_date"]
        max_date = self.hosts[hostname]["max_date"]
        return min_date, max_date

    def get_partitions(self, hostname):
        """Get available partitions for the specified hostname."""
        return self.hosts[hostname]["partitions"] or []

    def get_accounts(self, hostname):
        """Get available accounts for the specified hostname."""
        return self.hosts[hostname]["accounts"] or []

    def get_users(self, hostname):
        """Get available users for the specified hostname."""
        return self.hosts[hostname]["users"] or []

    def get_qos(self, hostname):
        """Get available QOS options for the specified hostname."""
        return self.hosts[hostname]["qos"] or []

    def get_states(self, hostname):
        """Get available states for the specified hostname."""
        return self.hosts[hostname]["states"] or []

    @timeit
    def load_data(self):
        """Load all data files into the `hosts` dictionary."""
        for hostname in self.get_hostnames():
            print(f"Loading data for {hostname}...")
            self._load_host_data(hostname)

    def _load_host_data(self, hostname):
        """Load data for a specific hostname and update metadata."""
        raw_data = self._load_raw_data(hostname)
        transformed_data = self._transform_data(raw_data)
        self.hosts[hostname]["data"] = transformed_data

        # Store metadata
        self.hosts[hostname]["min_date"] = raw_data["Submit"].dt.date.min().isoformat()
        self.hosts[hostname]["max_date"] = raw_data["Submit"].dt.date.max().isoformat()

        # Store unique values for filtering
        self.hosts[hostname]["partitions"] = transformed_data["Partition"].sort_values().unique().tolist() if "Partition" in transformed_data.columns else []
        self.hosts[hostname]["accounts"] = transformed_data["Account"].sort_values().unique().tolist() if "Account" in transformed_data.columns else []
        self.hosts[hostname]["users"] = transformed_data["User"].sort_values().unique().tolist() if "User" in transformed_data.columns else []
        self.hosts[hostname]["qos"] = transformed_data["QOS"].sort_values().unique().tolist() if "QOS" in transformed_data.columns else []
        self.hosts[hostname]["states"] = transformed_data["State"].sort_values().unique().tolist() if "State" in transformed_data.columns else []

        # Store file timestamps for future change detection
        host_dir = self.directory / hostname / "weekly-data"
        self._file_timestamps[hostname] = {}
        for file_path in host_dir.glob("*.parquet"):
            self._file_timestamps[hostname][file_path] = file_path.stat().st_mtime

    def _load_raw_data(self, hostname):
        """Load all Parquet files in the directory for a specific hostname."""
        host_dir = self.directory / hostname / "weekly-data"
        if not host_dir.exists() or not host_dir.is_dir():
            raise FileNotFoundError(f"Directory not found for hostname: {hostname}")

        parquet_files = list(host_dir.glob("*.parquet"))
        if not parquet_files:
            raise FileNotFoundError(f"No Parquet files found in directory: {host_dir}")

        return pd.concat([pd.read_parquet(file) for file in parquet_files], ignore_index=True)

    @timeit
    def _transform_data(self, raw_data: pd.DataFrame):
        """Apply necessary transformations to the raw data."""
        # Ensure column existence and data types
        if "Partition" not in raw_data.columns and "Partitions" in raw_data.columns:
            # Handle case where column might be named differently
            raw_data["Partition"] = raw_data["Partitions"]

        # Handle multiple partitions per job (if stored as a list or string)
        if "Partition" in raw_data.columns and raw_data["Partition"].dtype == "object":
            # If partition is stored as a comma-separated string, take the first one
            raw_data["Partition"] = raw_data["Partition"].apply(lambda x: x.split(",")[0].strip() if isinstance(x, str) else x)

        # Add date components for filtering complete periods
        if "Submit" in raw_data.columns:
            # Extract date components
            raw_data["SubmitYear"] = raw_data["Submit"].dt.year
            raw_data["SubmitMonth"] = raw_data["Submit"].dt.month
            raw_data["SubmitWeek"] = raw_data["Submit"].dt.isocalendar().week
            raw_data["SubmitDate"] = raw_data["Submit"].dt.date

            # Create period indicators for complete filtering
            raw_data["SubmitYearMonth"] = raw_data["Submit"].dt.strftime("%Y-%m")

            # Calculate the start date of the week (Monday) for each submission
            day_of_week = raw_data["Submit"].dt.dayofweek  # Monday=0, Sunday=6
            week_start = raw_data["Submit"] - pd.to_timedelta(day_of_week, unit="D")
            raw_data["SubmitYearWeek"] = week_start.dt.strftime("%Y-%m-%d")  # Format as YYYY-MM-DD

        # Add start day if Start column exists
        if "Start" in raw_data.columns:
            raw_data["StartDay"] = raw_data["Start"].dt.date

        return raw_data

    def check_for_updates(self):
        """Check all hosts for new or changed files and reload if necessary."""
        updated = False

        for hostname in self.get_hostnames():
            host_updates = self._check_host_updates(hostname)
            if host_updates:
                print(f"Updates detected for host {hostname}, reloading data...")
                try:
                    self._load_host_data(hostname)
                    updated = True
                    # Clear the cache since data has changed
                    self._filter_data.cache_clear()
                except Exception as e:
                    print(f"Error reloading data for {hostname}: {e!s}")

        return updated

    def _check_host_updates(self, hostname):
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
            print(f"New files found for {hostname}: {len(new_files)} files")
            return True

        # Changed files (timestamp differs)
        changed_files = []
        for file_path, current_time in current_files.items():
            if file_path in old_timestamps and current_time != old_timestamps[file_path]:
                changed_files.append(file_path)

        if changed_files:
            print(f"Changed files found for {hostname}: {len(changed_files)} files")
            return True

        # No changes detected
        return False

    @lru_cache(maxsize=10)
    def _filter_data(
        self,
        hostname=None,
        start_date=None,
        end_date=None,
        partitions=None,
        accounts=None,
        users=None,
        qos=None,
        states=None,
    ):
        """
        Filter data based on multiple criteria.

        Args:
            hostname: The cluster hostname
            start_date: Start date filter
            end_date: End date filter
            partitions: Set of partitions to include
            accounts: Set of accounts to include
            users: Set of users to include
            qos: Set of QOS values to include
            states: Set of job states to include

        Returns:
            pandas.DataFrame: Filtered data
        """
        df_filtered = self.hosts[hostname]["data"]

        if start_date:
            start_date = pd.to_datetime(start_date)
            df_filtered = df_filtered[df_filtered["Submit"] >= start_date]

        if end_date:
            end_date = pd.to_datetime(end_date)
            df_filtered = df_filtered[df_filtered["Submit"] <= end_date]

        if partitions and "Partition" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["Partition"].isin(partitions)]

        if accounts and "Account" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["Account"].isin(accounts)]

        if users and "User" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["User"].isin(users)]

        if qos and "QOS" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["QOS"].isin(qos)]

        if states and "State" in df_filtered.columns:
            df_filtered = df_filtered[df_filtered["State"].isin(states)]

        return df_filtered

    def get_complete_periods(self, hostname, period_type="month"):
        """
        Get list of complete time periods available in the data.

        Args:
            hostname: The cluster hostname
            period_type: Type of period ('day', 'week', 'month', 'year')

        Returns:
            list: List of complete periods
        """
        if hostname not in self.hosts or self.hosts[hostname]["data"] is None:
            return []

        df = self.hosts[hostname]["data"]

        if period_type == "month":
            # Get year-month periods
            now = pd.Timestamp.now()
            current_year_month = now.strftime("%Y-%m")

            # All periods except current (incomplete) month
            periods = sorted(df["SubmitYearMonth"].unique().tolist())
            if current_year_month in periods:
                periods.remove(current_year_month)

            return periods

        if period_type == "week":
            # Get week start dates
            now = pd.Timestamp.now()

            # Calculate current week's start date
            current_week_start = now - pd.to_timedelta(now.dayofweek, unit="D")
            current_week_start_str = current_week_start.strftime("%Y-%m-%d")

            # All periods except current (incomplete) week
            periods = sorted(df["SubmitYearWeek"].unique().tolist())
            if current_week_start_str in periods:
                periods.remove(current_week_start_str)

            return periods

        if period_type == "year":
            # Get years
            now = pd.Timestamp.now()
            current_year = now.year

            # All years except current (incomplete) year
            years = sorted(df["SubmitYear"].unique().tolist())
            if current_year in years:
                years.remove(current_year)

            return [str(year) for year in years]

        return []

    def filter(
        self,
        hostname,
        start_date=None,
        end_date=None,
        partitions=None,
        accounts=None,
        users=None,
        qos=None,
        states=None,
        complete_periods_only=False,
        period_type="month",
        format_accounts=True,
        account_segments=None,
    ):
        """
        Public method to filter data with enhanced options.

        Args:
            hostname: The cluster hostname
            start_date: Start date filter
            end_date: End date filter
            partitions: List of partitions to include
            accounts: List of accounts to include
            users: List of users to include
            qos: List of QOS values to include
            states: List of job states to include
            complete_periods_only: Whether to include only complete time periods
            period_type: Type of period when using complete_periods_only ('day', 'week', 'month', 'year')
            format_accounts: Whether to apply account name formatting (default: True)
            account_segments: Number of segments to keep (None = use global setting)

        Returns:
            pandas.DataFrame: Filtered data
        """
        if not hostname or hostname not in self.hosts or self.hosts[hostname]["data"] is None:
            # Return empty DataFrame if no data is available
            return pd.DataFrame()

        # Start with basic filtering
        df_filtered = self._filter_data(
            hostname=hostname,
            start_date=start_date if start_date else self.hosts[hostname]["min_date"],
            end_date=end_date if end_date else self.hosts[hostname]["max_date"],
            partitions=frozenset(partitions) if partitions else None,
            accounts=frozenset(accounts) if accounts else None,
            users=frozenset(users) if users else None,
            qos=frozenset(qos) if qos else None,
            states=frozenset(states) if states else None,
        )

        # Apply complete periods filter if requested
        if complete_periods_only and df_filtered.shape[0] > 0:
            now = pd.Timestamp.now()

            if period_type == "month":
                # Exclude current month
                current_year_month = now.strftime("%Y-%m")
                df_filtered = df_filtered[df_filtered["SubmitYearMonth"] != current_year_month]

            elif period_type == "week":
                # Calculate current week's start date
                current_week_start = now - pd.to_timedelta(now.dayofweek, unit="D")
                current_week_start_str = current_week_start.strftime("%Y-%m-%d")

                # Exclude current week
                df_filtered = df_filtered[df_filtered["SubmitYearWeek"] != current_week_start_str]

            elif period_type == "year":
                # Exclude current year
                current_year = now.year
                df_filtered = df_filtered[df_filtered["SubmitYear"] != current_year]

        # Apply account formatting if requested
        if format_accounts and "Account" in df_filtered.columns and df_filtered.shape[0] > 0:
            # Create a copy to avoid modifying the cached data
            df_filtered = df_filtered.copy()

            # Import our global formatter
            global formatter

            # Apply formatting with custom segments if specified
            if account_segments is not None:
                # Temporarily store the current setting
                original_segments = formatter.max_segments

                # Apply custom segments just for this filter operation
                formatter.max_segments = account_segments
                df_filtered["Account"] = df_filtered["Account"].apply(formatter.format_account)

                # Restore original setting
                formatter.max_segments = original_segments
            else:
                # Use current global setting
                df_filtered["Account"] = df_filtered["Account"].apply(formatter.format_account)

        return df_filtered
