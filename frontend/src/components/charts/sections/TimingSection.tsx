import React, { useState } from 'react';
import type { AggregatedChartsResponse } from '../../../types';
import type { ChartColors } from '../../../hooks/useDarkMode';
import type { TimingStats } from '../../../hooks/useTimingStats';
import { formatHours } from '../../../hooks/useTimingStats';
import TimelineChart from '../TimelineChart';
import PieChart from '../PieChart';
import HistogramChart from '../HistogramChart';
import StackedPercentageChart from '../StackedPercentageChart';
import { COLORS } from '../chartHelpers';

interface TimingSectionProps {
  data: AggregatedChartsResponse;
  colorMap: Map<string, string> | null;
  colorBy: string;
  chartColors: ChartColors;
  isDark: boolean;
  timingStats: TimingStats | null;
}

const TimingSection: React.FC<TimingSectionProps> = ({
  data,
  colorMap,
  colorBy,
  chartColors,
  isDark,
  timingStats,
}) => {
  const [waitingTimeTrendStat, setWaitingTimeTrendStat] = useState<string>('median');
  const [jobDurationTrendStat, setJobDurationTrendStat] = useState<string>('median');
  const [showWaitingTimeCharts, setShowWaitingTimeCharts] = useState<boolean>(true);
  const [showJobDurationCharts, setShowJobDurationCharts] = useState<boolean>(true);

  return (
    <section className="section">
      <h2 className="section-title">Timing</h2>

      {/* TREND CHARTS - Both collapsible */}
      <div className="timing-trends-row">
        {/* Waiting Time Trends */}
        <div className="timing-subsection">
          <div className="timing-subsection-header">
            <h3>Waiting Times</h3>
            <div className="timing-stats-row">
              <div className="timing-stat">
                <span className="timing-stat-label">Median</span>
                <span className="timing-stat-value">{formatHours(timingStats?.waitMedian ?? null)}</span>
              </div>
              <div className="timing-stat">
                <span className="timing-stat-label">P95</span>
                <span className="timing-stat-value timing-stat-warning">{formatHours(timingStats?.waitP95 ?? null)}</span>
              </div>
              <div className="timing-stat">
                <span className="timing-stat-label">Max</span>
                <span className="timing-stat-value timing-stat-danger">{formatHours(timingStats?.waitMax ?? null)}</span>
              </div>
            </div>
          </div>
          {data.waiting_times_trends && data.waiting_times_trends.x.length > 0 && (
            <div className="collapsible-chart">
              <div
                className="collapsible-chart-header"
                onClick={() => setShowWaitingTimeCharts(!showWaitingTimeCharts)}
              >
                <span className="collapse-icon">{showWaitingTimeCharts ? '-' : '+'}</span>
                <span>Waiting Time Trends</span>
              </div>
              {showWaitingTimeCharts && (
                <div className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3>Waiting Time Trends</h3>
                    {!data.waiting_times_trends.series && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <label style={{ fontSize: '0.9rem', fontWeight: 'normal' }}>Statistic:</label>
                        <select
                          value={waitingTimeTrendStat}
                          onChange={(e) => setWaitingTimeTrendStat(e.target.value)}
                          className="stat-select"
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
                    chartColors={chartColors}
                  />
                </div>
              )}
            </div>
          )}
        </div>

        {/* Job Duration Trends */}
        <div className="timing-subsection">
          <div className="timing-subsection-header">
            <h3>Job Duration</h3>
            <div className="timing-stats-row">
              <div className="timing-stat">
                <span className="timing-stat-label">Median</span>
                <span className="timing-stat-value">{formatHours(timingStats?.durationMedian ?? null)}</span>
              </div>
              <div className="timing-stat">
                <span className="timing-stat-label">P95</span>
                <span className="timing-stat-value">{formatHours(timingStats?.durationP95 ?? null)}</span>
              </div>
              <div className="timing-stat">
                <span className="timing-stat-label">Max</span>
                <span className="timing-stat-value">{formatHours(timingStats?.durationMax ?? null)}</span>
              </div>
            </div>
          </div>
          {data.job_duration_trends && data.job_duration_trends.x.length > 0 && (
            <div className="collapsible-chart">
              <div
                className="collapsible-chart-header"
                onClick={() => setShowJobDurationCharts(!showJobDurationCharts)}
              >
                <span className="collapse-icon">{showJobDurationCharts ? '-' : '+'}</span>
                <span>Job Duration Trends</span>
              </div>
              {showJobDurationCharts && (
                <div className="card">
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <h3>Job Duration Trends</h3>
                    {!data.job_duration_trends.series && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <label style={{ fontSize: '0.9rem', fontWeight: 'normal' }}>Statistic:</label>
                        <select
                          value={jobDurationTrendStat}
                          onChange={(e) => setJobDurationTrendStat(e.target.value)}
                          className="stat-select"
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
                    chartColors={chartColors}
                  />
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* STACKED DISTRIBUTION CHARTS */}
      <div className="chart-row-equal">
        {data.waiting_times_stacked && data.waiting_times_stacked.x && data.waiting_times_stacked.x.length > 0 && (
          <StackedPercentageChart
            data={data.waiting_times_stacked}
            title="Waiting Time Distribution Over Time"
            chartColors={chartColors}
            isDark={isDark}
          />
        )}
        {data.job_duration_stacked && data.job_duration_stacked.x && data.job_duration_stacked.x.length > 0 && (
          <StackedPercentageChart
            data={data.job_duration_stacked}
            title="Job Duration Distribution Over Time"
            chartColors={chartColors}
            isDark={isDark}
          />
        )}
      </div>

      {/* HISTOGRAM CHARTS */}
      <div className="chart-row-equal">
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
                chartColors={chartColors}
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
                chartColors={chartColors}
              />
            )}
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
                chartColors={chartColors}
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
                chartColors={chartColors}
              />
            )}
          </div>
        )}
      </div>
    </section>
  );
};

export default TimingSection;
