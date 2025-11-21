"""Timeline chart generators for CPU, GPU, jobs, and users over time."""
import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


def generate_cpu_usage_over_time(df: pd.DataFrame, period_type: str = "month", color_by: str | None = None) -> dict[str, list]:
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

    # Handle year extraction and week normalization
    df_copy = df.copy()

    if time_column not in df.columns:
        logger.warning(f"Time column '{time_column}' not found in DataFrame. Available columns: {df.columns.tolist()}")
        if period_type == "year" and "StartYearMonth" in df.columns:
            df_copy["StartYear"] = df_copy["StartYearMonth"].astype(str).str[:4]
        else:
            return {"x": [], "y": []}

    # CRITICAL FIX: Normalize week timestamps to Monday 00:00:00
    # The parquet files have exact job start times in StartYearWeek instead of week-start Mondays
    if period_type == "week" and time_column in df_copy.columns:
        # Convert to pandas datetime if not already
        df_copy[time_column] = pd.to_datetime(df_copy[time_column])
        # Normalize to start of week (Monday)
        df_copy[time_column] = df_copy[time_column].dt.to_period('W-MON').dt.start_time

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

    # Get all groups sorted by total CPU hours
    all_groups = grouped.groupby(color_by)["CPUHours"].sum().sort_values(ascending=False).index.tolist()
    grouped_filtered = grouped[grouped[color_by].isin(all_groups)]

    # Get all time periods (sorted)
    all_periods = sorted(df_copy[time_column].unique())

    # Build series for each group
    series = []
    for group in all_groups:
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


def generate_gpu_usage_over_time(df: pd.DataFrame, period_type: str = "month", color_by: str | None = None) -> dict[str, list]:
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

    # Handle year extraction and week normalization
    df_copy = df.copy()

    if time_column not in df.columns:
        logger.warning(f"Time column '{time_column}' not found in DataFrame. Available columns: {df.columns.tolist()}")
        if period_type == "year" and "StartYearMonth" in df.columns:
            df_copy["StartYear"] = df_copy["StartYearMonth"].astype(str).str[:4]
        else:
            return {"x": [], "y": []}

    # CRITICAL FIX: Normalize week timestamps to Monday 00:00:00
    # The parquet files have exact job start times in StartYearWeek instead of week-start Mondays
    if period_type == "week" and time_column in df_copy.columns:
        # Convert to pandas datetime if not already
        df_copy[time_column] = pd.to_datetime(df_copy[time_column])
        # Normalize to start of week (Monday)
        df_copy[time_column] = df_copy[time_column].dt.to_period('W-MON').dt.start_time

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

    # Get all groups sorted by total GPU hours
    all_groups = grouped.groupby(color_by)["GPUHours"].sum().sort_values(ascending=False).index.tolist()
    grouped_filtered = grouped[grouped[color_by].isin(all_groups)]

    # Get all time periods (sorted)
    all_periods = sorted(df_copy[time_column].unique())

    # Build series for each group
    series = []
    for group in all_groups:
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


def generate_active_users_over_time(df: pd.DataFrame, period_type: str = "month", color_by: str | None = None) -> dict[str, list]:
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
    # CRITICAL: Use Start time, not Submit time (matching CPU/GPU implementation)
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
        grouped = df_copy.groupby(time_column)["User"].nunique().sort_index()
        return {
            "x": grouped.index.tolist(),
            "y": grouped.values.tolist(),
        }

    # With color_by, return multi-series data for stacked chart
    # Group by time AND dimension, count unique users
    grouped = df_copy.groupby([time_column, color_by])["User"].nunique().reset_index(name="num_active_users")

    # Get all groups sorted by total unique users across all time
    # Note: This counts unique users PER group, not sum of unique counts
    all_groups = []
    for group in df_copy[color_by].unique():
        group_users = df_copy[df_copy[color_by] == group]["User"].nunique()
        all_groups.append((group, group_users))
    all_groups = sorted(all_groups, key=lambda x: x[1], reverse=True)
    all_groups = [g[0] for g in all_groups]

    grouped_filtered = grouped[grouped[color_by].isin(all_groups)]

    # Get all time periods (sorted)
    all_periods = sorted(df_copy[time_column].unique())

    # Build series for each group
    series = []
    for group in all_groups:
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


def generate_jobs_over_time(df: pd.DataFrame, period_type: str = "month", color_by: str | None = None) -> dict[str, list]:
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
        grouped = df_copy[time_column].value_counts().sort_index()
        return {
            "x": grouped.index.tolist(),
            "y": grouped.values.tolist(),
        }

    # With color_by, return multi-series data for stacked chart
    # Group by time AND dimension, count jobs
    grouped = df_copy.groupby([time_column, color_by]).size().reset_index(name="num_jobs")

    # Get all groups sorted by total job count
    all_groups = grouped.groupby(color_by)["num_jobs"].sum().sort_values(ascending=False).index.tolist()
    grouped_filtered = grouped[grouped[color_by].isin(all_groups)]

    # Get all time periods (sorted)
    all_periods = sorted(df_copy[time_column].unique())

    # Build series for each group
    series = []
    for group in all_groups:
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


def generate_waiting_times_over_time(df: pd.DataFrame, period_type: str = "month", color_by: str | None = None) -> dict[str, list]:
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

    # Get all groups sorted by average waiting time
    all_groups = grouped.groupby(color_by)["WaitingTimeHours"].mean().sort_values(ascending=False).index.tolist()
    grouped_filtered = grouped[grouped[color_by].isin(all_groups)]

    # Get all time periods (sorted)
    all_periods = sorted(df_filtered[time_column].unique())

    # Build series for each group
    series = []
    for group in all_groups:
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


def generate_job_duration_over_time(df: pd.DataFrame, period_type: str = "month", color_by: str | None = None) -> dict[str, list]:
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

    # Get all groups sorted by average duration
    all_groups = grouped.groupby(color_by)["ElapsedHours"].mean().sort_values(ascending=False).index.tolist()
    grouped_filtered = grouped[grouped[color_by].isin(all_groups)]

    # Get all time periods (sorted)
    all_periods = sorted(df_filtered[time_column].unique())

    # Build series for each group
    series = []
    for group in all_groups:
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
