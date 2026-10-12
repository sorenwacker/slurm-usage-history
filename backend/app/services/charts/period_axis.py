"""Complete period axis for time-series charts.

The generators derive their x-axis from the periods present in the data, so a period
in which no job started is missing and the plotted line jumps to the next period with
data. The chart endpoint builds the complete axis of the selected range with
``period_axis`` and reindexes every time-series chart onto it with ``fill_missing_periods``.
"""

from typing import Any

import pandas as pd

_FREQ = {"day": "D", "week": "W", "month": "M", "year": "Y"}


def period_axis(period_type: str, start: pd.Timestamp, end_exclusive: pd.Timestamp) -> list[Any]:
    """Every period of ``[start, end_exclusive)`` labelled like the stored period columns.

    Days are normalized timestamps (``StartDay``), weeks the Monday date as ``YYYY-MM-DD``
    (``StartYearWeek``), months ``YYYY-MM`` (``StartYearMonth``) and years integers
    (``StartYear``).

    Raises:
        ValueError: when ``period_type`` is not day, week, month or year.
    """
    if period_type not in _FREQ:
        msg = f"Unknown period_type {period_type!r}; expected one of {sorted(_FREQ)}"
        raise ValueError(msg)
    last = end_exclusive - pd.Timedelta(nanoseconds=1)
    if last < start:
        return []
    periods = pd.period_range(start, last, freq=_FREQ[period_type])
    if period_type == "day":
        return list(periods.start_time)
    if period_type == "week":
        return periods.start_time.strftime("%Y-%m-%d").tolist()
    if period_type == "month":
        return periods.astype(str).tolist()
    return [int(year) for year in periods.year]


def fill_missing_periods(chart: dict[str, Any], periods: list[Any], fill: float | None) -> dict[str, Any]:
    """Reindex a time-series chart onto ``periods`` plus any period the data has outside it.

    Supports the three time-series shapes: ``y`` values, ``series`` entries with ``data``,
    and ``stats`` columns. A period missing from the chart gets ``fill``. Charts without an
    ``x`` key pass through unchanged.
    """
    if "x" not in chart:
        return chart
    present = [x for x in chart["x"] if not pd.isna(x)]
    axis = sorted(set(periods) | set(present))
    position = {x: i for i, x in enumerate(chart["x"])}

    def reindex(values: list[Any]) -> list[Any]:
        return [values[position[x]] if x in position else fill for x in axis]

    filled = {**chart, "x": axis}
    if "y" in chart:
        filled["y"] = reindex(chart["y"])
    if "series" in chart:
        filled["series"] = [{**series, "data": reindex(series["data"])} for series in chart["series"]]
    if "stats" in chart:
        filled["stats"] = {name: reindex(values) for name, values in chart["stats"].items()}
    return filled
