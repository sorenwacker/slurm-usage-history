import React, { useState, useMemo, useEffect, useRef } from 'react';
import Plot from 'react-plotly.js';
import type { AggregatedChartsResponse, ChartData } from '../types';
import { createGlobalColorMap, COLORS } from './charts/chartHelpers';
import StackedAreaChart from './charts/StackedAreaChart';
import PieChart from './charts/PieChart';
import HistogramChart from './charts/HistogramChart';
import TimelineChart from './charts/TimelineChart';
import GaugeChart from './charts/GaugeChart';

interface ChartsProps {
  data: AggregatedChartsResponse | undefined;
  hideUnusedNodes: boolean;
  setHideUnusedNodes: (value: boolean) => void;
  sortByUsage: boolean;
  setSortByUsage: (value: boolean) => void;
  normalizeNodeUsage: boolean;
  setNormalizeNodeUsage: (value: boolean) => void;
  colorBy: string;  // The selected "color by" dimension (or "None")
  periodType: string;  // The period type (day, week, month, year)
}

const Charts: React.FC<ChartsProps> = ({ data, hideUnusedNodes, setHideUnusedNodes, sortByUsage, setSortByUsage, normalizeNodeUsage, setNormalizeNodeUsage, colorBy, periodType }) => {
  const [waitingTimeTrendStat, setWaitingTimeTrendStat] = useState<string>('median');
  const [jobDurationTrendStat, setJobDurationTrendStat] = useState<string>('median');
  const renderStartTime = useRef<number>(Date.now());

  // Create color map synchronously during render (not in useEffect)
  // This ensures the color map is available immediately when charts need it
  // Only create a color map if a "color by" dimension is selected (not "None")
  const colorMap = React.useMemo(() => {
    // colorBy is empty string "" when "None (default)" is selected
    console.log('Charts: colorBy =', JSON.stringify(colorBy), 'type:', typeof colorBy);
    if (!data || !colorBy) {
      console.log('Charts: Returning null colorMap because colorBy is empty');
      return null;
    }

    // Collect all unique series labels from all chart data
    const allLabels: string[] = [];

    // Helper to extract series names from chart data
    const extractSeriesNames = (chartData: any) => {
      if (chartData?.series) {
        chartData.series.forEach((series: any) => allLabels.push(String(series.name)));
      }
    };

    // Extract from all chart data that has series
    // NOTE: Timing section charts (waiting times and job duration) are excluded
    // from color mapping - they should not be affected by "Color By" selection
    extractSeriesNames(data.active_users_over_time);
    extractSeriesNames(data.jobs_over_time);
    extractSeriesNames(data.cpu_usage_over_time);
    extractSeriesNames(data.gpu_usage_over_time);
    extractSeriesNames(data.cpu_hours_by_account);
    extractSeriesNames(data.gpu_hours_by_account);
    extractSeriesNames(data.node_cpu_usage);
    extractSeriesNames(data.node_gpu_usage);

    // Create and return the color map
    return allLabels.length > 0 ? createGlobalColorMap(allLabels) : null;
  }, [data, colorBy]);

  // Filter, sort, and optionally normalize node data client-side
  const processedNodeData = useMemo(() => {
    if (!data) return { cpu: null, gpu: null };

    // Helper to normalize a value to percentage of max capacity
    const normalizeValue = (value: number, maxCapacity: number): number => {
      if (maxCapacity <= 0) return 0;
      return Math.min(100, (value / maxCapacity) * 100);
    };

    const filterAndSortNodeData = (nodeData: ChartData, resourceType: 'cpu' | 'gpu'): ChartData => {
      let indices = nodeData.x.map((_, i) => i);

      // Filter: hide nodes with 0 usage (when series data, sum all series values)
      if (hideUnusedNodes) {
        indices = indices.filter(i => {
          if (nodeData.series) {
            // Sum all series values for this node
            const total = nodeData.series.reduce((sum, s) => sum + (s.data[i] || 0), 0);
            return total > 0;
          } else if (nodeData.y) {
            return (nodeData.y[i] as number) > 0;
          }
          return true;
        });
      }

      // Sort: by usage (descending) or alphabetically
      if (sortByUsage) {
        indices.sort((a, b) => {
          let valueA = 0;
          let valueB = 0;

          if (nodeData.series) {
            valueA = nodeData.series.reduce((sum, s) => sum + (s.data[a] || 0), 0);
            valueB = nodeData.series.reduce((sum, s) => sum + (s.data[b] || 0), 0);
          } else if (nodeData.y) {
            valueA = nodeData.y[a] as number;
            valueB = nodeData.y[b] as number;
          }

          return valueB - valueA; // Descending order
        });
      }

      // Apply filtering/sorting, also remap hardware_config to match filtered nodes
      const filteredNodes = indices.map(i => nodeData.x[i]);
      const filteredHardwareConfig = nodeData.hardware_config
        ? Object.fromEntries(
            filteredNodes.map(node => [node, nodeData.hardware_config![String(node)]])
              .filter(([_, config]) => config !== undefined)
          )
        : undefined;

      // Get values (apply normalization if requested)
      const totalHours = nodeData.total_hours || 0;
      const shouldNormalize = normalizeNodeUsage && filteredHardwareConfig && totalHours > 0;

      let processedY: (string | number)[] | undefined = undefined;
      if (nodeData.y) {
        processedY = indices.map(i => {
          const node = String(nodeData.x[i]);
          const rawValue = nodeData.y![i] as number;
          if (shouldNormalize && filteredHardwareConfig[node]) {
            const hw = filteredHardwareConfig[node];
            const capacity = resourceType === 'cpu' ? hw.cpu_cores : hw.gpu_count;
            const maxCapacity = capacity * totalHours;
            return normalizeValue(rawValue, maxCapacity);
          }
          return rawValue;
        });
      }

      let processedSeries = nodeData.series?.map(s => ({
        ...s,
        data: indices.map(i => {
          const node = String(nodeData.x[i]);
          const rawValue = s.data[i];
          if (shouldNormalize && filteredHardwareConfig && filteredHardwareConfig[node]) {
            const hw = filteredHardwareConfig[node];
            const capacity = resourceType === 'cpu' ? hw.cpu_cores : hw.gpu_count;
            const maxCapacity = capacity * totalHours;
            return normalizeValue(rawValue, maxCapacity);
          }
          return rawValue;
        })
      }));

      return {
        ...nodeData,
        x: filteredNodes,
        y: processedY,
        series: processedSeries,
        normalized: shouldNormalize,  // Set based on actual normalization applied
        hardware_config: filteredHardwareConfig,  // Preserve hardware config
      };
    };

    return {
      cpu: data.node_cpu_usage ? filterAndSortNodeData(data.node_cpu_usage, 'cpu') : null,
      gpu: data.node_gpu_usage ? filterAndSortNodeData(data.node_gpu_usage, 'gpu') : null
    };
  }, [data, hideUnusedNodes, sortByUsage, normalizeNodeUsage]);

  // Calculate overall cluster utilization for gauges (when normalized)
  const clusterUtilization = useMemo(() => {
    if (!processedNodeData.cpu?.normalized && !processedNodeData.gpu?.normalized) {
      return { cpu: null, gpu: null };
    }

    const calculateAverage = (nodeData: ChartData | null): number | null => {
      if (!nodeData || !nodeData.normalized) return null;

      let total = 0;
      let count = 0;

      if (nodeData.series && nodeData.series.length > 0) {
        // Sum all series values for each node, then average
        for (let i = 0; i < nodeData.x.length; i++) {
          const nodeTotal = nodeData.series.reduce((sum, s) => sum + (s.data[i] || 0), 0);
          total += nodeTotal;
          count++;
        }
      } else if (nodeData.y) {
        nodeData.y.forEach(val => {
          total += val as number;
          count++;
        });
      }

      return count > 0 ? total / count : null;
    };

    return {
      cpu: calculateAverage(processedNodeData.cpu),
      gpu: calculateAverage(processedNodeData.gpu),
    };
  }, [processedNodeData]);

  // Performance logging - measure render time after charts are rendered
  useEffect(() => {
    if (!data) return;

    const renderTime = Date.now() - renderStartTime.current;
    console.log('═══════════════════════════════════════════════════════');
    console.log('📊 CHARTS RENDER PERFORMANCE');
    console.log('═══════════════════════════════════════════════════════');
    console.log(`⏱️  Render time: ${renderTime}ms`);
    console.log(`📈 Total jobs: ${data.summary.total_jobs.toLocaleString()}`);
    console.log(`🎨 Color by: ${colorBy || 'None'}`);
    console.log(`🔍 Hide unused nodes: ${hideUnusedNodes}`);
    console.log(`📊 Sort by usage: ${sortByUsage}`);
    console.log(`🖥️  CPU nodes (filtered): ${processedNodeData.cpu?.x.length || 0}`);
    console.log(`🎮 GPU nodes (filtered): ${processedNodeData.gpu?.x.length || 0}`);
    console.log('═══════════════════════════════════════════════════════');

    // Reset timer for next render
    renderStartTime.current = Date.now();
  }, [data, colorBy, hideUnusedNodes, sortByUsage, processedNodeData]);

  if (!data) {
    return (
      <div className="card">
        <p style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
          No data available. Select a cluster and date range to view charts.
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* USERS SECTION */}
      <section className="section">
        <h2 className="section-title">Users</h2>
        <div className="chart-row">
          {data.active_users_over_time && data.active_users_over_time.x.length > 0 && (
            <div className="card">
              <h3>Active Users</h3>
              <StackedAreaChart
                data={data.active_users_over_time}
                xTitle="Period"
                yTitle="Number of Users"
                defaultColor="#28a745"
                colorMap={colorMap}
                defaultName="Active Users"
                chartType="area"
                periodType={periodType}
              />
            </div>
          )}
          {data.user_activity_frequency && (
            (data.user_activity_frequency.type === 'pie' && (data.user_activity_frequency.labels?.length ?? 0) > 0) ||
            (data.user_activity_frequency.x && data.user_activity_frequency.x.length > 0)
          ) && (
            <div className="card">
              <h3>
                {data.user_activity_frequency.type === 'pie'
                  ? (colorBy === 'User' ? 'Most Active Users' : `User Activity by ${colorBy}`)
                  : 'User Activity Frequency'}
                <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>
                  {' '}({data.user_activity_frequency.total_users} users over {data.user_activity_frequency.total_periods} {data.user_activity_frequency.period_label})
                </span>
              </h3>
              {data.user_activity_frequency.type === 'pie' ? (
                <PieChart
                  data={{
                    labels: data.user_activity_frequency.labels || [],
                    values: data.user_activity_frequency.values || [],
                  }}
                  valueLabel={colorBy === 'User'
                    ? `Active ${data.user_activity_frequency.period_label || 'periods'}`
                    : `User-${data.user_activity_frequency.period_label || 'periods'}`}
                  colors={colorMap ? (data.user_activity_frequency.labels || []).map((label, idx) =>
                    colorMap.get(label) || COLORS[idx % COLORS.length]
                  ) : undefined}
                />
              ) : (
                <HistogramChart
                  data={data.user_activity_frequency}
                  xTitle={`Active ${data.user_activity_frequency.period_label || 'periods'}`}
                  yTitle="Number of Users"
                  defaultColor="#28a745"
                  colorMap={null}
                  isHistogram={true}
                  showMedianMean={true}
                  unit={` ${data.user_activity_frequency.period_label || 'periods'}`}
                  decimalPlaces={1}
                />
              )}
            </div>
          )}
        </div>
      </section>

      {/* JOBS SECTION */}
      <section className="section">
        <h2 className="section-title">Jobs</h2>
        <div className="chart-row">
          {data.jobs_over_time && data.jobs_over_time.x.length > 0 && (
            <div className="card">
              <h3>Number of Submitted Jobs</h3>
              <StackedAreaChart
                data={data.jobs_over_time}
                xTitle="Period"
                yTitle="Number of Submitted Jobs"
                defaultColor="#6f42c1"
                colorMap={colorMap}
                defaultName="Jobs"
                chartType="area"
                periodType={periodType}
              />
            </div>
          )}
          {data.jobs_distribution && (
            (data.jobs_distribution.type === 'pie' && (data.jobs_distribution.labels?.length ?? 0) > 0) ||
            (data.jobs_distribution.x && data.jobs_distribution.x.length > 0)
          ) && (
            <div className="card">
              <h3>
                {data.jobs_distribution.type === 'pie'
                  ? `Jobs by ${colorBy}`
                  : 'Jobs Distribution'}
                <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>
                  {' '}({data.summary.total_jobs.toLocaleString()} jobs)
                </span>
              </h3>
              {data.jobs_distribution.type === 'pie' ? (
                <PieChart
                  data={{
                    labels: data.jobs_distribution.labels || [],
                    values: data.jobs_distribution.values || [],
                  }}
                  valueLabel="Jobs"
                  colors={colorMap ? (data.jobs_distribution.labels || []).map((label, idx) =>
                    colorMap.get(label) || COLORS[idx % COLORS.length]
                  ) : undefined}
                />
              ) : (
                <HistogramChart
                  data={data.jobs_distribution}
                  xTitle="Jobs per Period"
                  yTitle="Number of Periods"
                  defaultColor="#6f42c1"
                  colorMap={null}
                  isHistogram={true}
                  showMedianMean={true}
                  unit=""
                  decimalPlaces={0}
                />
              )}
            </div>
          )}
        </div>
      </section>

      {/* USAGE SECTION */}
      <section className="section">
        <h2 className="section-title">Usage</h2>
        <div className="chart-row">
          {data.cpu_usage_over_time && data.cpu_usage_over_time.x.length > 0 && (
            <div className="card">
              <h3>CPU Usage</h3>
              <StackedAreaChart
                data={data.cpu_usage_over_time}
                xTitle="Period"
                yTitle="CPU Hours"
                defaultColor="#04A5D5"
                colorMap={colorMap}
                defaultName="CPU Hours"
                chartType="area"
                periodType={periodType}
              />
            </div>
          )}
          {data.cpu_hours_by_account && (
            (data.cpu_hours_by_account.type === 'pie' && (data.cpu_hours_by_account.labels?.length ?? 0) > 0) ||
            (data.cpu_hours_by_account.x && data.cpu_hours_by_account.x.length > 0)
          ) && (
            <div className="card">
              <h3>
                {data.cpu_hours_by_account.type === 'pie'
                  ? `CPU Usage by ${colorBy}`
                  : 'CPU Usage Distribution'}
                <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>
                  {' '}({Math.round(data.summary.total_cpu_hours).toLocaleString()} hours)
                </span>
              </h3>
              {data.cpu_hours_by_account.type === 'pie' ? (
                <PieChart
                  data={{
                    labels: data.cpu_hours_by_account.labels || [],
                    values: data.cpu_hours_by_account.values || [],
                  }}
                  valueLabel="CPU Hours"
                  colors={colorMap ? (data.cpu_hours_by_account.labels || []).map((label, idx) =>
                    colorMap.get(label) || COLORS[idx % COLORS.length]
                  ) : undefined}
                />
              ) : (
                <HistogramChart
                  data={data.cpu_hours_by_account}
                  xTitle="CPU Hours per Period"
                  yTitle="Number of Periods"
                  defaultColor="#04A5D5"
                  colorMap={null}
                  isHistogram={true}
                  showMedianMean={true}
                  unit="h"
                  decimalPlaces={0}
                />
              )}
            </div>
          )}
        </div>
        <div className="chart-row">
          {data.gpu_usage_over_time && data.gpu_usage_over_time.x.length > 0 && (
            <div className="card">
              <h3>GPU Usage</h3>
              <StackedAreaChart
                data={data.gpu_usage_over_time}
                xTitle="Period"
                yTitle="GPU Hours"
                defaultColor="#EC7300"
                colorMap={colorMap}
                defaultName="GPU Hours"
                chartType="area"
                periodType={periodType}
              />
            </div>
          )}
          {data.gpu_hours_by_account && (
            (data.gpu_hours_by_account.type === 'pie' && (data.gpu_hours_by_account.labels?.length ?? 0) > 0) ||
            (data.gpu_hours_by_account.x && data.gpu_hours_by_account.x.length > 0)
          ) && (
            <div className="card">
              <h3>
                {data.gpu_hours_by_account.type === 'pie'
                  ? `GPU Usage by ${colorBy}`
                  : 'GPU Usage Distribution'}
                <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>
                  {' '}({Math.round(data.summary.total_gpu_hours).toLocaleString()} hours)
                </span>
              </h3>
              {data.gpu_hours_by_account.type === 'pie' ? (
                <PieChart
                  data={{
                    labels: data.gpu_hours_by_account.labels || [],
                    values: data.gpu_hours_by_account.values || [],
                  }}
                  valueLabel="GPU Hours"
                  colors={colorMap ? (data.gpu_hours_by_account.labels || []).map((label, idx) =>
                    colorMap.get(label) || COLORS[idx % COLORS.length]
                  ) : undefined}
                />
              ) : (
                <HistogramChart
                  data={data.gpu_hours_by_account}
                  xTitle="GPU Hours per Period"
                  yTitle="Number of Periods"
                  defaultColor="#EC7300"
                  colorMap={null}
                  isHistogram={true}
                  showMedianMean={true}
                  unit="h"
                  decimalPlaces={0}
                />
              )}
            </div>
          )}
        </div>
        {(processedNodeData.cpu?.x.length || processedNodeData.gpu?.x.length) && (
          <div className="node-usage-section">
            <div className="node-usage-header">
              <h3 className="section-title">CPU/GPU Usage by Node</h3>
              <div className="node-usage-controls">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={hideUnusedNodes}
                    onChange={(e) => setHideUnusedNodes(e.target.checked)}
                  />
                  <span>Hide unused</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={sortByUsage}
                    onChange={(e) => setSortByUsage(e.target.checked)}
                  />
                  <span>Sort by usage</span>
                </label>
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    checked={normalizeNodeUsage}
                    onChange={(e) => setNormalizeNodeUsage(e.target.checked)}
                  />
                  <span>Normalize %</span>
                </label>
              </div>
            </div>
            {/* Utilization gauges - show when normalization is enabled */}
            {(clusterUtilization.cpu !== null || clusterUtilization.gpu !== null) && (
              <div className="gauge-grid">
                {clusterUtilization.cpu !== null && (
                  <div className="card gauge-card">
                    <GaugeChart
                      value={Math.round(clusterUtilization.cpu * 10) / 10}
                      title="Average CPU Utilization"
                    />
                  </div>
                )}
                {clusterUtilization.gpu !== null && (
                  <div className="card gauge-card">
                    <GaugeChart
                      value={Math.round(clusterUtilization.gpu * 10) / 10}
                      title="Average GPU Utilization"
                    />
                  </div>
                )}
              </div>
            )}
            {processedNodeData.cpu && processedNodeData.cpu.x.length > 0 && (
              <div className="card" style={{ marginBottom: '1.5rem' }}>
                <h3>CPU Usage by Node {processedNodeData.cpu.normalized && <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(% of capacity)</span>}</h3>
                <StackedAreaChart
                  data={processedNodeData.cpu}
                  xTitle="Node"
                  yTitle={processedNodeData.cpu.normalized ? "Utilization (%)" : "CPU Hours"}
                  defaultColor="#04A5D5"
                  colorMap={colorMap}
                  chartType="bar"
                  barMode="stack"
                />
              </div>
            )}
            {processedNodeData.gpu && processedNodeData.gpu.x.length > 0 && (
              <div className="card">
                <h3>GPU Usage by Node {processedNodeData.gpu.normalized && <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(% of capacity)</span>}</h3>
                <StackedAreaChart
                  data={processedNodeData.gpu}
                  xTitle="Node"
                  yTitle={processedNodeData.gpu.normalized ? "Utilization (%)" : "GPU Hours"}
                  defaultColor="#EC7300"
                  colorMap={colorMap}
                  chartType="bar"
                  barMode="stack"
                />
              </div>
            )}
          </div>
        )}
      </section>

      {/* TIMING SECTION */}
      <section className="section">
        <h2 className="section-title">Timing</h2>

        {/* WAITING TIME CHARTS */}
        <div className="chart-row">
          {data.waiting_times_trends && data.waiting_times_trends.x.length > 0 && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3>Waiting Time Trends</h3>
                {!data.waiting_times_trends.series && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <label style={{ fontSize: '0.9rem', fontWeight: 'normal' }}>Statistic:</label>
                    <select
                      value={waitingTimeTrendStat}
                      onChange={(e) => setWaitingTimeTrendStat(e.target.value)}
                      style={{
                        padding: '0.4rem 0.6rem',
                        borderRadius: '4px',
                        border: '1px solid #ccc',
                        fontSize: '0.9rem',
                      }}
                    >
                      <option value="mean">Mean</option>
                      <option value="median">Median</option>
                      <option value="max">Max</option>
                      <option value="p75">P75</option>
                      <option value="p90">P90</option>
                      <option value="p95">P95</option>
                      <option value="p99">P99</option>
                    </select>
                  </div>
                )}
              </div>
              <TimelineChart
                data={data.waiting_times_trends}
                xTitle="Period"
                yTitle="Waiting Time (hours)"
                colorMap={colorMap}
                defaultColor="#dc3545"
                statistic={waitingTimeTrendStat}
              />
            </div>
          )}
        </div>

        <div className="chart-row">
          {data.waiting_times_stacked && data.waiting_times_stacked.x && data.waiting_times_stacked.x.length > 0 && (
            <div className="card">
              <h3>Waiting Time Distribution Over Time <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(stacked percentages)</span></h3>
              <div className="chart-container">
                <Plot
                  data={data.waiting_times_stacked.series?.map((series: any) => ({
                    x: data.waiting_times_stacked.x,
                    y: series.data,
                    name: series.name,
                    type: 'bar',
                    marker: { color: series.color },
                    hovertemplate: `<b>${series.name}</b><br>%{y:.1f}%<br>Period: %{x}<extra></extra>`,
                  })) || []}
                  layout={{
                    autosize: true,
                    margin: { l: 80, r: 20, t: 20, b: 60 },
                    xaxis: {
                      title: { text: 'Period', font: { size: 14 }, standoff: 10 },
                      showgrid: true,
                      gridcolor: 'rgba(128, 128, 128, 0.1)',
                      zeroline: false,
                    },
                    yaxis: {
                      title: { text: 'Percentage (%)', font: { size: 14 }, standoff: 10 },
                      showgrid: true,
                      gridcolor: 'rgba(128, 128, 128, 0.1)',
                      zeroline: false,
                      tickformat: ',',
                      range: [0, 100],
                    },
                    barmode: 'stack',
                    showlegend: true,
                    legend: {
                      orientation: 'h',
                      y: -0.2,
                      x: 0.5,
                      xanchor: 'center',
                      yanchor: 'top',
                      font: { size: 10 },
                    },
                    plot_bgcolor: 'rgba(0, 0, 0, 0)',
                    paper_bgcolor: 'rgba(0, 0, 0, 0)',
                    hovermode: 'x unified',
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
          {data.waiting_times_hist && (
            (data.waiting_times_hist.type === 'pie' && (data.waiting_times_hist.labels?.length ?? 0) > 0) ||
            (data.waiting_times_hist.x && data.waiting_times_hist.x.length > 0)
          ) && (
            <div className="card">
              <h3>
                {data.waiting_times_hist.type === 'pie'
                  ? `Total Waiting Time by ${colorBy}`
                  : 'Job Waiting Times Distribution'}
                <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}> (all jobs)</span>
              </h3>
              {data.waiting_times_hist.type === 'pie' ? (
                <PieChart
                  data={{
                    labels: data.waiting_times_hist.labels || [],
                    values: data.waiting_times_hist.values || [],
                  }}
                  valueLabel="Hours waiting"
                  colors={colorMap ? (data.waiting_times_hist.labels || []).map((label, idx) =>
                    colorMap.get(label) || COLORS[idx % COLORS.length]
                  ) : undefined}
                />
              ) : (
                <HistogramChart
                  data={data.waiting_times_hist}
                  xTitle="Waiting Time (hours)"
                  yTitle="Percentage of Jobs (%)"
                  defaultColor="#dc3545"
                  colorMap={null}
                  isHistogram={false}
                  showMedianMean={true}
                  unit="h"
                  decimalPlaces={1}
                />
              )}
            </div>
          )}
        </div>

        {/* JOB DURATION CHARTS */}
        <div className="chart-row">
          {data.job_duration_trends && data.job_duration_trends.x.length > 0 && (
            <div className="card">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                <h3>Job Duration Trends</h3>
                {!data.job_duration_trends.series && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <label style={{ fontSize: '0.9rem', fontWeight: 'normal' }}>Statistic:</label>
                    <select
                      value={jobDurationTrendStat}
                      onChange={(e) => setJobDurationTrendStat(e.target.value)}
                      style={{
                        padding: '0.4rem 0.6rem',
                        borderRadius: '4px',
                        border: '1px solid #ccc',
                        fontSize: '0.9rem',
                      }}
                    >
                      <option value="mean">Mean</option>
                      <option value="median">Median</option>
                      <option value="max">Max</option>
                      <option value="p05">P05</option>
                      <option value="p25">P25</option>
                      <option value="p75">P75</option>
                      <option value="p90">P90</option>
                      <option value="p95">P95</option>
                      <option value="p99">P99</option>
                    </select>
                  </div>
                )}
              </div>
              <TimelineChart
                data={data.job_duration_trends}
                xTitle="Period"
                yTitle="Job Duration (hours)"
                colorMap={colorMap}
                defaultColor="#28a745"
                statistic={jobDurationTrendStat}
              />
            </div>
          )}
        </div>

        <div className="chart-row">
          {data.job_duration_stacked && data.job_duration_stacked.x && data.job_duration_stacked.x.length > 0 && (
            <div className="card">
              <h3>Job Duration Distribution Over Time <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(stacked percentages)</span></h3>
              <div className="chart-container">
                <Plot
                  data={data.job_duration_stacked.series?.map((series: any) => ({
                    x: data.job_duration_stacked.x,
                    y: series.data,
                    name: series.name,
                    type: 'bar',
                    marker: { color: series.color },
                    hovertemplate: `<b>${series.name}</b><br>%{y:.1f}%<br>Period: %{x}<extra></extra>`,
                  })) || []}
                  layout={{
                    autosize: true,
                    margin: { l: 80, r: 20, t: 20, b: 60 },
                    xaxis: {
                      title: { text: 'Period', font: { size: 14 }, standoff: 10 },
                      showgrid: true,
                      gridcolor: 'rgba(128, 128, 128, 0.1)',
                      zeroline: false,
                    },
                    yaxis: {
                      title: { text: 'Percentage (%)', font: { size: 14 }, standoff: 10 },
                      showgrid: true,
                      gridcolor: 'rgba(128, 128, 128, 0.1)',
                      zeroline: false,
                      tickformat: ',',
                      range: [0, 100],
                    },
                    barmode: 'stack',
                    showlegend: true,
                    legend: {
                      orientation: 'h',
                      y: -0.2,
                      x: 0.5,
                      xanchor: 'center',
                      yanchor: 'top',
                      font: { size: 10 },
                    },
                    plot_bgcolor: 'rgba(0, 0, 0, 0)',
                    paper_bgcolor: 'rgba(0, 0, 0, 0)',
                    hovermode: 'x unified',
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
          {data.job_duration_hist && (
            (data.job_duration_hist.type === 'pie' && (data.job_duration_hist.labels?.length ?? 0) > 0) ||
            (data.job_duration_hist.x && data.job_duration_hist.x.length > 0)
          ) && (
            <div className="card">
              <h3>
                {data.job_duration_hist.type === 'pie'
                  ? `Total Job Duration by ${colorBy}`
                  : 'Job Duration Distribution'}
                <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}> (all jobs)</span>
              </h3>
              {data.job_duration_hist.type === 'pie' ? (
                <PieChart
                  data={{
                    labels: data.job_duration_hist.labels || [],
                    values: data.job_duration_hist.values || [],
                  }}
                  valueLabel="Hours runtime"
                  colors={colorMap ? (data.job_duration_hist.labels || []).map((label, idx) =>
                    colorMap.get(label) || COLORS[idx % COLORS.length]
                  ) : undefined}
                />
              ) : (
                <HistogramChart
                  data={data.job_duration_hist}
                  xTitle="Job Duration (hours)"
                  yTitle="Percentage of Jobs (%)"
                  defaultColor="#28a745"
                  colorMap={null}
                  isHistogram={false}
                  showMedianMean={true}
                  unit="h"
                  decimalPlaces={1}
                />
              )}
            </div>
          )}
        </div>
      </section>

      {/* RESOURCES SECTION */}
      <section className="section">
        <h2 className="section-title">Allocated Resources</h2>
        <div className="chart-row-3col">
          {data.cpus_per_job && data.cpus_per_job.x.length > 0 && (
            <div className="card">
              <h3>CPUs per Job <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(all jobs)</span></h3>
              <HistogramChart
                data={data.cpus_per_job}
                xTitle="Number of CPUs"
                yTitle="Number of Jobs"
                defaultColor="#04A5D5"
                colorMap={colorMap}
                isHistogram={true}
              />
            </div>
          )}
          {data.gpus_per_job && data.gpus_per_job.x.length > 0 && (
            <div className="card">
              <h3>GPUs per Job <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(GPU jobs only)</span></h3>
              <HistogramChart
                data={data.gpus_per_job}
                xTitle="Number of GPUs"
                yTitle="Number of Jobs"
                defaultColor="#EC7300"
                colorMap={colorMap}
                isHistogram={true}
              />
            </div>
          )}
          {data.nodes_per_job && data.nodes_per_job.x.length > 0 && (
            <div className="card">
              <h3>Nodes per Job <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(all jobs)</span></h3>
              <HistogramChart
                data={data.nodes_per_job}
                xTitle="Number of Nodes"
                yTitle="Number of Jobs"
                defaultColor="#17a2b8"
                colorMap={colorMap}
                isHistogram={true}
              />
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default Charts;
