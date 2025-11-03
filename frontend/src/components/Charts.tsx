import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import type { FilterResponse } from '../types';

interface ChartsProps {
  data: FilterResponse | undefined;
}

const Charts: React.FC<ChartsProps> = ({ data }) => {
  // CPU Usage Over Time
  const cpuUsageData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const groupedByMonth: Record<string, number> = {};
    data.data.forEach((job) => {
      if (job.SubmitYearMonth && job.CPUHours) {
        groupedByMonth[job.SubmitYearMonth] = (groupedByMonth[job.SubmitYearMonth] || 0) + job.CPUHours;
      }
    });

    const sortedMonths = Object.keys(groupedByMonth).sort();
    const cpuHours = sortedMonths.map((month) => groupedByMonth[month]);

    return {
      x: sortedMonths,
      y: cpuHours,
    };
  }, [data]);

  // GPU Usage Over Time
  const gpuUsageData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const groupedByMonth: Record<string, number> = {};
    data.data.forEach((job) => {
      if (job.SubmitYearMonth && job.GPUHours) {
        groupedByMonth[job.SubmitYearMonth] = (groupedByMonth[job.SubmitYearMonth] || 0) + job.GPUHours;
      }
    });

    const sortedMonths = Object.keys(groupedByMonth).sort();
    const gpuHours = sortedMonths.map((month) => groupedByMonth[month]);

    return {
      x: sortedMonths,
      y: gpuHours,
    };
  }, [data]);

  // Jobs by Account
  const jobsByAccountData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const groupedByAccount: Record<string, number> = {};
    data.data.forEach((job) => {
      if (job.Account) {
        groupedByAccount[job.Account] = (groupedByAccount[job.Account] || 0) + 1;
      }
    });

    const sortedAccounts = Object.entries(groupedByAccount)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10);

    return {
      x: sortedAccounts.map(([account]) => account),
      y: sortedAccounts.map(([, count]) => count),
    };
  }, [data]);

  // Jobs by State
  const jobsByStateData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const groupedByState: Record<string, number> = {};
    data.data.forEach((job) => {
      if (job.State) {
        groupedByState[job.State] = (groupedByState[job.State] || 0) + 1;
      }
    });

    return {
      labels: Object.keys(groupedByState),
      values: Object.values(groupedByState),
    };
  }, [data]);

  if (!data || !data.data.length) {
    return (
      <div className="card">
        <p style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
          No data available. Select a cluster and date range to view charts.
        </p>
      </div>
    );
  }

  return (
    <>
      {/* CPU Usage Chart */}
      {cpuUsageData && cpuUsageData.x.length > 0 && (
        <div className="card">
          <h3>CPU Usage Over Time</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: cpuUsageData.x,
                  y: cpuUsageData.y,
                  type: 'scatter',
                  mode: 'lines+markers',
                  fill: 'tozeroy',
                  line: { color: '#04A5D5', width: 2 },
                  marker: { color: '#04A5D5', size: 8 },
                  name: 'CPU Hours',
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 50 },
                xaxis: { title: 'Month' },
                yaxis: { title: 'CPU Hours' },
                hovermode: 'closest',
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}

      {/* GPU Usage Chart */}
      {gpuUsageData && gpuUsageData.x.length > 0 && (
        <div className="card">
          <h3>GPU Usage Over Time</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: gpuUsageData.x,
                  y: gpuUsageData.y,
                  type: 'scatter',
                  mode: 'lines+markers',
                  fill: 'tozeroy',
                  line: { color: '#EC7300', width: 2 },
                  marker: { color: '#EC7300', size: 8 },
                  name: 'GPU Hours',
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 50 },
                xaxis: { title: 'Month' },
                yaxis: { title: 'GPU Hours' },
                hovermode: 'closest',
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}

      {/* Jobs by Account */}
      {jobsByAccountData && jobsByAccountData.x.length > 0 && (
        <div className="card">
          <h3>Top 10 Accounts by Number of Jobs</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: jobsByAccountData.x,
                  y: jobsByAccountData.y,
                  type: 'bar',
                  marker: { color: '#04A5D5' },
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 100 },
                xaxis: { title: 'Account', tickangle: -45 },
                yaxis: { title: 'Number of Jobs' },
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}

      {/* Jobs by State */}
      {jobsByStateData && jobsByStateData.labels.length > 0 && (
        <div className="card">
          <h3>Jobs by State</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  labels: jobsByStateData.labels,
                  values: jobsByStateData.values,
                  type: 'pie',
                  marker: {
                    colors: ['#04A5D5', '#EC7300', '#333333', '#28a745', '#dc3545'],
                  },
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 20, r: 20, t: 20, b: 20 },
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}
    </>
  );
};

export default Charts;
