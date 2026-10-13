"""A run collects every job that ended inside its window; the window length comes from the agent config."""

import json
import subprocess
from types import SimpleNamespace

import pytest

from slurm_usage_history.scripts import cluster_agent
from slurm_usage_history.scripts.exporter import SlurmDataExtractor

HEADER = "JobID|User|Submit|Start|End|State"


def sacct_output(rows: list[str]) -> str:
    return "\n".join([HEADER, *rows]) + "\n"


@pytest.fixture
def fake_sacct(monkeypatch):
    calls: list[list[str]] = []
    rows = [
        "1|alice|2026-09-01T10:00:00|2026-09-02T10:00:00|2026-09-20T10:00:00|COMPLETED",  # long job, ended in window
        "2|bob|2026-09-19T10:00:00|2026-09-19T11:00:00|2026-09-19T12:00:00|COMPLETED",  # short job in window
        "3|carol|2026-09-19T10:00:00|2026-09-19T11:00:00|2026-09-26T12:00:00|COMPLETED",  # ended after the window
        "4|dave|2026-09-21T10:00:00|2026-09-21T11:00:00|Unknown|RUNNING",  # still running
    ]

    def run(cmd, **_kwargs):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=sacct_output(rows), stderr="")

    monkeypatch.setattr(subprocess, "run", run)
    return calls


def test_jobs_are_selected_by_end_time_inside_the_window(fake_sacct):
    df = SlurmDataExtractor(cluster_name="TEST").extract_jobs("2026-09-15", "2026-09-21")
    assert sorted(df["JobID"]) == ["1", "2"]


def test_sacct_is_asked_up_to_the_end_of_the_last_day(fake_sacct):
    SlurmDataExtractor(cluster_name="TEST").extract_jobs("2026-09-15", "2026-09-21")
    (cmd,) = fake_sacct
    assert "--starttime=2026-09-15" in cmd
    assert "--endtime=2026-09-22" in cmd


def test_agent_run_uses_the_configured_collection_window(tmp_path, monkeypatch):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"api_url": "http://x", "api_key": "k", "collection_window_days": 30}))
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **_kw: calls.append(cmd) or SimpleNamespace(returncode=0))
    monkeypatch.setattr(cluster_agent, "window_start", lambda days: f"start-{days}")
    args = SimpleNamespace(
        config=str(config),
        cluster_name=None,
        start_date=None,
        end_date=None,
        dry_run=False,
        verbose=False,
        sync_config=False,
    )
    with pytest.raises(SystemExit):
        cluster_agent.run_command(args)
    (cmd,) = calls
    assert cmd[cmd.index("--start-date") + 1] == "start-30"


def test_agent_run_keeps_an_explicit_start_date(tmp_path, monkeypatch):
    config = tmp_path / "config.json"
    config.write_text(json.dumps({"api_url": "http://x", "api_key": "k", "collection_window_days": 30}))
    calls: list[list[str]] = []
    monkeypatch.setattr(subprocess, "run", lambda cmd, **_kw: calls.append(cmd) or SimpleNamespace(returncode=0))
    args = SimpleNamespace(
        config=str(config),
        cluster_name=None,
        start_date="2026-01-01",
        end_date=None,
        dry_run=False,
        verbose=False,
        sync_config=False,
    )
    with pytest.raises(SystemExit):
        cluster_agent.run_command(args)
    (cmd,) = calls
    assert cmd[cmd.index("--start-date") + 1] == "2026-01-01"
