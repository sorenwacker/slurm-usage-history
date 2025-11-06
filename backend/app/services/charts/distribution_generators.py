"""Distribution chart generators for histograms, pie charts, and stacked charts."""
from typing import Any, Optional

import numpy as np
import pandas as pd


def generate_by_dimension(df: pd.DataFrame, group_by: str | None, metric: str = "count", top_n: int = 10, period_type: str = "month") -> dict[str, list]:
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
        # For CPU/GPU hours: create per-period histogram (matching original Dash behavior)
        if metric in ["CPUHours", "GPUHours"]:
            if metric not in df.columns:
                return {"x": [], "y": [], "mean": 0, "median": 0, "type": "histogram"}

            # Get time column based on period type
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


def generate_jobs_by_account(df: pd.DataFrame) -> dict[str, list]:
    """Aggregate jobs by account (top 10)."""
    if "Account" not in df.columns:
        return {"x": [], "y": []}

    counts = df["Account"].value_counts().head(10)
    return {
        "x": counts.index.tolist(),
        "y": counts.values.tolist(),
    }


def generate_jobs_by_partition(df: pd.DataFrame) -> dict[str, list]:
    """Aggregate jobs by partition (top 10)."""
    if "Partition" not in df.columns:
        return {"x": [], "y": []}

    counts = df["Partition"].value_counts().head(10)
    return {
        "x": counts.index.tolist(),
        "y": counts.values.tolist(),
    }


def generate_jobs_by_state(df: pd.DataFrame) -> dict[str, list]:
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


def generate_waiting_times_hist(df: pd.DataFrame, color_by: Optional[str] = None) -> dict[str, Any]:
    """Aggregate waiting times into histogram bins with numeric x-axis."""
    return _aggregate_value_histogram(df, "WaitingTimeHours", color_by, filter_positive=False)


def generate_job_duration_hist(df: pd.DataFrame, color_by: Optional[str] = None) -> dict[str, Any]:
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
        "day": "StartDay",
        "week": "StartYearWeek",
        "month": "StartYearMonth",
        "year": "StartYear",
    }
    time_column = time_column_map.get(period_type, "StartYearMonth")

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


def generate_active_users_distribution(df: pd.DataFrame, period_type: str = "month", color_by: Optional[str] = None) -> dict[str, Any]:
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


def generate_jobs_distribution(df: pd.DataFrame, period_type: str = "month", color_by: Optional[str] = None) -> dict[str, Any]:
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


def generate_job_duration_stacked(df: pd.DataFrame, period_type: str = "month") -> dict[str, Any]:
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
        "day": "StartDay",
        "week": "StartYearWeek",
        "month": "StartYearMonth",
        "year": "StartYear",
    }
    time_column = time_column_map.get(period_type, "StartYearMonth")

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


def generate_waiting_times_stacked(df: pd.DataFrame, period_type: str = "month") -> dict[str, Any]:
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
        "day": "StartDay",
        "week": "StartYearWeek",
        "month": "StartYearMonth",
        "year": "StartYear",
    }
    time_column = time_column_map.get(period_type, "StartYearMonth")

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


def generate_waiting_times_trends(df: pd.DataFrame, period_type: str = "month", color_by: Optional[str] = None, stat: str = "median") -> dict[str, Any]:
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


def generate_job_duration_trends(df: pd.DataFrame, period_type: str = "month", color_by: Optional[str] = None, stat: str = "median") -> dict[str, Any]:
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


def generate_cpus_per_job(df: pd.DataFrame) -> dict[str, list]:
    """Aggregate CPUs per job distribution."""
    if "AllocCPUS" not in df.columns:
        return {"x": [], "y": []}

    counts = df["AllocCPUS"].value_counts().sort_index().head(20)
    return {
        "x": counts.index.tolist(),
        "y": counts.values.tolist(),
    }


def generate_gpus_per_job(df: pd.DataFrame) -> dict[str, list]:
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


def generate_nodes_per_job(df: pd.DataFrame) -> dict[str, list]:
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


def generate_cpu_hours_by_account(df: pd.DataFrame) -> dict[str, list]:
    """Aggregate CPU hours by account (top 10)."""
    if "Account" not in df.columns or "CPUHours" not in df.columns:
        return {"x": [], "y": []}

    totals = df.groupby("Account")["CPUHours"].sum().sort_values(ascending=False).head(10)
    return {
        "x": totals.index.tolist(),
        "y": totals.values.tolist(),
    }


def generate_gpu_hours_by_account(df: pd.DataFrame) -> dict[str, list]:
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
