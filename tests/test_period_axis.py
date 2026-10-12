"""The period axis of a time-series chart covers the selected range, including periods without jobs."""

import pandas as pd
import pytest
from backend.app.services.charts.period_axis import fill_missing_periods, period_axis


def derived_periods(starts: list[str]) -> pd.DataFrame:
    """Period columns exactly as the ingest endpoint derives them from ``Start``."""
    start = pd.to_datetime(pd.Series(starts))
    return pd.DataFrame(
        {
            "StartDay": start.dt.normalize(),
            "StartYearWeek": start.dt.to_period("W").dt.start_time.dt.strftime("%Y-%m-%d"),
            "StartYearMonth": start.dt.to_period("M").astype(str),
            "StartYear": start.dt.year,
        }
    )


WINDOW = (pd.Timestamp("2026-09-19"), pd.Timestamp("2026-09-24"))  # end exclusive


def test_day_axis_lists_every_day_of_the_window_in_the_stored_format():
    axis = period_axis("day", *WINDOW)
    assert axis == list(pd.to_datetime(["2026-09-19", "2026-09-20", "2026-09-21", "2026-09-22", "2026-09-23"]))
    assert axis[0] == derived_periods(["2026-09-19 13:00"])["StartDay"][0]


def test_week_axis_uses_monday_labels_like_the_stored_column():
    axis = period_axis("week", pd.Timestamp("2026-09-17"), pd.Timestamp("2026-10-01"))
    assert axis == ["2026-09-14", "2026-09-21", "2026-09-28"]
    assert axis[0] == derived_periods(["2026-09-17"])["StartYearWeek"][0]


def test_month_and_year_axes_match_the_stored_columns():
    assert period_axis("month", pd.Timestamp("2026-11-15"), pd.Timestamp("2027-02-01")) == [
        "2026-11",
        "2026-12",
        "2027-01",
    ]
    assert period_axis("year", pd.Timestamp("2025-06-01"), pd.Timestamp("2027-01-01")) == [2025, 2026]
    assert period_axis("year", *WINDOW)[0] == derived_periods(["2026-09-19"])["StartYear"][0]


def test_unknown_period_type_is_rejected():
    with pytest.raises(ValueError, match="period_type"):
        period_axis("fortnight", *WINDOW)


def test_counts_are_filled_with_zero_for_empty_periods():
    chart = {"x": ["2026-09", "2026-11"], "y": [3, 5]}
    filled = fill_missing_periods(chart, ["2026-09", "2026-10", "2026-11"], fill=0)
    assert filled == {"x": ["2026-09", "2026-10", "2026-11"], "y": [3, 0, 5]}


def test_series_and_stats_are_filled_with_the_given_value():
    chart = {
        "x": ["2026-09", "2026-11"],
        "series": [{"name": "a", "data": [1.0, 2.0], "color": "#000"}],
        "stats": {"mean": [1.5, 2.5]},
    }
    filled = fill_missing_periods(chart, ["2026-09", "2026-10", "2026-11"], fill=None)
    assert filled["series"] == [{"name": "a", "data": [1.0, None, 2.0], "color": "#000"}]
    assert filled["stats"] == {"mean": [1.5, None, 2.5]}


def test_periods_present_in_the_data_but_outside_the_axis_are_kept_in_order():
    chart = {"x": ["2026-12", "2026-09"], "y": [7, 3]}
    filled = fill_missing_periods(chart, ["2026-10", "2026-11"], fill=0)
    assert filled == {"x": ["2026-09", "2026-10", "2026-11", "2026-12"], "y": [3, 0, 0, 7]}


def test_charts_without_a_period_axis_pass_through_unchanged():
    empty = {"x": [], "y": []}
    assert fill_missing_periods(empty, ["2026-10"], fill=0) == {"x": ["2026-10"], "y": [0]}
    pie = {"labels": ["a"], "values": [1]}
    assert fill_missing_periods(pie, ["2026-10"], fill=0) == pie
