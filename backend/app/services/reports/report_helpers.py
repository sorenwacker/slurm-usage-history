"""Helper functions for date calculations and statistics."""

from typing import Any

import pandas as pd


def get_month_date_range(year: int, month: int) -> tuple[str, str]:
    """Get the start and end date for a given month."""
    start_date = f"{year}-{month:02d}-01"

    # Calculate last day of month
    if month == 12:
        end_year = year + 1
        end_month = 1
    else:
        end_year = year
        end_month = month + 1

    # Use first day of next month and subtract 1 day
    next_month_start = pd.Timestamp(f"{end_year}-{end_month:02d}-01")
    end_date = (next_month_start - pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    return start_date, end_date


def get_year_date_range(year: int) -> tuple[str, str]:
    """Get the start and end date for a given year."""
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    return start_date, end_date


def get_quarter_date_range(year: int, quarter: int) -> tuple[str, str]:
    """Get the start and end date for a given quarter (Q1-Q4)."""
    if not 1 <= quarter <= 4:
        raise ValueError(f"Quarter must be between 1 and 4, got {quarter}")

    # Define quarter start months
    quarter_start_months = {1: 1, 2: 4, 3: 7, 4: 10}
    start_month = quarter_start_months[quarter]

    # Calculate end month
    if quarter == 4:
        end_month = 12
        end_year = year
    else:
        end_month = start_month + 2
        end_year = year

    start_date = f"{year}-{start_month:02d}-01"

    # Calculate last day of the quarter's final month
    if end_month == 12:
        next_month_start = pd.Timestamp(f"{end_year + 1}-01-01")
    else:
        next_month_start = pd.Timestamp(f"{end_year}-{end_month + 1:02d}-01")

    end_date = (next_month_start - pd.Timedelta(days=1)).strftime("%Y-%m-%d")

    return start_date, end_date


def calculate_duration_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Calculate job duration statistics in hours."""
    if df.empty or "JobDuration" not in df.columns:
        return {
            "mean": 0.0,
            "median": 0.0,
            "p25": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    durations = df["JobDuration"].dropna()
    if len(durations) == 0:
        return {
            "mean": 0.0,
            "median": 0.0,
            "p25": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    return {
        "mean": float(durations.mean()),
        "median": float(durations.median()),
        "p25": float(durations.quantile(0.25)),
        "p75": float(durations.quantile(0.75)),
        "p90": float(durations.quantile(0.90)),
        "min": float(durations.min()),
        "max": float(durations.max()),
    }


def calculate_waiting_time_stats(df: pd.DataFrame) -> dict[str, Any]:
    """Calculate waiting time statistics in hours."""
    if df.empty or "WaitingTime" not in df.columns:
        return {
            "mean": 0.0,
            "median": 0.0,
            "p25": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    waiting_times = df["WaitingTime"].dropna()
    if len(waiting_times) == 0:
        return {
            "mean": 0.0,
            "median": 0.0,
            "p25": 0.0,
            "p75": 0.0,
            "p90": 0.0,
            "min": 0.0,
            "max": 0.0,
        }

    return {
        "mean": float(waiting_times.mean()),
        "median": float(waiting_times.median()),
        "p25": float(waiting_times.quantile(0.25)),
        "p75": float(waiting_times.quantile(0.75)),
        "p90": float(waiting_times.quantile(0.90)),
        "min": float(waiting_times.min()),
        "max": float(waiting_times.max()),
    }
