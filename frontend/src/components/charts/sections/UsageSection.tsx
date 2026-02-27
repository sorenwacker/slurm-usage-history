import React from 'react';
import type { AggregatedChartsResponse, ChartData } from '../../../types';
import type { ChartColors } from '../../../hooks/useDarkMode';
import StackedAreaChart from '../StackedAreaChart';
import PieChart from '../PieChart';
import HistogramChart from '../HistogramChart';
import GaugeChart from '../GaugeChart';
import { COLORS } from '../chartHelpers';

interface ProcessedNodeData {
  cpu: ChartData | null;
  gpu: ChartData | null;
}

interface ClusterUtilization {
  cpu: number | null;
  gpu: number | null;
}

interface UsageSectionProps {
  data: AggregatedChartsResponse;
  colorMap: Map<string, string> | null;
  colorBy: string;
  periodType: string;
  chartColors: ChartColors;
  processedNodeData: ProcessedNodeData;
  clusterUtilization: ClusterUtilization;
  hideUnusedNodes: boolean;
  setHideUnusedNodes: (value: boolean) => void;
  sortByUsage: boolean;
  setSortByUsage: (value: boolean) => void;
  normalizeNodeUsage: boolean;
  setNormalizeNodeUsage: (value: boolean) => void;
}

const UsageSection: React.FC<UsageSectionProps> = ({
  data,
  colorMap,
  colorBy,
  periodType,
  chartColors,
  processedNodeData,
  clusterUtilization,
  hideUnusedNodes,
  setHideUnusedNodes,
  sortByUsage,
  setSortByUsage,
  normalizeNodeUsage,
  setNormalizeNodeUsage,
}) => {
  return (
    <section className="section-combined">
      <div className="section-header">
        <h2>CPU Usage</h2>
        <h2>GPU Usage</h2>
      </div>
      <div className="chart-row-4col">
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
              chartColors={chartColors}
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
                chartColors={chartColors}
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
                chartColors={chartColors}
              />
            )}
          </div>
        )}
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
              chartColors={chartColors}
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
                chartColors={chartColors}
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
                chartColors={chartColors}
              />
            )}
          </div>
        )}
      </div>

      {/* Node Usage Section */}
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

          {/* Utilization gauges */}
          {(clusterUtilization.cpu !== null || clusterUtilization.gpu !== null) && (
            <div className="gauge-grid">
              {clusterUtilization.cpu !== null && (
                <div className="card gauge-card">
                  <GaugeChart
                    value={Math.round(clusterUtilization.cpu * 10) / 10}
                    title="Average CPU Utilization"
                    chartColors={chartColors}
                  />
                </div>
              )}
              {clusterUtilization.gpu !== null && (
                <div className="card gauge-card">
                  <GaugeChart
                    value={Math.round(clusterUtilization.gpu * 10) / 10}
                    title="Average GPU Utilization"
                    chartColors={chartColors}
                  />
                </div>
              )}
            </div>
          )}

          <div className="chart-row-equal">
            {processedNodeData.cpu && processedNodeData.cpu.x.length > 0 && (
              <div className="card">
                <h3>
                  CPU Usage by Node{' '}
                  {processedNodeData.cpu.normalized && (
                    <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>
                      (% of capacity)
                    </span>
                  )}
                </h3>
                <StackedAreaChart
                  data={processedNodeData.cpu}
                  xTitle="Node"
                  yTitle={processedNodeData.cpu.normalized ? "Utilization (%)" : "CPU Hours"}
                  defaultColor="#04A5D5"
                  colorMap={colorMap}
                  chartType="bar"
                  barMode="stack"
                  chartColors={chartColors}
                />
              </div>
            )}
            {processedNodeData.gpu && processedNodeData.gpu.x.length > 0 && (
              <div className="card">
                <h3>
                  GPU Usage by Node{' '}
                  {processedNodeData.gpu.normalized && (
                    <span style={{ fontSize: '0.85rem', color: '#666', fontWeight: 'normal' }}>
                      (% of capacity)
                    </span>
                  )}
                </h3>
                <StackedAreaChart
                  data={processedNodeData.gpu}
                  xTitle="Node"
                  yTitle={processedNodeData.gpu.normalized ? "Utilization (%)" : "GPU Hours"}
                  defaultColor="#EC7300"
                  colorMap={colorMap}
                  chartType="bar"
                  barMode="stack"
                  chartColors={chartColors}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </section>
  );
};

export default UsageSection;
