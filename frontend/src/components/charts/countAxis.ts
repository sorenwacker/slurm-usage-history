/** Bar width and tick spacing for a histogram over integer counts (nodes, CPUs or GPUs per job).
 *
 * Plotly sizes bars to the smallest gap between x values, so a chart with only the values 1 and 3
 * draws bars two units wide. Integer counts get a fixed width and ticks on every integer instead.
 */
export function countAxisBars(x: (string | number)[]): { width: number; dtick: number } | null {
  if (x.length === 0 || !x.every((v) => typeof v === 'number' && Number.isInteger(v))) return null;
  return { width: 0.8, dtick: 1 };
}
