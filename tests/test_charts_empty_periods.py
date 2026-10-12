"""The chart endpoint returns every period of the selected range, not only the periods with jobs."""

import pandas as pd
import pytest
from backend.app.api import charts as charts_api
from backend.app.core.saml_auth import get_current_user_saml
from fastapi import FastAPI
from fastapi.testclient import TestClient


def jobs_on(days: list[str]) -> pd.DataFrame:
    start = pd.to_datetime(pd.Series(days))
    n = len(days)
    return pd.DataFrame(
        {
            "JobID": [str(i) for i in range(n)],
            "User": ["u"] * n,
            "Account": ["acc"] * n,
            "Partition": ["cpu"] * n,
            "State": ["COMPLETED"] * n,
            "QOS": ["normal"] * n,
            "CPUHours": [2.0] * n,
            "GPUHours": [0.0] * n,
            "ElapsedHours": [1.0] * n,
            "WaitingTimeHours": [0.5] * n,
            "Submit": start - pd.Timedelta(hours=1),
            "Start": start,
            "End": start + pd.Timedelta(hours=1),
            "StartDay": start.dt.normalize(),
            "StartYearWeek": start.dt.to_period("W").dt.start_time.dt.strftime("%Y-%m-%d"),
            "StartYearMonth": start.dt.to_period("M").astype(str),
            "StartYear": start.dt.year,
            "SubmitDay": (start - pd.Timedelta(hours=1)).dt.normalize(),
        }
    )


class FakeDatastore:
    def __init__(self, frame: pd.DataFrame):
        self.frame = frame

    def filter(self, **_kwargs) -> pd.DataFrame:
        return self.frame


class NoNodes:
    def get_all_node_capacities(self, _hostname):
        return {}


@pytest.fixture
def client(monkeypatch):
    frame = jobs_on(["2026-09-20 10:00", "2026-09-23 10:00"])
    monkeypatch.setattr(charts_api, "get_datastore", lambda: FakeDatastore(frame))
    monkeypatch.setattr(charts_api, "get_cluster_config", NoNodes)
    monkeypatch.setattr(charts_api, "_chart_cache", {})
    app = FastAPI()
    app.include_router(charts_api.router, prefix="/api")
    app.dependency_overrides[get_current_user_saml] = lambda: {"username": "tester"}
    return TestClient(app)


def charts(client) -> dict:
    response = client.post(
        "/api/charts",
        json={"hostname": "test", "start_date": "2026-09-19", "end_date": "2026-09-24", "period_type": "day"},
    )
    assert response.status_code == 200, response.text
    return response.json()


DAYS = [f"2026-09-{d}T00:00:00" for d in ("19", "20", "21", "22", "23", "24")]


def test_counts_show_zero_on_days_without_jobs(client):
    data = charts(client)
    assert data["jobs_over_time"] == {"x": DAYS, "y": [0, 1, 0, 0, 1, 0]}
    assert data["cpu_usage_over_time"]["y"] == [0.0, 2.0, 0.0, 0.0, 2.0, 0.0]
    assert data["active_users_over_time"]["y"] == [0, 1, 0, 0, 1, 0]


def test_averages_leave_a_gap_on_days_without_jobs(client):
    data = charts(client)
    assert data["waiting_times_trends"]["x"] == DAYS
    assert data["waiting_times_trends"]["stats"]["mean"] == [None, 0.5, None, None, 0.5, None]
    assert data["waiting_times_over_time"]["y"] == [None, 0.5, None, None, 0.5, None]


def test_stacked_shares_are_zero_on_days_without_jobs(client):
    data = charts(client)
    stacked = data["job_duration_stacked"]
    assert stacked["x"] == DAYS
    assert all(len(series["data"]) == len(DAYS) for series in stacked["series"])
    assert sum(series["data"][0] for series in stacked["series"]) == 0
    assert sum(series["data"][1] for series in stacked["series"]) == pytest.approx(100.0)


def test_unknown_period_type_is_rejected_with_422(client):
    response = client.post("/api/charts", json={"hostname": "test", "period_type": "fortnight"})
    assert response.status_code == 422
