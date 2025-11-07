// Export all chart components and helpers for easy importing
export { default as TimelineChart } from './TimelineChart';
export { default as PieChart } from './PieChart';
export { default as HistogramChart } from './HistogramChart';
export { default as StackedAreaChart } from './StackedAreaChart';

export {
  COLORS,
  generateColorFromIndex,
  createGlobalColorMap,
  getColorForLabel,
  createMedianMeanAnnotation,
  generateChartTraces,
  getCommonLayout,
  getCommonConfig,
} from './chartHelpers';
