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

  // Active Users Over Time
  const activeUsersData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const usersByMonth: Record<string, Set<string>> = {};
    data.data.forEach((job) => {
      if (job.SubmitYearMonth && job.User) {
        if (!usersByMonth[job.SubmitYearMonth]) {
          usersByMonth[job.SubmitYearMonth] = new Set();
        }
        usersByMonth[job.SubmitYearMonth].add(job.User);
      }
    });

    const sortedMonths = Object.keys(usersByMonth).sort();
    const userCounts = sortedMonths.map((month) => usersByMonth[month].size);

    return {
      x: sortedMonths,
      y: userCounts,
    };
  }, [data]);

  // Number of Jobs Over Time
  const jobsOverTimeData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const groupedByMonth: Record<string, number> = {};
    data.data.forEach((job) => {
      if (job.SubmitYearMonth) {
        groupedByMonth[job.SubmitYearMonth] = (groupedByMonth[job.SubmitYearMonth] || 0) + 1;
      }
    });

    const sortedMonths = Object.keys(groupedByMonth).sort();
    const jobCounts = sortedMonths.map((month) => groupedByMonth[month]);

    return {
      x: sortedMonths,
      y: jobCounts,
    };
  }, [data]);

  // Jobs by Partition
  const jobsByPartitionData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const groupedByPartition: Record<string, number> = {};
    data.data.forEach((job) => {
      if (job.Partition) {
        groupedByPartition[job.Partition] = (groupedByPartition[job.Partition] || 0) + 1;
      }
    });

    const sortedPartitions = Object.entries(groupedByPartition)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10);

    return {
      x: sortedPartitions.map(([partition]) => partition),
      y: sortedPartitions.map(([, count]) => count),
    };
  }, [data]);

  // Waiting Times Histogram
  const waitingTimesHistData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const waitingTimes = data.data
      .filter((job) => job['WaitingTime [h]'] !== undefined && job['WaitingTime [h]'] !== null)
      .map((job) => job['WaitingTime [h]']);

    if (waitingTimes.length === 0) return null;

    return waitingTimes;
  }, [data]);

  // Job Duration Histogram
  const jobDurationHistData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const durations = data.data
      .filter((job) => job['Elapsed [h]'] !== undefined && job['Elapsed [h]'] !== null && job['Elapsed [h]'] > 0)
      .map((job) => job['Elapsed [h]']);

    if (durations.length === 0) return null;

    return durations;
  }, [data]);

  // CPUs per Job Distribution
  const cpusPerJobData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const cpuCounts: Record<number, number> = {};
    data.data.forEach((job) => {
      const cpus = job.CPUs || 0;
      cpuCounts[cpus] = (cpuCounts[cpus] || 0) + 1;
    });

    const sortedCPUs = Object.entries(cpuCounts)
      .sort(([a], [b]) => Number(a) - Number(b))
      .slice(0, 20); // Top 20 CPU counts

    return {
      x: sortedCPUs.map(([cpu]) => cpu),
      y: sortedCPUs.map(([, count]) => count),
    };
  }, [data]);

  // GPUs per Job Distribution
  const gpusPerJobData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const gpuCounts: Record<number, number> = {};
    data.data.forEach((job) => {
      const gpus = job.GPUs || 0;
      gpuCounts[gpus] = (gpuCounts[gpus] || 0) + 1;
    });

    const sortedGPUs = Object.entries(gpuCounts)
      .sort(([a], [b]) => Number(a) - Number(b))
      .filter(([gpu]) => Number(gpu) > 0); // Only show jobs with GPUs

    if (sortedGPUs.length === 0) return null;

    return {
      x: sortedGPUs.map(([gpu]) => gpu),
      y: sortedGPUs.map(([, count]) => count),
    };
  }, [data]);

  // Nodes per Job Distribution
  const nodesPerJobData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const nodeCounts: Record<number, number> = {};
    data.data.forEach((job) => {
      const nodes = job.Nodes || 0;
      if (nodes > 0) {
        nodeCounts[nodes] = (nodeCounts[nodes] || 0) + 1;
      }
    });

    if (Object.keys(nodeCounts).length === 0) return null;

    const sortedNodes = Object.entries(nodeCounts)
      .sort(([a], [b]) => Number(a) - Number(b))
      .slice(0, 20); // Top 20 node counts

    return {
      x: sortedNodes.map(([nodes]) => nodes),
      y: sortedNodes.map(([, count]) => count),
    };
  }, [data]);

  // CPU Hours by Account (Top 10)
  const cpuHoursByAccountData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const accountCPU: Record<string, number> = {};
    data.data.forEach((job) => {
      if (job.Account && job.CPUHours) {
        accountCPU[job.Account] = (accountCPU[job.Account] || 0) + job.CPUHours;
      }
    });

    const sortedAccounts = Object.entries(accountCPU)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10);

    if (sortedAccounts.length === 0) return null;

    return {
      x: sortedAccounts.map(([account]) => account),
      y: sortedAccounts.map(([, hours]) => hours),
    };
  }, [data]);

  // GPU Hours by Account (Top 10)
  const gpuHoursByAccountData = useMemo(() => {
    if (!data || !data.data.length) return null;

    const accountGPU: Record<string, number> = {};
    data.data.forEach((job) => {
      if (job.Account && job.GPUHours && job.GPUHours > 0) {
        accountGPU[job.Account] = (accountGPU[job.Account] || 0) + job.GPUHours;
      }
    });

    const sortedAccounts = Object.entries(accountGPU)
      .sort(([, a], [, b]) => b - a)
      .slice(0, 10);

    if (sortedAccounts.length === 0) return null;

    return {
      x: sortedAccounts.map(([account]) => account),
      y: sortedAccounts.map(([, hours]) => hours),
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
    <div className="charts-grid">
      {/* CPU Usage Chart */}
      {cpuUsageData && cpuUsageData.x.length > 0 && (
        <div className="card chart-full-width">
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
        <div className="card chart-full-width">
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

      {/* Active Users Over Time */}
      {activeUsersData && activeUsersData.x.length > 0 && (
        <div className="card chart-full-width">
          <h3>Active Users Over Time</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: activeUsersData.x,
                  y: activeUsersData.y,
                  type: 'scatter',
                  mode: 'lines+markers',
                  fill: 'tozeroy',
                  line: { color: '#28a745', width: 2 },
                  marker: { color: '#28a745', size: 8 },
                  name: 'Active Users',
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 50 },
                xaxis: { title: 'Month' },
                yaxis: { title: 'Number of Users' },
                hovermode: 'closest',
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}

      {/* Number of Jobs Over Time */}
      {jobsOverTimeData && jobsOverTimeData.x.length > 0 && (
        <div className="card chart-full-width">
          <h3>Number of Jobs Over Time</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: jobsOverTimeData.x,
                  y: jobsOverTimeData.y,
                  type: 'scatter',
                  mode: 'lines+markers',
                  fill: 'tozeroy',
                  line: { color: '#6f42c1', width: 2 },
                  marker: { color: '#6f42c1', size: 8 },
                  name: 'Jobs',
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 50 },
                xaxis: { title: 'Month' },
                yaxis: { title: 'Number of Jobs' },
                hovermode: 'closest',
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}

      {/* Jobs by Partition */}
      {jobsByPartitionData && jobsByPartitionData.x.length > 0 && (
        <div className="card">
          <h3>Top 10 Partitions by Number of Jobs</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: jobsByPartitionData.x,
                  y: jobsByPartitionData.y,
                  type: 'bar',
                  marker: { color: '#EC7300' },
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 100 },
                xaxis: { title: 'Partition', tickangle: -45 },
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

      {/* Waiting Times Histogram */}
      {waitingTimesHistData && waitingTimesHistData.length > 0 && (
        <div className="card">
          <h3>Job Waiting Times Distribution</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: waitingTimesHistData,
                  type: 'histogram',
                  marker: { color: '#04A5D5' },
                  name: 'Waiting Time',
                  nbinsx: 50,
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 50 },
                xaxis: { title: 'Waiting Time (hours)' },
                yaxis: { title: 'Number of Jobs' },
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}

      {/* Job Duration Histogram */}
      {jobDurationHistData && jobDurationHistData.length > 0 && (
        <div className="card">
          <h3>Job Duration Distribution</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: jobDurationHistData,
                  type: 'histogram',
                  marker: { color: '#EC7300' },
                  name: 'Duration',
                  nbinsx: 50,
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 50 },
                xaxis: { title: 'Job Duration (hours)' },
                yaxis: { title: 'Number of Jobs' },
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}

      {/* CPUs per Job Distribution */}
      {cpusPerJobData && cpusPerJobData.x.length > 0 && (
        <div className="card">
          <h3>CPUs per Job Distribution</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: cpusPerJobData.x,
                  y: cpusPerJobData.y,
                  type: 'bar',
                  marker: { color: '#28a745' },
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 50 },
                xaxis: { title: 'Number of CPUs' },
                yaxis: { title: 'Number of Jobs' },
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}

      {/* GPUs per Job Distribution */}
      {gpusPerJobData && gpusPerJobData.x.length > 0 && (
        <div className="card">
          <h3>GPUs per Job Distribution</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: gpusPerJobData.x,
                  y: gpusPerJobData.y,
                  type: 'bar',
                  marker: { color: '#6f42c1' },
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 50 },
                xaxis: { title: 'Number of GPUs' },
                yaxis: { title: 'Number of Jobs' },
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}

      {/* Nodes per Job Distribution */}
      {nodesPerJobData && nodesPerJobData.x.length > 0 && (
        <div className="card">
          <h3>Nodes per Job Distribution</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: nodesPerJobData.x,
                  y: nodesPerJobData.y,
                  type: 'bar',
                  marker: { color: '#17a2b8' },
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 50 },
                xaxis: { title: 'Number of Nodes' },
                yaxis: { title: 'Number of Jobs' },
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}

      {/* CPU Hours by Account */}
      {cpuHoursByAccountData && cpuHoursByAccountData.x.length > 0 && (
        <div className="card">
          <h3>Top 10 Accounts by CPU Hours</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: cpuHoursByAccountData.x,
                  y: cpuHoursByAccountData.y,
                  type: 'bar',
                  marker: { color: '#04A5D5' },
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 100 },
                xaxis: { title: 'Account', tickangle: -45 },
                yaxis: { title: 'CPU Hours' },
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}

      {/* GPU Hours by Account */}
      {gpuHoursByAccountData && gpuHoursByAccountData.x.length > 0 && (
        <div className="card">
          <h3>Top 10 Accounts by GPU Hours</h3>
          <div className="chart-container">
            <Plot
              data={[
                {
                  x: gpuHoursByAccountData.x,
                  y: gpuHoursByAccountData.y,
                  type: 'bar',
                  marker: { color: '#EC7300' },
                },
              ]}
              layout={{
                autosize: true,
                margin: { l: 50, r: 20, t: 20, b: 100 },
                xaxis: { title: 'Account', tickangle: -45 },
                yaxis: { title: 'GPU Hours' },
              }}
              useResizeHandler={true}
              style={{ width: '100%', height: '400px' }}
              config={{ responsive: true }}
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default Charts;
