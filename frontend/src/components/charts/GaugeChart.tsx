import React from 'react';
import Plot from 'react-plotly.js';

interface GaugeChartProps {
  value: number;  // 0-100 percentage
  title: string;
}

const GaugeChart: React.FC<GaugeChartProps> = ({
  value,
  title,
}) => {
  // Determine color based on utilization level
  const getBarColor = (val: number): string => {
    if (val < 50) return '#28a745';  // Green - low utilization
    if (val < 80) return '#ffc107';  // Yellow - moderate
    return '#dc3545';  // Red - high utilization
  };

  return (
    <div style={{ width: '100%', height: '220px' }}>
      <Plot
        data={[
          {
            type: 'indicator',
            mode: 'gauge+number',
            value: value,
            number: { suffix: '%', font: { size: 24 } },
            title: { text: title, font: { size: 14 } },
            gauge: {
              axis: {
                range: [0, 100],
                tickwidth: 1,
                tickcolor: '#666',
                tickvals: [0, 25, 50, 75, 100],
                ticktext: ['0%', '25%', '50%', '75%', '100%'],
              },
              bar: { color: getBarColor(value), thickness: 0.75 },
              bgcolor: 'white',
              borderwidth: 2,
              bordercolor: '#ddd',
              steps: [
                { range: [0, 50], color: 'rgba(40, 167, 69, 0.1)' },
                { range: [50, 80], color: 'rgba(255, 193, 7, 0.1)' },
                { range: [80, 100], color: 'rgba(220, 53, 69, 0.1)' },
              ],
              threshold: {
                line: { color: '#666', width: 2 },
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
          font: { color: '#333' },
        }}
        useResizeHandler={true}
        style={{ width: '100%', height: '100%' }}
        config={{ responsive: true, displayModeBar: false }}
      />
    </div>
  );
};

export default GaugeChart;
