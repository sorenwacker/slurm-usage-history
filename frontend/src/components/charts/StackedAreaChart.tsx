import React from 'react';
import Plot from 'react-plotly.js';
import type { ChartData } from '../../types';
import { generateChartTraces, getCommonLayout, getCommonConfig } from './chartHelpers';

interface StackedAreaChartProps {
  data: ChartData;
  xTitle: string;
  yTitle: string;
  defaultColor: string;
  colorMap: Map<string, string> | null;
  defaultName?: string;
  chartType?: 'area' | 'bar';
  barMode?: 'stack' | 'group';
}

const StackedAreaChart: React.FC<StackedAreaChartProps> = ({
  data,
  xTitle,
  yTitle,
  defaultColor,
  colorMap,
  defaultName = '',
  chartType = 'area',
  barMode = 'stack',
}) => {
  if (!data || !data.x || data.x.length === 0) {
    return null;
  }

  const showLegend = data.series && data.series.length > 1;

  const layout: any = {
    ...getCommonLayout(xTitle, yTitle, showLegend),
  };

  // Add barmode for bar charts
  if (chartType === 'bar') {
    layout.barmode = barMode;
  }

  return (
    <div className="chart-container">
      <Plot
        data={generateChartTraces(data, chartType, defaultColor, colorMap, defaultName)}
        layout={layout}
        useResizeHandler={true}
        style={{ width: '100%', height: '400px' }}
        config={getCommonConfig()}
      />
    </div>
  );
};

export default StackedAreaChart;
