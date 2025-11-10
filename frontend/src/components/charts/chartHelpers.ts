import type { ChartData } from '../../types';

// Base color palette for reference (used for pie charts and fallbacks)
export const COLORS = [
  '#04A5D5', '#EC7300', '#28a745', '#6f42c1', '#dc3545',
  '#17a2b8', '#ffc107', '#e83e8c', '#6c757d', '#fd7e14'
];

// Generate a distinct color using HSL color space
// This creates unlimited unique colors with good visual distinction
export const generateColorFromIndex = (index: number, _total?: number): string => {
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

// Helper function to create a consistent color mapping based on all unique labels
export const createGlobalColorMap = (allLabels: string[]): Map<string, string> => {
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
export const getColorForLabel = (label: string, colorMap: Map<string, string> | null, defaultColor: string): string => {
  if (colorMap && colorMap.has(label)) {
    return colorMap.get(label)!;
  }
  // If no color map (no "color by" selected), use the default color for all series
  return defaultColor;
};

// Helper function to create consistent median/mean annotations for histogram charts
export const createMedianMeanAnnotation = (
  median: number | undefined,
  average: number | undefined,
  color: string,
  decimalPlaces: number = 0,
  unit: string = ''
): any[] => {
  if (median === undefined || average === undefined) {
    return [];
  }

  return [{
    x: 0.5,
    y: 1.05,
    xref: 'paper',
    yref: 'paper',
    text: `Median: ${median.toFixed(decimalPlaces)}${unit} | Mean: ${average.toFixed(decimalPlaces)}${unit}`,
    showarrow: false,
    font: {
      size: 12,
      color: color,
    },
    bgcolor: 'rgba(255,255,255,0.9)',
    bordercolor: color,
    borderwidth: 1,
    borderpad: 4,
  }];
};

// Simplified: Generate Plotly traces from chart data
// Handles both single-series (y array) and multi-series (series array) automatically
export const generateChartTraces = (
  chartData: ChartData,
  chartType: 'area' | 'bar',
  defaultColor: string,
  colorMap: Map<string, string> | null,
  defaultName: string = ''
): any[] => {
  if (!chartData || !chartData.x || chartData.x.length === 0) {
    return [];
  }

  // Multi-series data (grouped by color_by)
  if (chartData.series && chartData.series.length > 0) {
    // If no color map (color by "None"), aggregate all series into one
    if (!colorMap) {
      console.log('generateChartTraces: No colorMap, aggregating', chartData.series.length, 'series');
      // Sum up all series data for each x value
      const aggregatedData = chartData.x.map((_, index) =>
        chartData.series!.reduce((sum, series) => sum + (series.data[index] || 0), 0)
      );

      if (chartType === 'area') {
        console.log('generateChartTraces: Returning single area trace with color', defaultColor);
        return [{
          x: chartData.x,
          y: aggregatedData,
          type: 'scatter',
          mode: 'lines',
          fill: 'tozeroy',
          marker: { color: defaultColor },
          line: { color: defaultColor },
          showlegend: false,
          hovertemplate: 'Period: %{x}<br>Value: %{y:,.0f}<extra></extra>',
        }];
      } else {
        console.log('generateChartTraces: Returning single bar trace with color', defaultColor);
        return [{
          x: chartData.x,
          y: aggregatedData,
          type: 'bar',
          marker: { color: defaultColor },
          showlegend: false,
          hovertemplate: '%{x}<br>Value: %{y:,.0f}<extra></extra>',
        }];
      }
    }

    // With color map, show all series with their respective colors
    if (chartType === 'area') {
      // Stacked area chart
      return chartData.series.map((series, index) => {
        const color = getColorForLabel(String(series.name), colorMap, defaultColor);
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
        marker: { color: getColorForLabel(String(series.name), colorMap, defaultColor) },
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
      // If no colorMap, use the default color for all bars (consistent single color)
      let colors: string | string[];

      if (colorMap) {
        // Color each bar based on category from colorMap or generated color
        colors = chartData.x.map((category, idx) => {
          const categoryStr = String(category);
          if (colorMap.has(categoryStr)) {
            return colorMap.get(categoryStr)!;
          }
          return generateColorFromIndex(idx, chartData.x.length);
        });
      } else {
        // No colorMap: use single default color for all bars
        colors = defaultColor;
      }

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
export const getCommonLayout = (xTitle: string, yTitle: string, showLegend: boolean = false) => ({
  autosize: true,
  margin: { l: 80, r: showLegend ? 220 : 20, t: 20, b: 60 },
  xaxis: {
    title: {
      text: xTitle,
      font: { size: 14 },
      standoff: 10,
    },
    showgrid: true,
    gridcolor: 'rgba(128, 128, 128, 0.1)',
    zeroline: false,
  },
  yaxis: {
    title: {
      text: yTitle,
      font: { size: 14 },
      standoff: 10,
    },
    showgrid: true,
    gridcolor: 'rgba(128, 128, 128, 0.1)',
    zeroline: false,
    tickformat: ',',  // Thousands separator
  },
  hovermode: 'x unified',
  hoverlabel: {
    bgcolor: 'white',
    bordercolor: '#ddd',
    font: { color: 'black', size: 12 },
  },
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
export const getCommonConfig = () => ({
  responsive: true,
  displayModeBar: 'hover',  // Show toolbar only on hover
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
