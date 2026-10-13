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
  let run: number[] = [];

  const closeRun = () => {
    if (run.length === 0) return;
    if (polygonX.length > 0) {
      polygonX.push(null);
      polygonY.push(null);
    }
    for (const i of run) {
      polygonX.push(x[i]);
      polygonY.push(upper[i]);
    }
    for (const i of [...run].reverse()) {
      polygonX.push(x[i]);
      polygonY.push(lower[i]);
    }
    run = [];
  };

  x.forEach((_, i) => {
    if (lower[i] == null || upper[i] == null) closeRun();
    else run.push(i);
  });
  closeRun();
  return { x: polygonX, y: polygonY };
}
