"""API endpoints for aggregated chart data.

This module provides endpoints that return pre-aggregated chart data instead of raw job records,
significantly improving performance by reducing payload size and leveraging pandas aggregation speed.
"""
from datetime import datetime
from typing import Any, Optional, TYPE_CHECKING

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException

from ..core.config import get_settings
from ..models.data_models import FilterRequest

# Import datastore
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

if TYPE_CHECKING:
    from slurm_usage_history.app.datastore import PandasDataStore

try:
    from slurm_usage_history.app.datastore import PandasDataStore
except ImportError:
    PandasDataStore = None  # type: ignore

router = APIRouter()
settings = get_settings()

# Global datastore instance
_datastore: Optional["PandasDataStore"] = None


def get_datastore() -> PandasDataStore:
    """Get or initialize the datastore singleton."""
    global _datastore
    if _datastore is None:
        if PandasDataStore is None:
            raise HTTPException(status_code=500, detail="DataStore not available")
        _datastore = PandasDataStore(directory=settings.data_path)
        _datastore.load_data()
        _datastore.start_auto_refresh(interval=settings.auto_refresh_interval)
    return _datastore


@router.post("/charts")
async def get_aggregated_charts(request: FilterRequest) -> dict[str, Any]:
    """Get all aggregated chart data in a single request.

    This endpoint performs all aggregations on the backend using pandas,
    returning only the aggregated data needed for charts. This reduces
    the payload from ~138MB to ~10-50KB.

    Args:
        request: Filter parameters (hostname, dates, partitions, accounts, etc.)

    Returns:
        Dictionary containing all aggregated chart data
    """
    try:
        datastore = get_datastore()

        # Apply filters to get the base dataset
        df = datastore.filter(
            hostname=request.hostname,
            start_date=request.start_date,
            end_date=request.end_date,
            partitions=request.partitions,
            accounts=request.accounts,
            users=request.users,
            qos=request.qos,
            states=request.states,
            complete_periods_only=request.complete_periods_only,
            period_type=request.period_type,
        )

        if df.empty:
            return _empty_charts_response()

        # Apply account formatting if requested
        if request.account_segments:
            df = _format_accounts_in_df(df, request.account_segments)

        # Generate all chart aggregations
        period_type = request.period_type or "month"
        color_by = request.color_by  # Can be: Account, Partition, State, QOS, User, or None

        # Get node usage data
        node_usage = _aggregate_node_usage(
            df,
            color_by=color_by,
            hide_unused=request.hide_unused_nodes,
            sort_by_usage=request.sort_by_usage,
        )

        charts_data = {
            "summary": _generate_summary(df),
            "cpu_usage_over_time": _aggregate_cpu_usage_over_time(df, period_type, color_by),
            "gpu_usage_over_time": _aggregate_gpu_usage_over_time(df, period_type, color_by),
            "active_users_over_time": _aggregate_active_users_over_time(df, period_type, color_by),
            "jobs_over_time": _aggregate_jobs_over_time(df, period_type, color_by),
            # Distribution charts - use color_by for dynamic grouping
            "jobs_by_account": _aggregate_by_dimension(df, color_by, metric="count", period_type=period_type),
            "jobs_by_partition": _aggregate_jobs_by_partition(df),  # Keep for now
            "jobs_by_state": _aggregate_jobs_by_state(df),  # Keep for now
            # Timing histograms (always ungrouped - ignore color_by)
            "waiting_times_hist": _aggregate_waiting_times_hist(df, None),
            "job_duration_hist": _aggregate_job_duration_hist(df, None),
            # Distribution charts
            "active_users_distribution": _aggregate_active_users_distribution(df, period_type, color_by),
            "jobs_distribution": _aggregate_jobs_distribution(df, period_type, color_by),
            # Stacked percentage charts (new)
            "job_duration_stacked": _aggregate_job_duration_stacked(df, period_type),
            "waiting_times_stacked": _aggregate_waiting_times_stacked(df, period_type),
            # Timing over time (always ungrouped - ignore color_by)
            "waiting_times_over_time": _aggregate_waiting_times_over_time(df, period_type, None),
            "job_duration_over_time": _aggregate_job_duration_over_time(df, period_type, None),
            # Timing trends (always ungrouped - ignore color_by)
            "waiting_times_trends": _aggregate_waiting_times_trends(df, period_type, None),
            "job_duration_trends": _aggregate_job_duration_trends(df, period_type, None),
            # Resource allocation
            "cpus_per_job": _aggregate_cpus_per_job(df),
            "gpus_per_job": _aggregate_gpus_per_job(df),
            "nodes_per_job": _aggregate_nodes_per_job(df),
            # Resource distribution charts - use color_by for dynamic grouping (with period_type for histogram mode)
            "cpu_hours_by_account": _aggregate_by_dimension(df, color_by, metric="CPUHours", period_type=period_type),
            "gpu_hours_by_account": _aggregate_by_dimension(df, color_by, metric="GPUHours", period_type=period_type),
            # Node usage charts
            "node_cpu_usage": node_usage["cpu_usage"],
            "node_gpu_usage": node_usage["gpu_usage"],
        }

        return charts_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating charts: {str(e)}")


def _empty_charts_response() -> dict[str, Any]:
    """Return empty chart data structure."""
    return {
        "summary": {"total_jobs": 0, "total_cpu_hours": 0, "total_gpu_hours": 0, "total_users": 0},
        "cpu_usage_over_time": {"x": [], "y": []},
        "gpu_usage_over_time": {"x": [], "y": []},
        "active_users_over_time": {"x": [], "y": []},
        "jobs_over_time": {"x": [], "y": []},
        "jobs_by_account": {"x": [], "y": []},
        "jobs_by_partition": {"x": [], "y": []},
        "jobs_by_state": {"labels": [], "values": []},
        "waiting_times_hist": {"x": [], "y": []},
        "job_duration_hist": {"x": [], "y": []},
        "waiting_times_over_time": {"x": [], "y": []},
        "job_duration_over_time": {"x": [], "y": []},
        "cpus_per_job": {"x": [], "y": []},
        "gpus_per_job": {"x": [], "y": []},
        "nodes_per_job": {"x": [], "y": []},
        "cpu_hours_by_account": {"x": [], "y": []},
        "gpu_hours_by_account": {"x": [], "y": []},
        "node_cpu_usage": {"x": [], "y": []},
        "node_gpu_usage": {"x": [], "y": []},
    }


def _generate_summary(df: pd.DataFrame) -> dict[str, Any]:
    """Generate summary statistics."""
    return {
        "total_jobs": int(len(df)),
        "total_cpu_hours": float(df["CPUHours"].sum()) if "CPUHours" in df.columns else 0.0,
        "total_gpu_hours": float(df["GPUHours"].sum()) if "GPUHours" in df.columns else 0.0,
        "total_users": int(df["User"].nunique()) if "User" in df.columns else 0,
    }


def _format_account_name(account: str, max_segments: int | None = None, separator: str = "-") -> str:
    """Format account name by keeping first N segments.

    Args:
        account: Account name to format (e.g., "ewi-insy-prb")
        max_segments: Number of segments to keep (None or 0 = keep all)
        separator: Separator character (default: "-")

    Returns:
        Formatted account name (e.g., "ewi-insy" with max_segments=2)

    Examples:
        >>> _format_account_name("ewi-insy-prb", max_segments=2)
        'ewi-insy'
        >>> _format_account_name("ewi-insy-prb", max_segments=1)
        'ewi'
        >>> _format_account_name("ewi-insy-prb", max_segments=None)
        'ewi-insy-prb'
    """
    if not max_segments or max_segments == 0:
        return account

    if not isinstance(account, str):
        return account

    segments = account.split(separator)
    return separator.join(segments[:max_segments])


def _format_accounts_in_df(df: pd.DataFrame, account_segments: int | None = None) -> pd.DataFrame:
    """Apply account formatting to the Account column in a DataFrame.

    Args:
        df: DataFrame with 'Account' column
        account_segments: Number of segments to keep in account names

    Returns:
        DataFrame with formatted account names
    """
    if account_segments and "Account" in df.columns and not df.empty:
        df = df.copy()
        df["Account"] = df["Account"].apply(lambda x: _format_account_name(x, account_segments))

    return df


def _aggregate_by_dimension(df: pd.DataFrame, group_by: str | None, metric: str = "count", top_n: int = 10, period_type: str = "month") -> dict[str, list]:
    """Generic aggregation function that groups by a dimension.

    Args:
        df: Input DataFrame
        group_by: Column to group by (Account, Partition, State, QOS, User, or None)
        metric: What to aggregate - 'count' for job counts, 'CPUHours', or 'GPUHours'
        top_n: Number of top groups to return
        period_type: Time period type (day, week, month, year) - used for histogram mode

    Returns:
        When group_by is None: Histogram data {"x": bins, "y": counts, "mean": value, "median": value, "type": "histogram"}
        When group_by is set: Bar chart data {"x": labels, "y": values}
    """
    # Map of valid group_by values to DataFrame column names
    column_map = {
        "Account": "Account",
        "Partition": "Partition",
        "State": "State",
        "QOS": "QOS",
        "User": "User",
    }

    # If no grouping, behavior depends on metric type
    if not group_by or group_by not in column_map:
        import numpy as np

        # For CPU/GPU hours: create per-period histogram (matching original Dash behavior)
        if metric in ["CPUHours", "GPUHours"]:
            if metric not in df.columns:
                return {"x": [], "y": [], "mean": 0, "median": 0, "type": "histogram"}

            # Get time column based on period type
            time_column_map = {
                "day": "SubmitDay",
                "week": "SubmitYearWeek",
                "month": "SubmitYearMonth",
                "year": "SubmitYear",
            }
            time_column = time_column_map.get(period_type, "SubmitYearMonth")

            # Handle year extraction if needed
            df_copy = df
            if time_column not in df.columns:
                if period_type == "year" and "SubmitYearMonth" in df.columns:
                    df_copy = df.copy()
                    df_copy["SubmitYear"] = df_copy["SubmitYearMonth"].astype(str).str[:4]
                else:
                    return {"x": [], "y": [], "mean": 0, "median": 0, "type": "histogram"}

            # Group by time period and sum hours
            usage_per_period = df_copy.groupby(time_column)[metric].sum()

            if len(usage_per_period) == 0:
                return {"x": [], "y": [], "mean": 0, "median": 0, "type": "histogram"}

            # Calculate mean and median
            mean_val = float(usage_per_period.mean())
            median_val = float(usage_per_period.median())

            # Create histogram with 20 bins (matching original)
            n_bins = 20
            counts, bin_edges = np.histogram(usage_per_period, bins=n_bins)

            # Use bin centers for plotting
            bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]

            return {
                "x": bin_centers,
                "y": counts.tolist(),
                "mean": mean_val,
                "median": median_val,
                "type": "histogram",  # Flag to indicate this is a histogram
            }

        # For job counts: create histogram showing distribution of jobs per user
        if "User" not in df.columns:
            return {"x": [], "y": [], "mean": 0, "median": 0}

        # Count jobs per user
        jobs_per_user = df["User"].value_counts()

        if len(jobs_per_user) == 0:
            return {"x": [], "y": [], "mean": 0, "median": 0}

        # Calculate mean and median from the raw data
        mean_val = float(jobs_per_user.mean())
        median_val = float(jobs_per_user.median())

        # Use automatic binning with pandas/numpy histogram
        # Determine optimal number of bins using Sturges' rule or sqrt
        n_bins = min(30, max(10, int(np.ceil(np.sqrt(len(jobs_per_user))))))

        # Create histogram with automatic binning
        counts, bin_edges = np.histogram(jobs_per_user, bins=n_bins)

        # Create bin labels as "low-high"
        bin_labels = [f"{int(bin_edges[i])}-{int(bin_edges[i+1])}" for i in range(len(bin_edges)-1)]

        # Use bin centers for plotting (better for continuous data)
        bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]

        return {
            "x": bin_centers,  # Use bin centers for better positioning
            "y": counts.tolist(),
            "mean": mean_val,
            "median": median_val,
            "bin_labels": bin_labels,  # For hover text
        }

    group_column = column_map.get(group_by, "Account")

    # Check if column exists
    if group_column not in df.columns:
        return {"x": [], "y": []}

    # Aggregate based on metric type
    if metric == "count":
        # Count jobs per group
        grouped = df[group_column].value_counts().head(top_n)
    elif metric in ["CPUHours", "GPUHours"]:
        # Sum hours per group
        if metric not in df.columns:
            return {"x": [], "y": []}
        grouped = df.groupby(group_column)[metric].sum().sort_values(ascending=False).head(top_n)
    else:
        return {"x": [], "y": []}

    return {
        "x": grouped.index.tolist(),
        "y": grouped.values.tolist(),
    }


def _aggregate_cpu_usage_over_time(df: pd.DataFrame, period_type: str = "month", color_by: str | None = None) -> dict[str, list]:
    """Aggregate CPU usage by time period, optionally grouped by a dimension.

    Args:
        df: Input DataFrame
        period_type: Time period (day, week, month, year)
        color_by: Optional dimension to group by (Account, Partition, State, QOS, User)

    Returns:
        Without color_by: {"x": [...], "y": [...]}
        With color_by: {"x": [...], "series": [{"name": "group", "data": [...]}, ...]}
    """
    if "CPUHours" not in df.columns:
        return {"x": [], "y": []}

    # Select time column based on period type
    # CRITICAL: Use Start time, not Submit time (matching original Dash implementation)
    time_column_map = {
        "day": "StartDay",
        "week": "StartYearWeek",
        "month": "StartYearMonth",
        "year": "StartYear",
    }
    time_column = time_column_map.get(period_type, "StartYearMonth")

    # Handle year extraction if needed
    df_copy = df
    if time_column not in df.columns:
        if period_type == "year" and "StartYearMonth" in df.columns:
            df_copy = df.copy()
            df_copy["StartYear"] = df_copy["StartYearMonth"].astype(str).str[:4]
        else:
            return {"x": [], "y": []}

    # If no color_by, return simple time series (backward compatible)
    if not color_by or color_by not in df_copy.columns:
        grouped = df_copy.groupby(time_column)["CPUHours"].sum().sort_index()
        return {
            "x": grouped.index.tolist(),
            "y": grouped.values.tolist(),
        }

    # With color_by, return multi-series data for stacked chart
    # Group by time AND dimension
    grouped = df_copy.groupby([time_column, color_by])["CPUHours"].sum().reset_index()

    # Get top 10 groups by total CPU hours
    top_groups = grouped.groupby(color_by)["CPUHours"].sum().nlargest(10).index.tolist()
    grouped_filtered = grouped[grouped[color_by].isin(top_groups)]

    # Get all time periods (sorted)
    all_periods = sorted(df_copy[time_column].unique())

    # Build series for each group
    series = []
    for group in top_groups:
        group_data = grouped_filtered[grouped_filtered[color_by] == group]
        # Create a complete series with 0 for missing periods
        data = []
        for period in all_periods:
            period_value = group_data[group_data[time_column] == period]["CPUHours"].sum()
            data.append(float(period_value) if period_value > 0 else 0.0)

        series.append({
            "name": str(group),
            "data": data,
        })

    return {
        "x": all_periods,
        "series": series,
    }


def _aggregate_gpu_usage_over_time(df: pd.DataFrame, period_type: str = "month", color_by: str | None = None) -> dict[str, list]:
    """Aggregate GPU usage by time period, optionally grouped by a dimension.

    Args:
        df: Input DataFrame
        period_type: Time period (day, week, month, year)
        color_by: Optional dimension to group by (Account, Partition, State, QOS, User)

    Returns:
        Without color_by: {"x": [...], "y": [...]}
        With color_by: {"x": [...], "series": [{"name": "group", "data": [...]}, ...]}
    """
    if "GPUHours" not in df.columns:
        return {"x": [], "y": []}

    # Select time column based on period type
    # CRITICAL: Use Start time, not Submit time (matching original Dash implementation)
    time_column_map = {
        "day": "StartDay",
        "week": "StartYearWeek",
        "month": "StartYearMonth",
        "year": "StartYear",
    }
    time_column = time_column_map.get(period_type, "StartYearMonth")

    # Handle year extraction if needed
    df_copy = df
    if time_column not in df.columns:
        if period_type == "year" and "StartYearMonth" in df.columns:
            df_copy = df.copy()
            df_copy["StartYear"] = df_copy["StartYearMonth"].astype(str).str[:4]
        else:
            return {"x": [], "y": []}

    # If no color_by, return simple time series (backward compatible)
    if not color_by or color_by not in df_copy.columns:
        grouped = df_copy.groupby(time_column)["GPUHours"].sum().sort_index()
        return {
            "x": grouped.index.tolist(),
            "y": grouped.values.tolist(),
        }

    # With color_by, return multi-series data for stacked chart
    # Group by time AND dimension
    grouped = df_copy.groupby([time_column, color_by])["GPUHours"].sum().reset_index()

    # Get top 10 groups by total GPU hours
    top_groups = grouped.groupby(color_by)["GPUHours"].sum().nlargest(10).index.tolist()
    grouped_filtered = grouped[grouped[color_by].isin(top_groups)]

    # Get all time periods (sorted)
    all_periods = sorted(df_copy[time_column].unique())

    # Build series for each group
    series = []
    for group in top_groups:
        group_data = grouped_filtered[grouped_filtered[color_by] == group]
        # Create a complete series with 0 for missing periods
        data = []
        for period in all_periods:
            period_value = group_data[group_data[time_column] == period]["GPUHours"].sum()
            data.append(float(period_value) if period_value > 0 else 0.0)

        series.append({
            "name": str(group),
            "data": data,
        })

    return {
        "x": all_periods,
        "series": series,
    }


def _aggregate_active_users_over_time(df: pd.DataFrame, period_type: str = "month", color_by: str | None = None) -> dict[str, list]:
    """Aggregate active users by time period, optionally grouped by a dimension.

    Args:
        df: Input DataFrame
        period_type: Time period (day, week, month, year)
        color_by: Optional dimension to group by (Account, Partition, State, QOS, User)

    Returns:
        Without color_by: {"x": [...], "y": [...]}
        With color_by: {"x": [...], "series": [{"name": "group", "data": [...]}, ...]}
    """
    if "User" not in df.columns:
        return {"x": [], "y": []}

    # Select time column based on period type
    time_column_map = {
        "day": "SubmitDay",
        "week": "SubmitYearWeek",
        "month": "SubmitYearMonth",
        "year": "SubmitYear",
    }
    time_column = time_column_map.get(period_type, "SubmitYearMonth")

    # Handle year extraction if needed
    df_copy = df
    if time_column not in df.columns:
        if period_type == "year" and "SubmitYearMonth" in df.columns:
            df_copy = df.copy()
            df_copy["SubmitYear"] = df_copy["SubmitYearMonth"].astype(str).str[:4]
        else:
            return {"x": [], "y": []}

    # If no color_by, return simple time series (backward compatible)
    if not color_by or color_by not in df_copy.columns:
        grouped = df_copy.groupby(time_column)["User"].nunique().sort_index()
        return {
            "x": grouped.index.tolist(),
            "y": grouped.values.tolist(),
        }

    # With color_by, return multi-series data for stacked chart
    # Group by time AND dimension, count unique users
    grouped = df_copy.groupby([time_column, color_by])["User"].nunique().reset_index(name="num_active_users")

    # Get top 10 groups by total unique users across all time
    # Note: This counts unique users PER group, not sum of unique counts
    top_groups = []
    for group in df_copy[color_by].unique():
        group_users = df_copy[df_copy[color_by] == group]["User"].nunique()
        top_groups.append((group, group_users))
    top_groups = sorted(top_groups, key=lambda x: x[1], reverse=True)[:10]
    top_groups = [g[0] for g in top_groups]

    grouped_filtered = grouped[grouped[color_by].isin(top_groups)]

    # Get all time periods (sorted)
    all_periods = sorted(df_copy[time_column].unique())

    # Build series for each group
    series = []
    for group in top_groups:
        group_data = grouped_filtered[grouped_filtered[color_by] == group]
        # Create a complete series with 0 for missing periods
        data = []
        for period in all_periods:
            period_data = group_data[group_data[time_column] == period]
            period_value = period_data["num_active_users"].sum() if not period_data.empty else 0
            data.append(int(period_value))

        series.append({
            "name": str(group),
            "data": data,
        })

    return {
        "x": all_periods,
        "series": series,
    }


def _aggregate_jobs_over_time(df: pd.DataFrame, period_type: str = "month", color_by: str | None = None) -> dict[str, list]:
    """Aggregate job counts by time period, optionally grouped by a dimension.

    Args:
        df: Input DataFrame
        period_type: Time period (day, week, month, year)
        color_by: Optional dimension to group by (Account, Partition, State, QOS, User)

    Returns:
        Without color_by: {"x": [...], "y": [...]}
        With color_by: {"x": [...], "series": [{"name": "group", "data": [...]}, ...]}
    """
    # Select time column based on period type
    time_column_map = {
        "day": "SubmitDay",
        "week": "SubmitYearWeek",
        "month": "SubmitYearMonth",
        "year": "SubmitYear",
    }
    time_column = time_column_map.get(period_type, "SubmitYearMonth")

    # Handle year extraction if needed
    df_copy = df
    if time_column not in df.columns:
        if period_type == "year" and "SubmitYearMonth" in df.columns:
            df_copy = df.copy()
            df_copy["SubmitYear"] = df_copy["SubmitYearMonth"].astype(str).str[:4]
        else:
            return {"x": [], "y": []}

    # If no color_by, return simple time series (backward compatible)
    if not color_by or color_by not in df_copy.columns:
        grouped = df_copy[time_column].value_counts().sort_index()
        return {
            "x": grouped.index.tolist(),
            "y": grouped.values.tolist(),
        }

    # With color_by, return multi-series data for stacked chart
    # Group by time AND dimension, count jobs
    grouped = df_copy.groupby([time_column, color_by]).size().reset_index(name="num_jobs")

    # Get top 10 groups by total job count
    top_groups = grouped.groupby(color_by)["num_jobs"].sum().nlargest(10).index.tolist()
    grouped_filtered = grouped[grouped[color_by].isin(top_groups)]

    # Get all time periods (sorted)
    all_periods = sorted(df_copy[time_column].unique())

    # Build series for each group
    series = []
    for group in top_groups:
        group_data = grouped_filtered[grouped_filtered[color_by] == group]
        # Create a complete series with 0 for missing periods
        data = []
        for period in all_periods:
            period_data = group_data[group_data[time_column] == period]
            period_value = period_data["num_jobs"].sum() if not period_data.empty else 0
            data.append(int(period_value))

        series.append({
            "name": str(group),
            "data": data,
        })

    return {
        "x": all_periods,
        "series": series,
    }


def _aggregate_jobs_by_account(df: pd.DataFrame) -> dict[str, list]:
    """Aggregate jobs by account (top 10)."""
    if "Account" not in df.columns:
        return {"x": [], "y": []}

    counts = df["Account"].value_counts().head(10)
    return {
        "x": counts.index.tolist(),
        "y": counts.values.tolist(),
    }


def _aggregate_jobs_by_partition(df: pd.DataFrame) -> dict[str, list]:
    """Aggregate jobs by partition (top 10)."""
    if "Partition" not in df.columns:
        return {"x": [], "y": []}

    counts = df["Partition"].value_counts().head(10)
    return {
        "x": counts.index.tolist(),
        "y": counts.values.tolist(),
    }


def _aggregate_jobs_by_state(df: pd.DataFrame) -> dict[str, list]:
    """Aggregate jobs by state."""
    if "State" not in df.columns:
        return {"labels": [], "values": []}

    counts = df["State"].value_counts()
    return {
        "labels": counts.index.tolist(),
        "values": counts.values.tolist(),
    }


def _aggregate_value_histogram(
    df: pd.DataFrame,
    value_column: str,
    color_by: Optional[str] = None,
    filter_positive: bool = False
) -> dict[str, Any]:
    """Generic function to create histograms for numeric value distributions."""
    if value_column not in df.columns:
        return {"x": [], "y": [], "median": 0, "average": 0}

    # Filter data if needed
    if filter_positive:
        values = df[df[value_column] > 0][value_column].dropna()
    else:
        values = df[value_column].dropna()

    if values.empty:
        return {"x": [], "y": [], "median": 0, "average": 0}

    # Calculate overall statistics
    median_val = float(values.median())
    mean_val = float(values.mean())

    # If no grouping, return simple numeric histogram
    if not color_by or color_by == "None":
        # Use predefined bins matching the original Dash implementation
        bin_edges = [0, 1, 4, 12, 24, 72, 168, float('inf')]
        bin_labels = ["< 1h", "1h - 4h", "4h - 12h", "12h - 24h", "1d - 3d", "3d - 7d", "> 7d"]

        # Create histogram with predefined bins
        counts, _ = np.histogram(values, bins=bin_edges)

        # Convert to percentage to make it consistent with frontend expectations
        total = counts.sum()
        percentages = [(count / total * 100) if total > 0 else 0 for count in counts]

        return {
            "type": "histogram",
            "x": bin_labels,
            "y": percentages,
            "median": median_val,
            "average": mean_val,
        }

    # Grouped histogram mode when color_by is specified
    if color_by not in df.columns:
        return {"type": "histogram", "x": [], "series": []}

    # Filter df if needed
    if filter_positive:
        df = df[df[value_column] > 0]

    # Predefined bins
    bin_edges = [0, 1, 4, 12, 24, 72, 168, float('inf')]
    bin_labels = ["< 1h", "1h - 4h", "4h - 12h", "12h - 24h", "1d - 3d", "3d - 7d", "> 7d"]

    # Group by color_by dimension and create histogram for each group
    series = []
    for group_name in df[color_by].unique():
        if pd.isna(group_name):
            continue
        group_df = df[df[color_by] == group_name]
        group_values = group_df[value_column].values

        if len(group_values) == 0:
            continue

        # Create histogram with predefined bins
        counts, _ = np.histogram(group_values, bins=bin_edges)

        # Convert to percentage
        total = counts.sum()
        percentages = [(count / total * 100) if total > 0 else 0 for count in counts]

        series.append({
            "name": str(group_name),
            "data": percentages
        })

    return {
        "type": "histogram",
        "x": bin_labels,
        "series": series,
        "median": median_val,
        "average": mean_val,
    }


def _aggregate_waiting_times_hist(df: pd.DataFrame, color_by: Optional[str] = None) -> dict[str, Any]:
    """Aggregate waiting times into histogram bins with numeric x-axis."""
    return _aggregate_value_histogram(df, "WaitingTimeHours", color_by, filter_positive=False)


def _aggregate_job_duration_hist(df: pd.DataFrame, color_by: Optional[str] = None) -> dict[str, Any]:
    """Aggregate job durations into histogram bins with numeric x-axis."""
    return _aggregate_value_histogram(df, "ElapsedHours", color_by, filter_positive=True)


def _aggregate_period_distribution(
    df: pd.DataFrame,
    period_type: str,
    color_by: Optional[str],
    agg_func,
    metric_name: str,
    allowed_pie_dimensions: Optional[list[str]] = None
) -> dict[str, Any]:
    """
    Generic function to create distribution histograms for period-based metrics.

    Args:
        df: Input DataFrame
        period_type: Time period (day, week, month, year)
        color_by: Optional dimension to group by (Account, Partition, User, QOS, State)
        agg_func: Function to aggregate per period (e.g., lambda df, col: df.groupby(col).size())
        metric_name: Name of the metric (for error messages)
        allowed_pie_dimensions: Ignored (kept for API compatibility)

    Returns:
        WITHOUT color_by: Histogram {"type": "histogram", "x": bin_centers, "y": counts, "average": float, "median": float}
        WITH color_by: Bar chart {"x": categories, "y": values}
        On error: {"type": "empty"}
    """
    if df.empty:
        return {"type": "empty", "x": [], "y": []}

    # If color_by is specified, group by that dimension instead of creating histogram
    if color_by and color_by in df.columns:
        # Group by the color_by dimension and aggregate across all periods
        grouped = agg_func(df, color_by)

        if grouped.empty:
            return {"type": "empty", "x": [], "y": []}

        # Sort by value (descending) and return as simple bar chart
        grouped_sorted = grouped.sort_values(ascending=False)

        return {
            "x": [str(x) for x in grouped_sorted.index.tolist()],
            "y": grouped_sorted.values.tolist(),
        }

    # Determine time column based on period_type
    time_column_map = {
        "day": "SubmitDay",
        "week": "SubmitYearWeek",
        "month": "SubmitYearMonth",
        "year": "SubmitYear",
    }
    time_column = time_column_map.get(period_type, "SubmitYearMonth")

    if time_column not in df.columns:
        return {"type": "empty", "x": [], "y": []}

    # Create histogram: distribution of metric per period
    values_per_period = agg_func(df, time_column)

    if values_per_period.empty:
        return {"type": "empty", "x": [], "y": []}

    # Create histogram bins for the values
    values = values_per_period.values

    # Use adaptive binning based on data distribution
    num_bins = min(20, max(5, len(values)))

    # Create histogram
    counts, bin_edges = np.histogram(values, bins=num_bins)

    # Use bin centers for plotting (matching CPU/GPU distribution style)
    bin_centers = [(bin_edges[i] + bin_edges[i+1]) / 2 for i in range(len(bin_edges)-1)]

    # Calculate statistics
    avg_value = float(values.mean())
    median_value = float(np.median(values))

    return {
        "type": "histogram",
        "x": bin_centers,
        "y": counts.tolist(),
        "average": avg_value,
        "median": median_value,
    }


def _aggregate_active_users_distribution(df: pd.DataFrame, period_type: str = "month", color_by: Optional[str] = None) -> dict[str, Any]:
    """
    Aggregate active users distribution (matching original Dash implementation).

    WITHOUT color_by: Histogram showing distribution of active users per time period (20 bins, average line)
    WITH color_by="Account": Pie chart showing unique users per account
    WITH other color_by: Returns warning message
    """
    if "User" not in df.columns:
        return {"type": "empty", "x": [], "y": []}

    # Aggregation function: count unique users per period or dimension
    def agg_unique_users(data, group_col):
        return data.groupby(group_col)["User"].nunique()

    return _aggregate_period_distribution(
        df=df,
        period_type=period_type,
        color_by=color_by,
        agg_func=agg_unique_users,
        metric_name="Active users",
        allowed_pie_dimensions=["Account"]
    )


def _aggregate_jobs_distribution(df: pd.DataFrame, period_type: str = "month", color_by: Optional[str] = None) -> dict[str, Any]:
    """
    Aggregate jobs distribution (matching original Dash implementation).

    WITHOUT color_by: Histogram showing distribution of job counts per period (20 bins, average line)
    WITH color_by: Pie chart showing jobs by dimension (Account, Partition, State, QOS, User)
    """
    # Aggregation function: count jobs per period or dimension
    def agg_job_count(data, group_col):
        return data.groupby(group_col).size()

    return _aggregate_period_distribution(
        df=df,
        period_type=period_type,
        color_by=color_by,
        agg_func=agg_job_count,
        metric_name="Jobs",
        allowed_pie_dimensions=None  # All dimensions allowed for jobs
    )


def _aggregate_job_duration_stacked(df: pd.DataFrame, period_type: str = "month") -> dict[str, Any]:
    """
    Aggregate job duration distribution as stacked percentage bar chart over time.

    Original Dash implementation (callbacks.py:1275-1413):
    - Stacked bar chart showing percentage distribution by time period
    - 7 duration bins: < 1h, 1h-4h, 4h-12h, 12h-24h, 1d-3d, 3d-7d, > 7d
    - Y-axis: Percentage (0-100%)
    - Green color gradient (7 specific colors)
    """
    if "ElapsedHours" not in df.columns:
        return {"x": [], "series": []}

    # Determine time column
    time_column_map = {
        "day": "SubmitDay",
        "week": "SubmitYearWeek",
        "month": "SubmitYearMonth",
        "year": "SubmitYear",
    }
    time_column = time_column_map.get(period_type, "SubmitYearMonth")

    if time_column not in df.columns:
        return {"x": [], "series": []}

    # Define 7 duration bins with thresholds in hours
    bins = [
        ("< 1h", 0, 1),
        ("1h-4h", 1, 4),
        ("4h-12h", 4, 12),
        ("12h-24h", 12, 24),
        ("1d-3d", 24, 72),
        ("3d-7d", 72, 168),
        ("> 7d", 168, float('inf')),
    ]

    # Green color gradient (matching original)
    colors = [
        "#d4edda",  # Very light green
        "#c3e6cb",
        "#a3d5a1",
        "#7bc77e",
        "#52b058",
        "#3d9142",
        "#28a745",  # Dark green
    ]

    # Categorize jobs into duration bins
    df_copy = df.copy()
    df_copy["DurationBin"] = pd.cut(
        df_copy["ElapsedHours"],
        bins=[b[1] for b in bins] + [float('inf')],
        labels=[b[0] for b in bins],
        right=False,
        include_lowest=True
    )

    # Count jobs per time period and duration bin
    grouped = df_copy.groupby([time_column, "DurationBin"]).size().unstack(fill_value=0)

    if grouped.empty:
        return {"x": [], "series": []}

    # Convert counts to percentages
    grouped_pct = grouped.div(grouped.sum(axis=1), axis=0) * 100

    # Build time series for each bin
    time_periods = grouped_pct.index.tolist()
    series = []

    for i, (bin_label, _, _) in enumerate(bins):
        if bin_label in grouped_pct.columns:
            series.append({
                "name": bin_label,
                "data": grouped_pct[bin_label].tolist(),
                "color": colors[i],
            })

    # Reverse series so long duration jobs (> 7d) appear at bottom
    series.reverse()

    return {
        "x": time_periods,
        "series": series,
    }


def _aggregate_waiting_times_stacked(df: pd.DataFrame, period_type: str = "month") -> dict[str, Any]:
    """
    Aggregate waiting time distribution as stacked percentage bar chart over time.

    Original Dash implementation (callbacks.py:1416-1552):
    - Stacked bar chart showing percentage distribution by time period
    - 6 duration bins: < 30min, 30min-1h, 1h-4h, 4h-12h, 12h-24h, > 24h
    - Y-axis: Percentage (0-100%)
    - Red/orange gradient (6 specific colors)
    """
    if "WaitingTimeHours" not in df.columns:
        return {"x": [], "series": []}

    # Determine time column
    time_column_map = {
        "day": "SubmitDay",
        "week": "SubmitYearWeek",
        "month": "SubmitYearMonth",
        "year": "SubmitYear",
    }
    time_column = time_column_map.get(period_type, "SubmitYearMonth")

    if time_column not in df.columns:
        return {"x": [], "series": []}

    # Define 6 waiting time bins with thresholds in hours
    bins = [
        ("< 30min", 0, 0.5),
        ("30min-1h", 0.5, 1),
        ("1h-4h", 1, 4),
        ("4h-12h", 4, 12),
        ("12h-24h", 12, 24),
        ("> 24h", 24, float('inf')),
    ]

    # Red/orange color gradient (matching original)
    colors = [
        "#ffe5e5",  # Very light red
        "#ffb3b3",
        "#ff8080",
        "#ff4d4d",
        "#ff1a1a",
        "#cc0000",  # Dark red
    ]

    # Categorize jobs into waiting time bins
    df_copy = df[df["WaitingTimeHours"].notna()].copy()
    if df_copy.empty:
        return {"x": [], "series": []}

    df_copy["WaitingBin"] = pd.cut(
        df_copy["WaitingTimeHours"],
        bins=[b[1] for b in bins] + [float('inf')],
        labels=[b[0] for b in bins],
        right=False,
        include_lowest=True
    )

    # Count jobs per time period and waiting bin
    grouped = df_copy.groupby([time_column, "WaitingBin"]).size().unstack(fill_value=0)

    if grouped.empty:
        return {"x": [], "series": []}

    # Convert counts to percentages
    grouped_pct = grouped.div(grouped.sum(axis=1), axis=0) * 100

    # Build time series for each bin
    time_periods = grouped_pct.index.tolist()
    series = []

    for i, (bin_label, _, _) in enumerate(bins):
        if bin_label in grouped_pct.columns:
            series.append({
                "name": bin_label,
                "data": grouped_pct[bin_label].tolist(),
                "color": colors[i],
            })

    return {
        "x": time_periods,
        "series": series,
    }


def _aggregate_waiting_times_over_time(df: pd.DataFrame, period_type: str = "month", color_by: str | None = None) -> dict[str, list]:
    """Aggregate average waiting times by time period, optionally grouped by a dimension.

    Args:
        df: Input DataFrame
        period_type: Time period (day, week, month, year)
        color_by: Optional dimension to group by (Account, Partition, State, QOS, User)

    Returns:
        Without color_by: {"x": [...], "y": [...]}
        With color_by: {"x": [...], "series": [{"name": "group", "data": [...]}, ...]}
    """
    if "WaitingTimeHours" not in df.columns:
        return {"x": [], "y": []}

    # Select time column based on period type
    time_column_map = {
        "day": "SubmitDay",
        "week": "SubmitYearWeek",
        "month": "SubmitYearMonth",
        "year": "SubmitYear",
    }
    time_column = time_column_map.get(period_type, "SubmitYearMonth")

    # Handle year extraction if needed
    df_copy = df
    if time_column not in df.columns:
        if period_type == "year" and "SubmitYearMonth" in df.columns:
            df_copy = df.copy()
            df_copy["SubmitYear"] = df_copy["SubmitYearMonth"].astype(str).str[:4]
        else:
            return {"x": [], "y": []}

    # Filter out null waiting times
    df_filtered = df_copy[df_copy["WaitingTimeHours"].notna()].copy()
    if df_filtered.empty:
        return {"x": [], "y": []}

    # If no color_by, return simple time series (backward compatible)
    if not color_by or color_by not in df_filtered.columns:
        grouped = df_filtered.groupby(time_column)["WaitingTimeHours"].mean().sort_index()
        return {
            "x": grouped.index.tolist(),
            "y": grouped.values.tolist(),
        }

    # With color_by, return multi-series data for stacked chart
    # Group by time AND dimension
    grouped = df_filtered.groupby([time_column, color_by])["WaitingTimeHours"].mean().reset_index()

    # Get top 10 groups by average waiting time
    top_groups = grouped.groupby(color_by)["WaitingTimeHours"].mean().nlargest(10).index.tolist()
    grouped_filtered = grouped[grouped[color_by].isin(top_groups)]

    # Get all time periods (sorted)
    all_periods = sorted(df_filtered[time_column].unique())

    # Build series for each group
    series = []
    for group in top_groups:
        group_data = grouped_filtered[grouped_filtered[color_by] == group]
        # Create a complete series with 0 for missing periods
        data = []
        for period in all_periods:
            period_value = group_data[group_data[time_column] == period]["WaitingTimeHours"].mean()
            data.append(float(period_value) if pd.notna(period_value) else 0.0)

        series.append({
            "name": str(group),
            "data": data,
        })

    return {
        "x": all_periods,
        "series": series,
    }


def _aggregate_job_duration_over_time(df: pd.DataFrame, period_type: str = "month", color_by: str | None = None) -> dict[str, list]:
    """Aggregate average job duration by time period, optionally grouped by a dimension.

    Args:
        df: Input DataFrame
        period_type: Time period (day, week, month, year)
        color_by: Optional dimension to group by (Account, Partition, State, QOS, User)

    Returns:
        Without color_by: {"x": [...], "y": [...]}
        With color_by: {"x": [...], "series": [{"name": "group", "data": [...]}, ...]}
    """
    if "ElapsedHours" not in df.columns:
        return {"x": [], "y": []}

    # Select time column based on period type
    time_column_map = {
        "day": "SubmitDay",
        "week": "SubmitYearWeek",
        "month": "SubmitYearMonth",
        "year": "SubmitYear",
    }
    time_column = time_column_map.get(period_type, "SubmitYearMonth")

    # Handle year extraction if needed
    df_copy = df
    if time_column not in df.columns:
        if period_type == "year" and "SubmitYearMonth" in df.columns:
            df_copy = df.copy()
            df_copy["SubmitYear"] = df_copy["SubmitYearMonth"].astype(str).str[:4]
        else:
            return {"x": [], "y": []}

    # Filter out null or zero durations
    df_filtered = df_copy[(df_copy["ElapsedHours"].notna()) & (df_copy["ElapsedHours"] > 0)].copy()
    if df_filtered.empty:
        return {"x": [], "y": []}

    # If no color_by, return simple time series (backward compatible)
    if not color_by or color_by not in df_filtered.columns:
        grouped = df_filtered.groupby(time_column)["ElapsedHours"].mean().sort_index()
        return {
            "x": grouped.index.tolist(),
            "y": grouped.values.tolist(),
        }

    # With color_by, return multi-series data for stacked chart
    # Group by time AND dimension
    grouped = df_filtered.groupby([time_column, color_by])["ElapsedHours"].mean().reset_index()

    # Get top 10 groups by average duration
    top_groups = grouped.groupby(color_by)["ElapsedHours"].mean().nlargest(10).index.tolist()
    grouped_filtered = grouped[grouped[color_by].isin(top_groups)]

    # Get all time periods (sorted)
    all_periods = sorted(df_filtered[time_column].unique())

    # Build series for each group
    series = []
    for group in top_groups:
        group_data = grouped_filtered[grouped_filtered[color_by] == group]
        # Create a complete series with 0 for missing periods
        data = []
        for period in all_periods:
            period_value = group_data[group_data[time_column] == period]["ElapsedHours"].mean()
            data.append(float(period_value) if pd.notna(period_value) else 0.0)

        series.append({
            "name": str(group),
            "data": data,
        })

    return {
        "x": all_periods,
        "series": series,
    }


def _aggregate_waiting_times_trends(df: pd.DataFrame, period_type: str = "month", color_by: Optional[str] = None, stat: str = "median") -> dict[str, Any]:
    """Aggregate waiting time statistics (mean, median, max, percentiles) by time period.

    Args:
        df: Input DataFrame
        period_type: Time period (day, week, month, year)
        color_by: Optional grouping dimension for multi-line mode
        stat: Statistic to use when color_by is specified (default: median)

    Returns:
        Dictionary with multiple statistical series for trend visualization
    """
    if "WaitingTimeHours" not in df.columns:
        return {"x": [], "stats": {}}

    # Select time column based on period type
    time_column_map = {
        "day": "SubmitDay",
        "week": "SubmitYearWeek",
        "month": "SubmitYearMonth",
        "year": "SubmitYear",
    }
    time_column = time_column_map.get(period_type, "SubmitYearMonth")

    # Handle year extraction if needed
    df_copy = df
    if time_column not in df.columns:
        if period_type == "year" and "SubmitYearMonth" in df.columns:
            df_copy = df.copy()
            df_copy["SubmitYear"] = df_copy["SubmitYearMonth"].astype(str).str[:4]
        else:
            return {"x": [], "stats": {}}

    # Filter out null waiting times
    df_filtered = df_copy[df_copy["WaitingTimeHours"].notna()].copy()
    if df_filtered.empty:
        return {"x": [], "stats": {}}

    # Get all time periods (sorted)
    all_periods = sorted(df_filtered[time_column].unique())

    # Multi-line mode when color_by is specified
    if color_by and color_by != "None" and color_by in df_filtered.columns:
        groups = sorted(df_filtered[color_by].dropna().unique())
        series = []

        for group in groups:
            group_df = df_filtered[df_filtered[color_by] == group]
            values = []

            for period in all_periods:
                period_data = group_df[group_df[time_column] == period]["WaitingTimeHours"]

                if not period_data.empty:
                    # Calculate the selected statistic
                    if stat == "mean":
                        values.append(float(period_data.mean()))
                    elif stat == "median":
                        values.append(float(period_data.median()))
                    elif stat == "max":
                        values.append(float(period_data.max()))
                    elif stat.startswith("p"):
                        # Handle percentiles (p25, p50, p75, p90, p95, p99)
                        percentile = int(stat[1:]) / 100.0
                        values.append(float(period_data.quantile(percentile)))
                    else:
                        values.append(float(period_data.median()))
                else:
                    values.append(0.0)

            series.append({
                "name": str(group),
                "data": values,
            })

        return {
            "x": all_periods,
            "series": series,
        }

    # Single line mode - calculate all statistics
    stats = {
        "mean": [],
        "median": [],
        "max": [],
        "p25": [],  # 25th percentile
        "p50": [],  # 50th percentile (same as median)
        "p75": [],  # 75th percentile
        "p90": [],  # 90th percentile
        "p95": [],  # 95th percentile
        "p99": [],  # 99th percentile
    }

    for period in all_periods:
        period_data = df_filtered[df_filtered[time_column] == period]["WaitingTimeHours"]

        if not period_data.empty:
            stats["mean"].append(float(period_data.mean()))
            stats["median"].append(float(period_data.median()))
            stats["max"].append(float(period_data.max()))
            stats["p25"].append(float(period_data.quantile(0.25)))
            stats["p50"].append(float(period_data.quantile(0.50)))
            stats["p75"].append(float(period_data.quantile(0.75)))
            stats["p90"].append(float(period_data.quantile(0.90)))
            stats["p95"].append(float(period_data.quantile(0.95)))
            stats["p99"].append(float(period_data.quantile(0.99)))
        else:
            # Fill with 0 for missing periods
            for key in stats:
                stats[key].append(0.0)

    return {
        "x": all_periods,
        "stats": stats,
    }


def _aggregate_job_duration_trends(df: pd.DataFrame, period_type: str = "month", color_by: Optional[str] = None, stat: str = "median") -> dict[str, Any]:
    """Aggregate job duration statistics (mean, median, max, percentiles) by time period.

    Args:
        df: Input DataFrame
        period_type: Time period (day, week, month, year)
        color_by: Optional grouping dimension for multi-line mode
        stat: Statistic to use when color_by is specified (default: median)

    Returns:
        Dictionary with multiple statistical series for trend visualization
    """
    if "ElapsedHours" not in df.columns:
        return {"x": [], "stats": {}}

    # Select time column based on period type
    time_column_map = {
        "day": "SubmitDay",
        "week": "SubmitYearWeek",
        "month": "SubmitYearMonth",
        "year": "SubmitYear",
    }
    time_column = time_column_map.get(period_type, "SubmitYearMonth")

    # Handle year extraction if needed
    df_copy = df
    if time_column not in df.columns:
        if period_type == "year" and "SubmitYearMonth" in df.columns:
            df_copy = df.copy()
            df_copy["SubmitYear"] = df_copy["SubmitYearMonth"].astype(str).str[:4]
        else:
            return {"x": [], "stats": {}}

    # Filter out null or zero durations
    df_filtered = df_copy[(df_copy["ElapsedHours"].notna()) & (df_copy["ElapsedHours"] > 0)].copy()
    if df_filtered.empty:
        return {"x": [], "stats": {}}

    # Get all time periods (sorted)
    all_periods = sorted(df_filtered[time_column].unique())

    # Multi-line mode when color_by is specified
    if color_by and color_by != "None" and color_by in df_filtered.columns:
        groups = sorted(df_filtered[color_by].dropna().unique())
        series = []

        for group in groups:
            group_df = df_filtered[df_filtered[color_by] == group]
            values = []

            for period in all_periods:
                period_data = group_df[group_df[time_column] == period]["ElapsedHours"]

                if not period_data.empty:
                    # Calculate the selected statistic
                    if stat == "mean":
                        values.append(float(period_data.mean()))
                    elif stat == "median":
                        values.append(float(period_data.median()))
                    elif stat == "max":
                        values.append(float(period_data.max()))
                    elif stat.startswith("p"):
                        # Handle percentiles (p25, p50, p75, p90, p95, p99)
                        percentile = int(stat[1:]) / 100.0
                        values.append(float(period_data.quantile(percentile)))
                    else:
                        values.append(float(period_data.median()))
                else:
                    values.append(0.0)

            series.append({
                "name": str(group),
                "data": values,
            })

        return {
            "x": all_periods,
            "series": series,
        }

    # Single line mode - calculate all statistics
    stats = {
        "mean": [],
        "median": [],
        "max": [],
        "p25": [],  # 25th percentile
        "p50": [],  # 50th percentile (same as median)
        "p75": [],  # 75th percentile
        "p90": [],  # 90th percentile
        "p95": [],  # 95th percentile
        "p99": [],  # 99th percentile
    }

    for period in all_periods:
        period_data = df_filtered[df_filtered[time_column] == period]["ElapsedHours"]

        if not period_data.empty:
            stats["mean"].append(float(period_data.mean()))
            stats["median"].append(float(period_data.median()))
            stats["max"].append(float(period_data.max()))
            stats["p25"].append(float(period_data.quantile(0.25)))
            stats["p50"].append(float(period_data.quantile(0.50)))
            stats["p75"].append(float(period_data.quantile(0.75)))
            stats["p90"].append(float(period_data.quantile(0.90)))
            stats["p95"].append(float(period_data.quantile(0.95)))
            stats["p99"].append(float(period_data.quantile(0.99)))
        else:
            # Fill with 0 for missing periods
            for key in stats:
                stats[key].append(0.0)

    return {
        "x": all_periods,
        "stats": stats,
    }


def _aggregate_cpus_per_job(df: pd.DataFrame) -> dict[str, list]:
    """Aggregate CPUs per job distribution."""
    if "AllocCPUS" not in df.columns:
        return {"x": [], "y": []}

    counts = df["AllocCPUS"].value_counts().sort_index().head(20)
    return {
        "x": counts.index.tolist(),
        "y": counts.values.tolist(),
    }


def _aggregate_gpus_per_job(df: pd.DataFrame) -> dict[str, list]:
    """Aggregate GPUs per job distribution (only jobs with GPUs, limited to 20 bins)."""
    if "AllocGPUS" not in df.columns:
        return {"x": [], "y": []}

    gpu_jobs = df[df["AllocGPUS"] > 0]
    if gpu_jobs.empty:
        return {"x": [], "y": []}

    counts = gpu_jobs["AllocGPUS"].value_counts().sort_index().head(20)
    return {
        "x": counts.index.tolist(),
        "y": counts.values.tolist(),
    }


def _aggregate_nodes_per_job(df: pd.DataFrame) -> dict[str, list]:
    """Aggregate nodes per job distribution."""
    if "Nodes" not in df.columns:
        return {"x": [], "y": []}

    node_jobs = df[df["Nodes"] > 0]
    if node_jobs.empty:
        return {"x": [], "y": []}

    counts = node_jobs["Nodes"].value_counts().sort_index().head(20)
    return {
        "x": counts.index.tolist(),
        "y": counts.values.tolist(),
    }


def _aggregate_cpu_hours_by_account(df: pd.DataFrame) -> dict[str, list]:
    """Aggregate CPU hours by account (top 10)."""
    if "Account" not in df.columns or "CPUHours" not in df.columns:
        return {"x": [], "y": []}

    totals = df.groupby("Account")["CPUHours"].sum().sort_values(ascending=False).head(10)
    return {
        "x": totals.index.tolist(),
        "y": totals.values.tolist(),
    }


def _aggregate_gpu_hours_by_account(df: pd.DataFrame) -> dict[str, list]:
    """Aggregate GPU hours by account (top 10)."""
    if "Account" not in df.columns or "GPUHours" not in df.columns:
        return {"x": [], "y": []}

    gpu_df = df[df["GPUHours"] > 0]
    if gpu_df.empty:
        return {"x": [], "y": []}

    totals = gpu_df.groupby("Account")["GPUHours"].sum().sort_values(ascending=False).head(10)
    return {
        "x": totals.index.tolist(),
        "y": totals.values.tolist(),
    }


def _aggregate_node_usage(
    df: pd.DataFrame,
    color_by: str | None = None,
    hide_unused: bool = True,
    sort_by_usage: bool = False,
) -> dict[str, Any]:
    """Aggregate CPU and GPU usage by node.

    Args:
        df: Input DataFrame
        color_by: Optional dimension to group by (Account, Partition, State, QOS, User)
        hide_unused: Hide nodes with 0 usage
        sort_by_usage: Sort nodes by usage (default: alphabetical)

    Returns:
        Dictionary with cpu_usage and gpu_usage data
    """
    if "NodeList" not in df.columns:
        return {
            "cpu_usage": {"x": [], "y": [], "series": []},
            "gpu_usage": {"x": [], "y": [], "series": []},
        }

    # Explode NodeList to get one row per node
    cols = ["NodeList", "CPUHours", "GPUHours"]
    if color_by and color_by in df.columns:
        cols.append(color_by)

    node_df = df[cols].copy()

    # NodeList can be:
    # 1. A numpy array like array(['node1', 'node2'])
    # 2. A list like ['node1', 'node2']
    # 3. A comma-separated string like "node1,node2"
    # We need to handle all cases and convert to a list for explode()
    def process_nodelist(val):
        import numpy as np

        # If it's a numpy array, convert to list
        if isinstance(val, np.ndarray):
            return val.tolist()
        # If it's already a list or tuple, use as is
        elif isinstance(val, (list, tuple)):
            return list(val)
        # Otherwise it's a string, split on commas
        else:
            return str(val).split(",")

    node_df["NodeList"] = node_df["NodeList"].apply(process_nodelist)
    node_df = node_df.explode("NodeList")
    node_df = node_df[node_df["NodeList"].notna()]
    node_df["NodeList"] = node_df["NodeList"].astype(str).str.strip()

    if node_df.empty:
        return {
            "cpu_usage": {"x": [], "y": [], "series": []},
            "gpu_usage": {"x": [], "y": [], "series": []},
        }

    # Group by node (and optionally color_by dimension)
    if color_by and color_by in node_df.columns:
        groupby_cols = ["NodeList", color_by]
        cpu_grouped = node_df.groupby(groupby_cols)["CPUHours"].sum().reset_index()
        gpu_grouped = node_df.groupby(groupby_cols)["GPUHours"].sum().reset_index()
    else:
        cpu_grouped = node_df.groupby("NodeList")["CPUHours"].sum().reset_index()
        gpu_grouped = node_df.groupby("NodeList")["GPUHours"].sum().reset_index()

    # Hide unused nodes if requested
    if hide_unused:
        cpu_grouped = cpu_grouped[cpu_grouped["CPUHours"] > 0]
        gpu_grouped = gpu_grouped[gpu_grouped["GPUHours"] > 0]

    # Sort nodes
    if sort_by_usage:
        if color_by and color_by in cpu_grouped.columns:
            cpu_total_per_node = cpu_grouped.groupby("NodeList")["CPUHours"].sum().sort_values(ascending=False)
            gpu_total_per_node = gpu_grouped.groupby("NodeList")["GPUHours"].sum().sort_values(ascending=False)
        else:
            cpu_total_per_node = cpu_grouped.set_index("NodeList")["CPUHours"].sort_values(ascending=False)
            gpu_total_per_node = gpu_grouped.set_index("NodeList")["GPUHours"].sort_values(ascending=False)
        cpu_sorted_nodes = cpu_total_per_node.index.tolist()
        gpu_sorted_nodes = gpu_total_per_node.index.tolist()
    else:
        # Alphabetical sort (natural sort would be better but requires natsort library)
        cpu_sorted_nodes = sorted(cpu_grouped["NodeList"].unique())
        gpu_sorted_nodes = sorted(gpu_grouped["NodeList"].unique())

    # Build response
    if color_by and color_by in cpu_grouped.columns:
        # Multi-series for stacked bar chart
        cpu_series = []
        top_groups = cpu_grouped.groupby(color_by)["CPUHours"].sum().nlargest(10).index.tolist()
        for group in top_groups:
            group_data = cpu_grouped[cpu_grouped[color_by] == group]
            data = []
            for node in cpu_sorted_nodes:
                node_value = group_data[group_data["NodeList"] == node]["CPUHours"].sum()
                data.append(float(node_value) if node_value > 0 else 0.0)
            cpu_series.append({
                "name": str(group),
                "data": data,
            })

        gpu_series = []
        top_groups = gpu_grouped.groupby(color_by)["GPUHours"].sum().nlargest(10).index.tolist()
        for group in top_groups:
            group_data = gpu_grouped[gpu_grouped[color_by] == group]
            data = []
            for node in gpu_sorted_nodes:
                node_value = group_data[group_data["NodeList"] == node]["GPUHours"].sum()
                data.append(float(node_value) if node_value > 0 else 0.0)
            gpu_series.append({
                "name": str(group),
                "data": data,
            })

        return {
            "cpu_usage": {
                "x": cpu_sorted_nodes,
                "series": cpu_series,
            },
            "gpu_usage": {
                "x": gpu_sorted_nodes,
                "series": gpu_series,
            },
        }
    else:
        # Single series
        cpu_data = []
        for node in cpu_sorted_nodes:
            value = cpu_grouped[cpu_grouped["NodeList"] == node]["CPUHours"].sum()
            cpu_data.append(float(value))

        gpu_data = []
        for node in gpu_sorted_nodes:
            value = gpu_grouped[gpu_grouped["NodeList"] == node]["GPUHours"].sum()
            gpu_data.append(float(value))

        return {
            "cpu_usage": {
                "x": cpu_sorted_nodes,
                "y": cpu_data,
            },
            "gpu_usage": {
                "x": gpu_sorted_nodes,
                "y": gpu_data,
            },
        }
