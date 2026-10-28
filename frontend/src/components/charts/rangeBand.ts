/** Polygon for a shaded band between a lower and an upper bound, drawn with Plotly `fill: 'toself'`.
 *
 * Plotly's `tonexty` fill joins line segments straight across null values, so a band around a line
 * with gaps is filled through the gaps. A `toself` fill closes each null-separated segment on its
 * own, so the band is built as one polygon per contiguous run of periods that have both bounds:
 * the upper bound forward, the lower bound back, and a null between runs.
 */
export function rangeBandPolygon(
  x: (string | number)[],
  lower: (number | null)[],
  upper: (number | null)[],
): { x: (string | number | null)[]; y: (number | null)[] } {
  const polygonX: (string | number | null)[] = [];
  const polygonY: (number | null)[] = [];
  let runStart = 0;

  const closeRun = (end: number) => {
    if (end > runStart) {
      if (polygonX.length > 0) {
        polygonX.push(null);
        polygonY.push(null);
      }
      for (let i = runStart; i < end; i++) {
        polygonX.push(x[i]);
        polygonY.push(upper[i]);
      }
      for (let i = end - 1; i >= runStart; i--) {
        polygonX.push(x[i]);
        polygonY.push(lower[i]);
      }
    }
    runStart = end + 1;
  };

  x.forEach((_, i) => {
    if (lower[i] == null || upper[i] == null) closeRun(i);
  });
  closeRun(x.length);
  return { x: polygonX, y: polygonY };
}

/** Plotly trace of the P25-P75 band of a trend chart.
 *
 * The band has an outline in the fill colour, so a run of one period, whose polygon has no area,
 * is drawn as a vertical bar from P25 to P75. Missing percentiles give an empty band.
 */
export function rangeBandTrace(
  x: (string | number)[],
  stats: { p25?: (number | null)[]; p75?: (number | null)[] },
  color: string,
) {
  const band = rangeBandPolygon(x, stats.p25 ?? [], stats.p75 ?? []);
  return {
    x: band.x,
    y: band.y,
    type: 'scatter',
    mode: 'lines',
    fill: 'toself',
    fillcolor: `${color}30`, // Hex alpha for transparency
    line: { width: 4, color: `${color}30` },
    name: 'P25-P75 Range',
    showlegend: true,
    hoverinfo: 'skip',
  };
}
