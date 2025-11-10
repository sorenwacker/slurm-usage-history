import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.app.services.charts.distribution_generators import (
    generate_jobs_by_state,
    generate_jobs_by_partition,
    generate_jobs_by_account,
    generate_waiting_times_hist,
    generate_job_duration_hist,
    generate_waiting_times_stacked,
    generate_job_duration_stacked,
    generate_waiting_times_trends,
    generate_job_duration_trends,
    generate_nodes_per_job,
    generate_cpus_per_job,
    generate_gpus_per_job,
    generate_cpu_hours_by_account,
    generate_gpu_hours_by_account,
)
from backend.app.services.charts.timeline_generators import (
    generate_cpu_usage_over_time,
    generate_gpu_usage_over_time,
    generate_active_users_over_time,
    generate_jobs_over_time,
    generate_waiting_times_over_time,
    generate_job_duration_over_time,
)


@pytest.fixture
def sample_dataframe():
    """Create a sample dataframe for testing plot generation."""
    np.random.seed(42)
    n_rows = 1000

    start_dates = pd.date_range(
        start=datetime.now() - timedelta(days=30),
        end=datetime.now(),
        periods=n_rows
    )

    df = pd.DataFrame({
        'JobID': range(1, n_rows + 1),
        'State': np.random.choice(['COMPLETED', 'FAILED', 'CANCELLED', 'TIMEOUT'], n_rows),
        'Partition': np.random.choice(['gpu', 'cpu', 'interactive'], n_rows, p=[0.3, 0.6, 0.1]),
        'Account': np.random.choice(['account1', 'account2', 'account3'], n_rows),
        'User': np.random.choice(['user1', 'user2', 'user3', 'user4'], n_rows),
        'QOS': np.random.choice(['normal', 'high', 'low'], n_rows),
        'CPUHours': np.random.exponential(10, n_rows),
        'GPUHours': np.random.exponential(5, n_rows),
        'ElapsedHours': np.random.exponential(3, n_rows),
        'WaitingTime': np.random.exponential(1, n_rows),
        'AllocNodes': np.random.choice([1, 2, 3, 4], n_rows, p=[0.7, 0.2, 0.08, 0.02]),
        'AllocCPUS': np.random.choice([1, 2, 4, 8, 16], n_rows),
        'AllocGPUS': np.random.choice([0, 1, 2, 4], n_rows, p=[0.6, 0.3, 0.08, 0.02]),
        'Start': start_dates,
        'Submit': start_dates - pd.to_timedelta(np.random.exponential(1, n_rows), unit='h'),
        'End': start_dates + pd.to_timedelta(np.random.exponential(3, n_rows), unit='h'),
        'StartYearMonth': start_dates.to_period('M').astype(str),
        'StartDay': start_dates.date.astype(str),
    })

    return df


def validate_chart_output(result, min_points=1):
    """Validate that chart output has correct structure."""
    assert result is not None, "Chart result should not be None"
    assert isinstance(result, dict), "Chart result should be a dictionary"
    assert 'x' in result, "Chart result should have 'x' key"
    assert 'y' in result, "Chart result should have 'y' key"
    assert isinstance(result['x'], list), "x values should be a list"
    assert isinstance(result['y'], list), "y values should be a list"
    assert len(result['x']) >= min_points, f"Chart should have at least {min_points} data point(s)"
    assert len(result['x']) == len(result['y']), "x and y should have same length"
    return True


class TestDistributionPlots:
    """Test all distribution plot generation functions."""

    def test_generate_jobs_by_state(self, sample_dataframe):
        result = generate_jobs_by_state(sample_dataframe)
        assert validate_chart_output(result)
        assert all(isinstance(x, str) for x in result['x']), "State labels should be strings"
        assert all(isinstance(y, (int, float)) for y in result['y']), "Values should be numeric"

    def test_generate_jobs_by_partition(self, sample_dataframe):
        result = generate_jobs_by_partition(sample_dataframe)
        assert validate_chart_output(result)
        assert all(isinstance(x, str) for x in result['x']), "Partition labels should be strings"

    def test_generate_jobs_by_account(self, sample_dataframe):
        result = generate_jobs_by_account(sample_dataframe)
        assert validate_chart_output(result)
        assert all(isinstance(x, str) for x in result['x']), "Account labels should be strings"

    def test_generate_waiting_times_hist(self, sample_dataframe):
        result = generate_waiting_times_hist(sample_dataframe)
        assert validate_chart_output(result, min_points=1)

    def test_generate_job_duration_hist(self, sample_dataframe):
        result = generate_job_duration_hist(sample_dataframe)
        assert validate_chart_output(result, min_points=1)

    def test_generate_nodes_per_job(self, sample_dataframe):
        result = generate_nodes_per_job(sample_dataframe)
        assert validate_chart_output(result)
        assert all(isinstance(x, (int, str)) for x in result['x']), "Node counts should be numeric or string"

    def test_generate_cpus_per_job(self, sample_dataframe):
        result = generate_cpus_per_job(sample_dataframe)
        assert validate_chart_output(result)

    def test_generate_gpus_per_job(self, sample_dataframe):
        result = generate_gpus_per_job(sample_dataframe)
        assert validate_chart_output(result)

    def test_generate_cpu_hours_by_account(self, sample_dataframe):
        result = generate_cpu_hours_by_account(sample_dataframe)
        assert validate_chart_output(result)
        assert all(isinstance(x, str) for x in result['x']), "Account labels should be strings"

    def test_generate_gpu_hours_by_account(self, sample_dataframe):
        result = generate_gpu_hours_by_account(sample_dataframe)
        assert validate_chart_output(result)

    @pytest.mark.parametrize("period_type", ["day", "week", "month"])
    def test_generate_waiting_times_stacked(self, sample_dataframe, period_type):
        result = generate_waiting_times_stacked(sample_dataframe, period_type)
        assert validate_chart_output(result, min_points=1)

    @pytest.mark.parametrize("period_type", ["day", "week", "month"])
    def test_generate_job_duration_stacked(self, sample_dataframe, period_type):
        result = generate_job_duration_stacked(sample_dataframe, period_type)
        assert validate_chart_output(result, min_points=1)

    @pytest.mark.parametrize("period_type", ["day", "week", "month"])
    def test_generate_waiting_times_trends(self, sample_dataframe, period_type):
        result = generate_waiting_times_trends(sample_dataframe, period_type)
        assert validate_chart_output(result, min_points=1)

    @pytest.mark.parametrize("period_type", ["day", "week", "month"])
    def test_generate_job_duration_trends(self, sample_dataframe, period_type):
        result = generate_job_duration_trends(sample_dataframe, period_type)
        assert validate_chart_output(result, min_points=1)


class TestTimelinePlots:
    """Test all timeline plot generation functions."""

    @pytest.mark.parametrize("period_type", ["day", "week", "month"])
    def test_generate_cpu_usage_over_time(self, sample_dataframe, period_type):
        result = generate_cpu_usage_over_time(sample_dataframe, period_type)
        assert validate_chart_output(result)
        assert all(isinstance(y, (int, float)) for y in result['y']), "Values should be numeric"

    @pytest.mark.parametrize("period_type", ["day", "week", "month"])
    def test_generate_gpu_usage_over_time(self, sample_dataframe, period_type):
        result = generate_gpu_usage_over_time(sample_dataframe, period_type)
        assert validate_chart_output(result)
        assert all(isinstance(y, (int, float)) for y in result['y']), "Values should be numeric"

    @pytest.mark.parametrize("period_type", ["day", "week", "month"])
    def test_generate_active_users_over_time(self, sample_dataframe, period_type):
        result = generate_active_users_over_time(sample_dataframe, period_type)
        assert validate_chart_output(result)
        assert all(isinstance(y, (int, float)) for y in result['y']), "Values should be numeric"

    @pytest.mark.parametrize("period_type", ["day", "week", "month"])
    def test_generate_jobs_over_time(self, sample_dataframe, period_type):
        result = generate_jobs_over_time(sample_dataframe, period_type)
        assert validate_chart_output(result)
        assert all(isinstance(y, (int, float)) for y in result['y']), "Values should be numeric"

    @pytest.mark.parametrize("period_type", ["day", "week", "month"])
    def test_generate_waiting_times_over_time(self, sample_dataframe, period_type):
        result = generate_waiting_times_over_time(sample_dataframe, period_type)
        assert validate_chart_output(result)
        assert all(isinstance(y, (int, float)) for y in result['y']), "Values should be numeric"

    @pytest.mark.parametrize("period_type", ["day", "week", "month"])
    def test_generate_job_duration_over_time(self, sample_dataframe, period_type):
        result = generate_job_duration_over_time(sample_dataframe, period_type)
        assert validate_chart_output(result)
        assert all(isinstance(y, (int, float)) for y in result['y']), "Values should be numeric"


class TestEmptyDataFrame:
    """Test plot generation with empty dataframes."""

    def test_empty_dataframe_jobs_by_state(self):
        empty_df = pd.DataFrame(columns=['State'])
        result = generate_jobs_by_state(empty_df)
        assert result is not None

    def test_empty_dataframe_cpu_usage_over_time(self):
        empty_df = pd.DataFrame(columns=['Start', 'CPUHours'])
        result = generate_cpu_usage_over_time(empty_df, 'day')
        assert result is not None


class TestDataQuality:
    """Test plot generation handles data quality issues."""

    def test_null_values_in_waiting_times(self, sample_dataframe):
        df = sample_dataframe.copy()
        df.loc[:10, 'WaitingTime'] = np.nan
        result = generate_waiting_times_hist(df)
        assert validate_chart_output(result, min_points=1)

    def test_null_values_in_nodes(self, sample_dataframe):
        df = sample_dataframe.copy()
        df.loc[:10, 'AllocNodes'] = np.nan
        result = generate_nodes_per_job(df)
        assert validate_chart_output(result, min_points=1)

    def test_negative_cpu_hours(self, sample_dataframe):
        df = sample_dataframe.copy()
        df.loc[:10, 'CPUHours'] = -1
        result = generate_cpu_hours_by_account(df)
        assert validate_chart_output(result, min_points=1)
