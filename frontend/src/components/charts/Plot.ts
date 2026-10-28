// Partial plotly bundle: only the trace types the dashboard renders.
// The full plotly.js is ~3.5 MB minified; core + four traces is a fraction of that.
import { createElement } from 'react';
import type { PlotProps } from 'react-plotly.js';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js/lib/core';
import bar from 'plotly.js/lib/bar';
import scatter from 'plotly.js/lib/scatter';
import pie from 'plotly.js/lib/pie';
import indicator from 'plotly.js/lib/indicator';
import { withLocalOnlyConfig } from './plotConfig';

Plotly.register([bar, scatter, pie, indicator]);

const PlotlyPlot = createPlotlyComponent(Plotly);

const Plot = (props: PlotProps) => createElement(PlotlyPlot, { ...props, config: withLocalOnlyConfig(props.config) });

export default Plot;
