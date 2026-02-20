import React from 'react';
import Plot from 'react-plotly.js';
import type { ChartColorOptions } from './chartHelpers';

interface GaugeChartProps {
  value: number;  // 0-100 percentage
  title: string;
  chartColors?: ChartColorOptions;
}

const GaugeChart: React.FC<GaugeChartProps> = ({
  value,
  title,
  chartColors,
}) => {
  // Determine color based on utilization level
  const getBarColor = (val: number): string => {
    if (val < 50) return '#28a745';  // Green - low utilization
    if (val < 80) return '#ffc107';  // Yellow - moderate
    return '#dc3545';  // Red - high utilization
  };

  const textColor = chartColors?.textColor || '#333';
  const isDark = textColor === '#ffffff' || textColor === '#fff';

  return (
    <div style={{ width: '100%', height: '220px' }}>
      <Plot
        data={[
          {
            type: 'indicator',
            mode: 'gauge+number',
            value: value,
            number: { suffix: '%', font: { size: 24, color: textColor } },
            title: { text: title, font: { size: 14, color: textColor } },
            gauge: {
              axis: {
                range: [0, 100],
                tickwidth: 1,
                tickcolor: textColor,
                tickvals: [0, 25, 50, 75, 100],
                ticktext: ['0%', '25%', '50%', '75%', '100%'],
                tickfont: { color: textColor },
              },
              bar: { color: getBarColor(value), thickness: 0.75 },
              bgcolor: isDark ? '#1a1a1a' : 'white',
              borderwidth: 2,
              bordercolor: isDark ? '#404040' : '#ddd',
              steps: [
                { range: [0, 50], color: isDark ? 'rgba(40, 167, 69, 0.2)' : 'rgba(40, 167, 69, 0.1)' },
                { range: [50, 80], color: isDark ? 'rgba(255, 193, 7, 0.2)' : 'rgba(255, 193, 7, 0.1)' },
                { range: [80, 100], color: isDark ? 'rgba(220, 53, 69, 0.2)' : 'rgba(220, 53, 69, 0.1)' },
              ],
              threshold: {
                line: { color: textColor, width: 2 },
                thickness: 0.75,
                value: value,
              },
            },
          },
        ]}
        layout={{
          autosize: true,
          margin: { l: 30, r: 30, t: 60, b: 20 },
          paper_bgcolor: 'rgba(0,0,0,0)',
          font: { color: textColor },
        }}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
        config={{ responsive: true, displayModeBar: false }}
      />
    </div>
  );
};

export default GaugeChart;
