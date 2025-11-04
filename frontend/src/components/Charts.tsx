import React, { useState } from 'react';
import Plot from 'react-plotly.js';
import type { AggregatedChartsResponse, ChartData } from '../types';

interface ChartsProps {
  data: AggregatedChartsResponse | undefined;
  hideUnusedNodes: boolean;
  setHideUnusedNodes: (value: boolean) => void;
  sortByUsage: boolean;
  setSortByUsage: (value: boolean) => void;
}

// Base color palette for reference (used for pie charts and fallbacks)
const COLORS = [
  '#04A5D5', '#EC7300', '#28a745', '#6f42c1', '#dc3545',
  '#17a2b8', '#ffc107', '#e83e8c', '#6c757d', '#fd7e14'
];

// Generate a distinct color using HSL color space
// This creates unlimited unique colors with good visual distinction
const generateColorFromIndex = (index: number, total: number): string => {
  // Use golden angle approximation for better color distribution
  const goldenAngle = 137.508;
  const hue = (index * goldenAngle) % 360;

  // Vary saturation and lightness to create more distinct colors
  // This helps when there are many categories
  const saturationVariations = [75, 65, 85, 55];
  const lightnessVariations = [50, 60, 40, 55];

  const satIndex = Math.floor(index / 30) % saturationVariations.length;
  const lightIndex = Math.floor(index / 15) % lightnessVariations.length;

  const saturation = saturationVariations[satIndex];
  const lightness = lightnessVariations[lightIndex];

  return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
};

// Helper function to generate an array of colors for bar charts
// This centralizes the color generation logic for all bar charts
const generateBarColors = (dataLength: number): string[] => {
  return Array.from({ length: dataLength }, (_, idx) =>
    generateColorFromIndex(idx, dataLength)
  );
};

// Helper function to create a consistent color mapping based on all unique labels
const createGlobalColorMap = (allLabels: string[]): Map<string, string> => {
  const uniqueLabels = Array.from(new Set(allLabels)).sort();
  const colorMap = new Map<string, string>();
  const total = uniqueLabels.length;

  uniqueLabels.forEach((label, index) => {
    // For first 10 labels, use the predefined colors for better consistency with existing charts
    // For labels beyond 10, use generated colors
    if (index < COLORS.length) {
      colorMap.set(label, COLORS[index]);
    } else {
      colorMap.set(label, generateColorFromIndex(index, total));
    }
  });
  return colorMap;
};

// Helper function to get color for a label
const getColorForLabel = (label: string, colorMap: Map<string, string> | null): string => {
  if (colorMap && colorMap.has(label)) {
    return colorMap.get(label)!;
  }
  // Fallback to first color if no mapping exists
  return COLORS[0];
};

// Simplified: Generate Plotly traces from chart data
// Handles both single-series (y array) and multi-series (series array) automatically
const generateChartTraces = (chartData: ChartData, chartType: 'area' | 'bar', defaultColor: string, colorMap: Map<string, string> | null, defaultName: string = ''): any[] => {
  if (!chartData || !chartData.x || chartData.x.length === 0) {
    return [];
  }

  // Multi-series data (grouped by color_by)
  if (chartData.series && chartData.series.length > 0) {
    if (chartType === 'area') {
      // Stacked area chart
      return chartData.series.map((series, index) => {
        const color = getColorForLabel(String(series.name), colorMap);
        return {
          x: chartData.x,
          y: series.data,
          type: 'scatter',
          mode: 'lines',
          fill: index === 0 ? 'tozeroy' : 'tonexty',
          stackgroup: 'one',
          name: String(series.name),
          marker: { color: color },
          hovertemplate: '<b>%{fullData.name}</b><br>Period: %{x}<br>Value: %{y:,.0f}<extra></extra>',
        };
      });
    } else {
      // Stacked bar chart
      return chartData.series.map((series) => ({
        x: chartData.x,
        y: series.data,
        type: 'bar',
        name: String(series.name),
        marker: { color: getColorForLabel(String(series.name), colorMap) },
        hovertemplate: '<b>%{fullData.name}</b><br>%{x}<br>Value: %{y:,.0f}<extra></extra>',
      }));
    }
  }

  // Single-series data (no grouping)
  if (chartData.y) {
    if (chartType === 'area') {
      // Simple area chart
      return [{
        x: chartData.x,
        y: chartData.y,
        type: 'scatter',
        mode: 'lines+markers',
        fill: 'tozeroy',
        line: { color: defaultColor, width: 2 },
        marker: { color: defaultColor, size: 8 },
        name: defaultName,
        hovertemplate: '<b>%{fullData.name}</b><br>Period: %{x}<br>Value: %{y:,.0f}<extra></extra>',
      }];
    } else {
      // Simple bar chart - color each bar based on category if we have a colorMap
      // Generate colors for each bar (either from colorMap or generate new ones)
      const colors = chartData.x.map((category, idx) => {
        const categoryStr = String(category);
        // Try to use color from colorMap first (for consistency across charts)
        if (colorMap && colorMap.has(categoryStr)) {
          return colorMap.get(categoryStr);
        }
        // Otherwise generate color based on index
        return generateColorFromIndex(idx, chartData.x.length);
      });

      return [{
        x: chartData.x,
        y: chartData.y,
        type: 'bar',
        marker: { color: colors },
        name: defaultName,
        hovertemplate: '<b>%{x}</b><br>Value: %{y:,.0f}<extra></extra>',
      }];
    }
  }

  return [];
};

// Common layout settings for better chart consistency
const getCommonLayout = (xTitle: string, yTitle: string, showLegend: boolean = false) => ({
  autosize: true,
  margin: { l: 60, r: showLegend ? 220 : 20, t: 20, b: 80 },
  xaxis: {
    title: xTitle,
    showgrid: true,
    gridcolor: 'rgba(128, 128, 128, 0.1)',
    zeroline: false,
  },
  yaxis: {
    title: yTitle,
    showgrid: true,
    gridcolor: 'rgba(128, 128, 128, 0.1)',
    zeroline: false,
    tickformat: ',',  // Thousands separator
  },
  hovermode: 'x unified',
  showlegend: showLegend,
  legend: {
    x: 1.01,
    y: 1,
    xanchor: 'left',
    yanchor: 'top',
    bgcolor: 'rgba(255, 255, 255, 0.9)',
    bordercolor: '#ddd',
    borderwidth: 1,
  },
  plot_bgcolor: 'rgba(0, 0, 0, 0)',
  paper_bgcolor: 'rgba(0, 0, 0, 0)',
});

// Common config for all charts
const getCommonConfig = () => ({
  responsive: true,
  displayModeBar: true,
  displaylogo: false,
  modeBarButtonsToRemove: ['lasso2d', 'select2d'],
  toImageButtonOptions: {
    format: 'png',
    filename: 'slurm_chart',
    height: 800,
    width: 1200,
    scale: 2,
  },
});

const Charts: React.FC<ChartsProps> = ({ data, hideUnusedNodes, setHideUnusedNodes, sortByUsage, setSortByUsage }) => {
  const [activeNodeTab, setActiveNodeTab] = useState<'cpu' | 'gpu'>('cpu');
  const [waitingTimeTrendStat, setWaitingTimeTrendStat] = useState<string>('median');
  const [jobDurationTrendStat, setJobDurationTrendStat] = useState<string>('median');

  // Create color map synchronously during render (not in useEffect)
  // This ensures the color map is available immediately when charts need it
  const colorMap = React.useMemo(() => {
    if (!data) {
      return null;
    }

    // Collect all unique series labels from all chart data
    const allLabels: string[] = [];

    // Helper to extract series names from chart data
    const extractSeriesNames = (chartData: ChartData | undefined) => {
      if (chartData?.series) {
        chartData.series.forEach(series => allLabels.push(String(series.name)));
      }
    };

    // Extract from all chart data that has series
    extractSeriesNames(data.active_users_over_time);
    extractSeriesNames(data.jobs_over_time);
    extractSeriesNames(data.cpu_usage_over_time);
    extractSeriesNames(data.gpu_usage_over_time);
    extractSeriesNames(data.cpu_hours_by_account);
    extractSeriesNames(data.gpu_hours_by_account);
    extractSeriesNames(data.node_cpu_usage);
    extractSeriesNames(data.node_gpu_usage);
    extractSeriesNames(data.waiting_times_over_time);
    extractSeriesNames(data.job_duration_over_time);
    extractSeriesNames(data.waiting_times_hist);
    extractSeriesNames(data.job_duration_hist);

    // Create and return the color map
    return allLabels.length > 0 ? createGlobalColorMap(allLabels) : null;
  }, [data]);

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
              <div className="chart-container">
                <Plot
                  data={generateChartTraces(data.active_users_over_time, 'area', '#28a745', colorMap, 'Active Users')}
                  layout={{
                    ...getCommonLayout('Period', 'Number of Users', data.active_users_over_time.series && data.active_users_over_time.series.length > 1),
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={getCommonConfig()}
                />
              </div>
            </div>
          )}
          {data.active_users_distribution && data.active_users_distribution.x && data.active_users_distribution.x.length > 0 && (
            <div className="card">
              <h3>Active Users Distribution <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(all periods)</span></h3>
              <div className="chart-container">
                <Plot
                  data={data.active_users_distribution.type === 'histogram' ? [{
                    x: data.active_users_distribution.x,
                    y: data.active_users_distribution.y,
                    type: 'bar',
                    marker: { color: '#28a745' },
                    name: 'Frequency',
                    hovertemplate: '<b>Users per Period</b><br>Users: %{x}<br>Periods: %{y:,.0f}<extra></extra>',
                  }] : generateChartTraces(data.active_users_distribution, 'bar', '#28a745', colorMap)}
                  layout={data.active_users_distribution.type === 'histogram' ? {
                    ...getCommonLayout('Users per Period', 'Number of Periods'),
                    xaxis: {
                      ...getCommonLayout('Users per Period', 'Number of Periods').xaxis,
                      title: 'Users per Period',
                    },
                    yaxis: {
                      ...getCommonLayout('Users per Period', 'Number of Periods').yaxis,
                      title: 'Number of Periods',
                    },
                    shapes: [
                      ...(data.active_users_distribution.median !== undefined ? [{
                        type: 'line',
                        xref: 'x',
                        yref: 'paper',
                        x0: data.active_users_distribution.median,
                        y0: 0,
                        x1: data.active_users_distribution.median,
                        y1: 1,
                        line: {
                          color: 'red',
                          width: 2,
                        },
                      }] : []),
                      ...(data.active_users_distribution.average !== undefined ? [{
                        type: 'line',
                        xref: 'x',
                        yref: 'paper',
                        x0: data.active_users_distribution.average,
                        y0: 0,
                        x1: data.active_users_distribution.average,
                        y1: 1,
                        line: {
                          color: 'red',
                          width: 2,
                          dash: 'dash',
                        },
                      }] : []),
                    ],
                    annotations: [
                      ...(data.active_users_distribution.median !== undefined ? [{
                        x: data.active_users_distribution.median,
                        y: 1,
                        xref: 'x',
                        yref: 'paper',
                        text: `Median: ${data.active_users_distribution.median.toFixed(0)}`,
                        showarrow: true,
                        arrowhead: 2,
                        ax: 0,
                        ay: -40,
                        bgcolor: 'rgba(255,255,255,0.8)',
                        bordercolor: 'rgba(0,0,0,0.2)',
                        borderwidth: 1,
                        borderpad: 4,
                      }] : []),
                      ...(data.active_users_distribution.average !== undefined ? [{
                        x: data.active_users_distribution.average,
                        y: 1,
                        xref: 'x',
                        yref: 'paper',
                        text: `Mean: ${data.active_users_distribution.average.toFixed(0)}`,
                        showarrow: true,
                        arrowhead: 2,
                        ax: 0,
                        ay: -80,
                        bgcolor: 'rgba(255,255,255,0.8)',
                        bordercolor: 'rgba(255,0,0,0.5)',
                        borderwidth: 1,
                        borderpad: 4,
                      }] : []),
                    ],
                  } : getCommonLayout('Category', 'Count')}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
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
              <h3>Number of Jobs</h3>
              <div className="chart-container">
                <Plot
                  data={generateChartTraces(data.jobs_over_time, 'area', '#6f42c1', colorMap, 'Jobs')}
                  layout={{
                    ...getCommonLayout('Period', 'Number of Jobs', data.jobs_over_time.series && data.jobs_over_time.series.length > 1),
                    barmode: 'stack',
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={getCommonConfig()}
                />
              </div>
            </div>
          )}
          {data.jobs_distribution && data.jobs_distribution.x && data.jobs_distribution.x.length > 0 && (
            <div className="card">
              <h3>Jobs Distribution <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(all periods)</span></h3>
              <div className="chart-container">
                <Plot
                  data={data.jobs_distribution.type === 'histogram' ? [
                    {
                      x: data.jobs_distribution.x,
                      y: data.jobs_distribution.y,
                      type: 'bar',
                      marker: { color: '#6f42c1' },
                      name: 'Frequency',
                      hovertemplate: '<b>Jobs per Period</b><br>Jobs: %{x}<br>Periods: %{y:,.0f}<extra></extra>',
                    },
                  ] : generateChartTraces(data.jobs_distribution, 'bar', '#6f42c1', colorMap)}
                  layout={data.jobs_distribution.type === 'histogram' ? {
                    ...getCommonLayout('Jobs per Period', 'Number of Periods'),
                    xaxis: {
                      ...getCommonLayout('Jobs per Period', 'Number of Periods').xaxis,
                      title: 'Jobs per Period',
                    },
                    yaxis: {
                      ...getCommonLayout('Jobs per Period', 'Number of Periods').yaxis,
                      title: 'Number of Periods',
                    },
                    shapes: [
                      ...(data.jobs_distribution.median !== undefined ? [{
                        type: 'line',
                        xref: 'x',
                        yref: 'paper',
                        x0: data.jobs_distribution.median,
                        y0: 0,
                        x1: data.jobs_distribution.median,
                        y1: 1,
                        line: {
                          color: 'red',
                          width: 2,
                        },
                      }] : []),
                      ...(data.jobs_distribution.average !== undefined ? [{
                        type: 'line',
                        xref: 'x',
                        yref: 'paper',
                        x0: data.jobs_distribution.average,
                        y0: 0,
                        x1: data.jobs_distribution.average,
                        y1: 1,
                        line: {
                          color: 'red',
                          width: 2,
                          dash: 'dash',
                        },
                      }] : []),
                    ],
                    annotations: [
                      ...(data.jobs_distribution.median !== undefined ? [{
                        x: data.jobs_distribution.median,
                        y: 1,
                        xref: 'x',
                        yref: 'paper',
                        text: `Median: ${data.jobs_distribution.median.toFixed(0)}`,
                        showarrow: true,
                        arrowhead: 2,
                        ax: 0,
                        ay: -40,
                        bgcolor: 'rgba(255,255,255,0.8)',
                        bordercolor: 'rgba(0,0,0,0.2)',
                        borderwidth: 1,
                        borderpad: 4,
                      }] : []),
                      ...(data.jobs_distribution.average !== undefined ? [{
                        x: data.jobs_distribution.average,
                        y: 1,
                        xref: 'x',
                        yref: 'paper',
                        text: `Mean: ${data.jobs_distribution.average.toFixed(0)}`,
                        showarrow: true,
                        arrowhead: 2,
                        ax: 0,
                        ay: -80,
                        bgcolor: 'rgba(255,255,255,0.8)',
                        bordercolor: 'rgba(255,0,0,0.5)',
                        borderwidth: 1,
                        borderpad: 4,
                      }] : []),
                    ],
                  } : getCommonLayout('Category', 'Count')}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
          {data.jobs_distribution && data.jobs_distribution.type === 'pie' && (
            <div className="card">
              <h3>Jobs Distribution</h3>
              <div className="chart-container">
                <Plot
                  data={[
                    {
                      labels: data.jobs_distribution.labels,
                      values: data.jobs_distribution.values,
                      type: 'pie',
                      marker: { colors: COLORS },
                      textposition: 'inside',
                      textinfo: 'label+percent',
                      hovertemplate: '<b>%{label}</b><br>Jobs: %{value:,.0f}<br>Percentage: %{percent}<extra></extra>',
                    },
                  ]}
                  layout={{
                    autosize: true,
                    margin: { l: 20, r: 20, t: 20, b: 20 },
                    showlegend: true,
                    legend: { x: 1.05, y: 0.5, xanchor: 'left', yanchor: 'middle' },
                    plot_bgcolor: 'rgba(0, 0, 0, 0)',
                    paper_bgcolor: 'rgba(0, 0, 0, 0)',
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={getCommonConfig()}
                />
              </div>
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
              <div className="chart-container">
                <Plot
                  data={generateChartTraces(data.cpu_usage_over_time, 'area', '#04A5D5', colorMap, 'CPU Hours')}
                  layout={{
                    ...getCommonLayout('Period', 'CPU Hours', data.cpu_usage_over_time.series && data.cpu_usage_over_time.series.length > 1),
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
          {data.cpu_hours_by_account && data.cpu_hours_by_account.x.length > 0 && (
            <div className="card">
              <h3>CPU Usage Distribution</h3>
              <div className="chart-container">
                <Plot
                  data={data.cpu_hours_by_account.type === 'histogram' ? [
                    {
                      x: data.cpu_hours_by_account.x,
                      y: data.cpu_hours_by_account.y,
                      type: 'bar',
                      marker: { color: '#04A5D5' },
                      hovertemplate: '<b>CPU Hours per Period</b><br>Range: %{x:.0f}h<br>Periods: %{y:,.0f}<extra></extra>',
                    },
                  ] : generateChartTraces(data.cpu_hours_by_account, 'bar', '#04A5D5', colorMap)}
                  layout={data.cpu_hours_by_account.type === 'histogram' ? {
                    ...getCommonLayout('CPU Hours per Period', 'Number of Periods'),
                    xaxis: {
                      ...getCommonLayout('CPU Hours per Period', 'Number of Periods').xaxis,
                      title: 'CPU Hours per Period',
                    },
                    yaxis: {
                      ...getCommonLayout('CPU Hours per Period', 'Number of Periods').yaxis,
                      title: 'Number of Periods',
                    },
                    shapes: [
                      ...(data.cpu_hours_by_account.median !== undefined ? [{
                        type: 'line',
                        xref: 'x',
                        yref: 'paper',
                        x0: data.cpu_hours_by_account.median,
                        y0: 0,
                        x1: data.cpu_hours_by_account.median,
                        y1: 1,
                        line: {
                          color: 'red',
                          width: 2,
                        },
                      }] : []),
                      ...(data.cpu_hours_by_account.mean !== undefined ? [{
                        type: 'line',
                        xref: 'x',
                        yref: 'paper',
                        x0: data.cpu_hours_by_account.mean,
                        y0: 0,
                        x1: data.cpu_hours_by_account.mean,
                        y1: 1,
                        line: {
                          color: 'red',
                          width: 2,
                          dash: 'dash',
                        },
                      }] : []),
                    ],
                    annotations: [
                      ...(data.cpu_hours_by_account.median !== undefined ? [{
                        x: data.cpu_hours_by_account.median,
                        y: 1,
                        xref: 'x',
                        yref: 'paper',
                        text: `Median: ${data.cpu_hours_by_account.median.toFixed(0)}h`,
                        showarrow: true,
                        arrowhead: 2,
                        ax: 0,
                        ay: -40,
                        bgcolor: 'rgba(255,255,255,0.8)',
                        bordercolor: 'rgba(0,0,0,0.2)',
                        borderwidth: 1,
                        borderpad: 4,
                      }] : []),
                      ...(data.cpu_hours_by_account.mean !== undefined ? [{
                        x: data.cpu_hours_by_account.mean,
                        y: 1,
                        xref: 'x',
                        yref: 'paper',
                        text: `Mean: ${data.cpu_hours_by_account.mean.toFixed(0)}h`,
                        showarrow: true,
                        arrowhead: 2,
                        ax: 0,
                        ay: -80,
                        bgcolor: 'rgba(255,255,255,0.8)',
                        bordercolor: 'rgba(255,0,0,0.5)',
                        borderwidth: 1,
                        borderpad: 4,
                      }] : []),
                    ],
                  } : {
                    ...getCommonLayout('Account', 'CPU Hours'),
                    xaxis: {
                      ...getCommonLayout('Account', 'CPU Hours').xaxis,
                      tickangle: -45,
                    },
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
        </div>
        <div className="chart-row">
          {data.gpu_usage_over_time && data.gpu_usage_over_time.x.length > 0 && (
            <div className="card">
              <h3>GPU Usage</h3>
              <div className="chart-container">
                <Plot
                  data={generateChartTraces(data.gpu_usage_over_time, 'area', '#EC7300', colorMap, 'GPU Hours')}
                  layout={{
                    ...getCommonLayout('Period', 'GPU Hours', data.gpu_usage_over_time.series && data.gpu_usage_over_time.series.length > 1),
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
          {data.gpu_hours_by_account && data.gpu_hours_by_account.x.length > 0 && (
            <div className="card">
              <h3>GPU Usage Distribution</h3>
              <div className="chart-container">
                <Plot
                  data={data.gpu_hours_by_account.type === 'histogram' ? [
                    {
                      x: data.gpu_hours_by_account.x,
                      y: data.gpu_hours_by_account.y,
                      type: 'bar',
                      marker: { color: '#EC7300' },
                      hovertemplate: '<b>GPU Hours per Period</b><br>Range: %{x:.0f}h<br>Periods: %{y:,.0f}<extra></extra>',
                    },
                  ] : generateChartTraces(data.gpu_hours_by_account, 'bar', '#EC7300', colorMap)}
                  layout={data.gpu_hours_by_account.type === 'histogram' ? {
                    ...getCommonLayout('GPU Hours per Period', 'Number of Periods'),
                    xaxis: {
                      ...getCommonLayout('GPU Hours per Period', 'Number of Periods').xaxis,
                      title: 'GPU Hours per Period',
                    },
                    yaxis: {
                      ...getCommonLayout('GPU Hours per Period', 'Number of Periods').yaxis,
                      title: 'Number of Periods',
                    },
                    shapes: [
                      ...(data.gpu_hours_by_account.median !== undefined ? [{
                        type: 'line',
                        xref: 'x',
                        yref: 'paper',
                        x0: data.gpu_hours_by_account.median,
                        y0: 0,
                        x1: data.gpu_hours_by_account.median,
                        y1: 1,
                        line: {
                          color: 'red',
                          width: 2,
                        },
                      }] : []),
                      ...(data.gpu_hours_by_account.mean !== undefined ? [{
                        type: 'line',
                        xref: 'x',
                        yref: 'paper',
                        x0: data.gpu_hours_by_account.mean,
                        y0: 0,
                        x1: data.gpu_hours_by_account.mean,
                        y1: 1,
                        line: {
                          color: 'red',
                          width: 2,
                          dash: 'dash',
                        },
                      }] : []),
                    ],
                    annotations: [
                      ...(data.gpu_hours_by_account.median !== undefined ? [{
                        x: data.gpu_hours_by_account.median,
                        y: 1,
                        xref: 'x',
                        yref: 'paper',
                        text: `Median: ${data.gpu_hours_by_account.median.toFixed(0)}h`,
                        showarrow: true,
                        arrowhead: 2,
                        ax: 0,
                        ay: -40,
                        bgcolor: 'rgba(255,255,255,0.8)',
                        bordercolor: 'rgba(0,0,0,0.2)',
                        borderwidth: 1,
                        borderpad: 4,
                      }] : []),
                      ...(data.gpu_hours_by_account.mean !== undefined ? [{
                        x: data.gpu_hours_by_account.mean,
                        y: 1,
                        xref: 'x',
                        yref: 'paper',
                        text: `Mean: ${data.gpu_hours_by_account.mean.toFixed(0)}h`,
                        showarrow: true,
                        arrowhead: 2,
                        ax: 0,
                        ay: -80,
                        bgcolor: 'rgba(255,255,255,0.8)',
                        bordercolor: 'rgba(255,0,0,0.5)',
                        borderwidth: 1,
                        borderpad: 4,
                      }] : []),
                    ],
                  } : {
                    ...getCommonLayout('Account', 'GPU Hours'),
                    xaxis: {
                      ...getCommonLayout('Account', 'GPU Hours').xaxis,
                      tickangle: -45,
                    },
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
        </div>
        {(data.node_cpu_usage?.x.length > 0 || data.node_gpu_usage?.x.length > 0) && (
          <div className="card" style={{ marginTop: '1.5rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3>CPU/GPU Usage by Node</h3>
              <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
                  <input
                    type="checkbox"
                    checked={hideUnusedNodes}
                    onChange={(e) => setHideUnusedNodes(e.target.checked)}
                  />
                  Hide unused nodes
                </label>
                <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.9rem' }}>
                  <input
                    type="checkbox"
                    checked={sortByUsage}
                    onChange={(e) => setSortByUsage(e.target.checked)}
                  />
                  Sort by usage
                </label>
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '1rem', borderBottom: '1px solid #e0e0e0' }}>
              <button
                onClick={() => setActiveNodeTab('cpu')}
                style={{
                  padding: '0.5rem 1rem',
                  border: 'none',
                  background: activeNodeTab === 'cpu' ? '#04A5D5' : 'transparent',
                  color: activeNodeTab === 'cpu' ? 'white' : '#666',
                  cursor: 'pointer',
                  borderRadius: '4px 4px 0 0',
                  fontWeight: activeNodeTab === 'cpu' ? 'bold' : 'normal',
                }}
              >
                CPU Usage
              </button>
              <button
                onClick={() => setActiveNodeTab('gpu')}
                style={{
                  padding: '0.5rem 1rem',
                  border: 'none',
                  background: activeNodeTab === 'gpu' ? '#EC7300' : 'transparent',
                  color: activeNodeTab === 'gpu' ? 'white' : '#666',
                  cursor: 'pointer',
                  borderRadius: '4px 4px 0 0',
                  fontWeight: activeNodeTab === 'gpu' ? 'bold' : 'normal',
                }}
              >
                GPU Usage
              </button>
            </div>
            <div className="chart-container">
              {activeNodeTab === 'cpu' && data.node_cpu_usage?.x.length > 0 && (
                <Plot
                  data={generateChartTraces(data.node_cpu_usage, 'bar', '#04A5D5', colorMap)}
                  layout={{
                    ...getCommonLayout('Node', 'CPU Hours', data.node_cpu_usage.series && data.node_cpu_usage.series.length > 1),
                    xaxis: {
                      ...getCommonLayout('Node', 'CPU Hours').xaxis,
                      tickangle: -45,
                    },
                    barmode: 'stack',
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              )}
              {activeNodeTab === 'gpu' && data.node_gpu_usage?.x.length > 0 && (
                <Plot
                  data={generateChartTraces(data.node_gpu_usage, 'bar', '#EC7300', colorMap)}
                  layout={{
                    ...getCommonLayout('Node', 'GPU Hours', data.node_gpu_usage.series && data.node_gpu_usage.series.length > 1),
                    xaxis: {
                      ...getCommonLayout('Node', 'GPU Hours').xaxis,
                      tickangle: -45,
                    },
                    barmode: 'stack',
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              )}
              {activeNodeTab === 'cpu' && (!data.node_cpu_usage?.x || data.node_cpu_usage.x.length === 0) && (
                <p style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
                  No CPU node usage data available.
                </p>
              )}
              {activeNodeTab === 'gpu' && (!data.node_gpu_usage?.x || data.node_gpu_usage.x.length === 0) && (
                <p style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
                  No GPU node usage data available.
                </p>
              )}
            </div>
          </div>
        )}
      </section>

      {/* TIMING SECTION */}
      <section className="section">
        <h2 className="section-title">Timing</h2>

        {/* WAITING TIME CHARTS */}
        <div className="chart-row">
          {data.waiting_times_over_time && data.waiting_times_over_time.x.length > 0 && (
            <div className="card">
              <h3>Average Waiting Time Over Time</h3>
              <div className="chart-container">
                <Plot
                  data={generateChartTraces(data.waiting_times_over_time, 'area', '#dc3545', colorMap, 'Avg Waiting Time (hrs)')}
                  layout={{
                    ...getCommonLayout('Period', 'Average Waiting Time (hours)', data.waiting_times_over_time.series && data.waiting_times_over_time.series.length > 1),
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
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
                      <option value="p50">P50</option>
                      <option value="p75">P75</option>
                      <option value="p90">P90</option>
                      <option value="p95">P95</option>
                      <option value="p99">P99</option>
                    </select>
                  </div>
                )}
              </div>
              <div className="chart-container">
                <Plot
                  data={
                    data.waiting_times_trends.series && data.waiting_times_trends.series.length > 0
                      ? // Multi-line mode when grouped
                        data.waiting_times_trends.series.map((series: any, idx: number) => ({
                          x: data.waiting_times_trends.x,
                          y: series.data,
                          type: 'scatter',
                          mode: 'lines+markers',
                          marker: { color: getColorForLabel(series.name), size: 8 },
                          line: { color: getColorForLabel(series.name), width: 3 },
                          name: series.name,
                        }))
                      : // Single line mode with P25-P75 range
                        [
                          // P75 upper bound (transparent line)
                          {
                            x: data.waiting_times_trends.x,
                            y: data.waiting_times_trends.stats.p75,
                            type: 'scatter',
                            mode: 'lines',
                            line: { width: 0 },
                            showlegend: false,
                            hoverinfo: 'skip',
                          },
                          // P25-P75 shaded range
                          {
                            x: data.waiting_times_trends.x,
                            y: data.waiting_times_trends.stats.p25,
                            type: 'scatter',
                            mode: 'lines',
                            fill: 'tonexty',
                            fillcolor: 'rgba(220, 53, 69, 0.15)',
                            line: { width: 0 },
                            name: 'P25-P75 Range',
                            showlegend: true,
                            hoverinfo: 'skip',
                          },
                          // Selected statistic line
                          {
                            x: data.waiting_times_trends.x,
                            y: data.waiting_times_trends.stats[waitingTimeTrendStat as keyof typeof data.waiting_times_trends.stats],
                            type: 'scatter',
                            mode: 'lines+markers',
                            marker: { color: '#dc3545', size: 6 },
                            line: { color: '#dc3545', width: 2 },
                            name: waitingTimeTrendStat.toUpperCase(),
                          },
                        ]
                  }
                  layout={{
                    ...getCommonLayout('Period', 'Waiting Time (hours)', true),
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
        </div>

        <div className="chart-row">
          {data.waiting_times_stacked && data.waiting_times_stacked.x && data.waiting_times_stacked.x.length > 0 && (
            <div className="card">
              <h3>Waiting Time Distribution Over Time <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(stacked percentages)</span></h3>
              <div className="chart-container">
                <Plot
                  data={data.waiting_times_stacked.series.map((series: any) => ({
                    x: data.waiting_times_stacked.x,
                    y: series.data,
                    name: series.name,
                    type: 'bar',
                    marker: { color: series.color },
                    hovertemplate: `<b>${series.name}</b><br>%{y:.1f}%<br>Period: %{x}<extra></extra>`,
                  }))}
                  layout={{
                    ...getCommonLayout('Period', 'Percentage (%)'),
                    barmode: 'stack',
                    yaxis: {
                      ...getCommonLayout('', '').yaxis,
                      title: 'Percentage (%)',
                      range: [0, 100],
                    },
                    legend: {
                      orientation: 'h',
                      y: -0.2,
                      x: 0.5,
                      xanchor: 'center',
                      yanchor: 'top',
                    },
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={getCommonConfig()}
                />
              </div>
            </div>
          )}
          {data.waiting_times_hist && data.waiting_times_hist.x && data.waiting_times_hist.x.length > 0 && (
            <div className="card">
              <h3>Job Waiting Times Distribution <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(all jobs)</span></h3>
            <div className="chart-container">
              <Plot
                data={
                  data.waiting_times_hist.series && data.waiting_times_hist.series.length > 0
                    ? data.waiting_times_hist.series.map((series: any, idx: number) => ({
                        x: data.waiting_times_hist.x,
                        y: series.data,
                        type: 'bar',
                        marker: { color: getColorForLabel(series.name) },
                        name: series.name,
                        hovertemplate: '<b>%{x}</b><br>Jobs: %{y:.1f}%<extra></extra>',
                      }))
                    : [{
                        x: data.waiting_times_hist.x,
                        y: data.waiting_times_hist.y,
                        type: 'bar',
                        marker: { color: '#dc3545' },
                        name: 'Waiting Time',
                        hovertemplate: '<b>%{x}</b><br>Jobs: %{y:.1f}%<extra></extra>',
                      }]
                }
                layout={{
                  ...getCommonLayout('Waiting Time (hours)', 'Percentage of Jobs (%)', data.waiting_times_hist.series && data.waiting_times_hist.series.length > 1),
                  barmode: data.waiting_times_hist.series && data.waiting_times_hist.series.length > 0 ? 'group' : 'overlay',
                  annotations: [
                    ...(data.waiting_times_hist.median !== undefined && data.waiting_times_hist.average !== undefined ? [{
                      x: 0.5,
                      y: 1.05,
                      xref: 'paper',
                      yref: 'paper',
                      text: `Median: ${data.waiting_times_hist.median.toFixed(1)}h | Mean: ${data.waiting_times_hist.average.toFixed(1)}h`,
                      showarrow: false,
                      font: {
                        size: 12,
                        color: '#d63031',
                      },
                      bgcolor: 'rgba(255,255,255,0.9)',
                      bordercolor: '#d63031',
                      borderwidth: 1,
                      borderpad: 4,
                    }] : []),
                  ],
                }}
                useResizeHandler={true}
                style={{ width: '100%', height: '400px' }}
                config={{ responsive: true }}
              />
            </div>
          </div>
        )}
        </div>

        {/* JOB DURATION CHARTS */}
        <div className="chart-row">
          {data.job_duration_over_time && data.job_duration_over_time.x.length > 0 && (
            <div className="card">
              <h3>Average Job Duration Over Time</h3>
              <div className="chart-container">
                <Plot
                  data={generateChartTraces(data.job_duration_over_time, 'area', '#28a745', colorMap, 'Avg Duration (hrs)')}
                  layout={{
                    ...getCommonLayout('Period', 'Average Job Duration (hours)', data.job_duration_over_time.series && data.job_duration_over_time.series.length > 1),
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
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
                      <option value="p50">P50</option>
                      <option value="p75">P75</option>
                      <option value="p90">P90</option>
                      <option value="p95">P95</option>
                      <option value="p99">P99</option>
                    </select>
                  </div>
                )}
              </div>
              <div className="chart-container">
                <Plot
                  data={
                    data.job_duration_trends.series && data.job_duration_trends.series.length > 0
                      ? // Multi-line mode when grouped
                        data.job_duration_trends.series.map((series: any, idx: number) => ({
                          x: data.job_duration_trends.x,
                          y: series.data,
                          type: 'scatter',
                          mode: 'lines+markers',
                          marker: { color: getColorForLabel(series.name), size: 8 },
                          line: { color: getColorForLabel(series.name), width: 3 },
                          name: series.name,
                        }))
                      : // Single line mode with P25-P75 range
                        [
                          // P75 upper bound (transparent line)
                          {
                            x: data.job_duration_trends.x,
                            y: data.job_duration_trends.stats.p75,
                            type: 'scatter',
                            mode: 'lines',
                            line: { width: 0 },
                            showlegend: false,
                            hoverinfo: 'skip',
                          },
                          // P25-P75 shaded range
                          {
                            x: data.job_duration_trends.x,
                            y: data.job_duration_trends.stats.p25,
                            type: 'scatter',
                            mode: 'lines',
                            fill: 'tonexty',
                            fillcolor: 'rgba(40, 167, 69, 0.15)',
                            line: { width: 0 },
                            name: 'P25-P75 Range',
                            showlegend: true,
                            hoverinfo: 'skip',
                          },
                          // Selected statistic line
                          {
                            x: data.job_duration_trends.x,
                            y: data.job_duration_trends.stats[jobDurationTrendStat as keyof typeof data.job_duration_trends.stats],
                            type: 'scatter',
                            mode: 'lines+markers',
                            marker: { color: '#28a745', size: 6 },
                            line: { color: '#28a745', width: 2 },
                            name: jobDurationTrendStat.toUpperCase(),
                          },
                        ]
                  }
                  layout={{
                    ...getCommonLayout('Period', 'Job Duration (hours)', true),
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
        </div>

        <div className="chart-row">
          {data.job_duration_stacked && data.job_duration_stacked.x && data.job_duration_stacked.x.length > 0 && (
            <div className="card">
              <h3>Job Duration Distribution Over Time <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(stacked percentages)</span></h3>
              <div className="chart-container">
                <Plot
                  data={data.job_duration_stacked.series.map((series: any) => ({
                    x: data.job_duration_stacked.x,
                    y: series.data,
                    name: series.name,
                    type: 'bar',
                    marker: { color: series.color },
                    hovertemplate: `<b>${series.name}</b><br>%{y:.1f}%<br>Period: %{x}<extra></extra>`,
                  }))}
                  layout={{
                    ...getCommonLayout('Period', 'Percentage (%)'),
                    barmode: 'stack',
                    yaxis: {
                      ...getCommonLayout('', '').yaxis,
                      title: 'Percentage (%)',
                      range: [0, 100],
                    },
                    legend: {
                      orientation: 'h',
                      y: -0.2,
                      x: 0.5,
                      xanchor: 'center',
                      yanchor: 'top',
                    },
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={getCommonConfig()}
                />
              </div>
            </div>
          )}
          {data.job_duration_hist && data.job_duration_hist.x && data.job_duration_hist.x.length > 0 && (
            <div className="card">
              <h3>Job Duration Distribution <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(all jobs)</span></h3>
              <div className="chart-container">
                <Plot
                  data={
                    data.job_duration_hist.series && data.job_duration_hist.series.length > 0
                      ? data.job_duration_hist.series.map((series: any, idx: number) => ({
                          x: data.job_duration_hist.x,
                          y: series.data,
                          type: 'bar',
                          marker: { color: getColorForLabel(series.name) },
                          name: series.name,
                          hovertemplate: '<b>%{x}</b><br>Jobs: %{y:.1f}%<extra></extra>',
                        }))
                      : [{
                          x: data.job_duration_hist.x,
                          y: data.job_duration_hist.y,
                          type: 'bar',
                          marker: { color: '#28a745' },
                          name: 'Duration',
                          hovertemplate: '<b>%{x}</b><br>Jobs: %{y:.1f}%<extra></extra>',
                        }]
                  }
                  layout={{
                    ...getCommonLayout('Job Duration (hours)', 'Percentage of Jobs (%)',
                      data.job_duration_hist.series && data.job_duration_hist.series.length > 1),
                    barmode: data.job_duration_hist.series && data.job_duration_hist.series.length > 0 ? 'group' : 'overlay',
                    annotations: [
                      ...(data.job_duration_hist.median !== undefined && data.job_duration_hist.average !== undefined ? [{
                        x: 0.5,
                        y: 1.05,
                        xref: 'paper',
                        yref: 'paper',
                        text: `Median: ${data.job_duration_hist.median.toFixed(1)}h | Mean: ${data.job_duration_hist.average.toFixed(1)}h`,
                        showarrow: false,
                        font: {
                          size: 12,
                          color: '#28a745',
                        },
                        bgcolor: 'rgba(255,255,255,0.9)',
                        bordercolor: '#28a745',
                        borderwidth: 1,
                        borderpad: 4,
                      }] : []),
                    ],
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
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
              <div className="chart-container">
                <Plot
                  data={[
                    {
                      x: data.cpus_per_job.x,
                      y: data.cpus_per_job.y,
                      type: 'bar',
                      marker: { color: '#28a745' },
                      hovertemplate: '<b>CPUs</b><br>Count: %{x}<br>Jobs: %{y:,.0f}<extra></extra>',
                    },
                  ]}
                  layout={{
                    ...getCommonLayout('Number of CPUs', 'Number of Jobs'),
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
          {data.gpus_per_job && data.gpus_per_job.x.length > 0 && (
            <div className="card">
              <h3>GPUs per Job <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(GPU jobs only)</span></h3>
              <div className="chart-container">
                <Plot
                  data={[
                    {
                      x: data.gpus_per_job.x,
                      y: data.gpus_per_job.y,
                      type: 'bar',
                      marker: { color: '#6f42c1' },
                      hovertemplate: '<b>GPUs</b><br>Count: %{x}<br>Jobs: %{y:,.0f}<extra></extra>',
                    },
                  ]}
                  layout={{
                    ...getCommonLayout('Number of GPUs', 'Number of Jobs'),
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
          {data.nodes_per_job && data.nodes_per_job.x.length > 0 && (
            <div className="card">
              <h3>Nodes per Job <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>(all jobs)</span></h3>
              <div className="chart-container">
                <Plot
                  data={[
                    {
                      x: data.nodes_per_job.x,
                      y: data.nodes_per_job.y,
                      type: 'bar',
                      marker: { color: '#17a2b8' },
                      hovertemplate: '<b>Nodes</b><br>Count: %{x}<br>Jobs: %{y:,.0f}<extra></extra>',
                    },
                  ]}
                  layout={{
                    ...getCommonLayout('Number of Nodes', 'Number of Jobs'),
                  }}
                  useResizeHandler={true}
                  style={{ width: '100%', height: '400px' }}
                  config={{ responsive: true }}
                />
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default Charts;
