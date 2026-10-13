import { clampDate, defaultDateRange, type DateRange } from './dateRange';

/** Selected values the new cluster also has; all of them while its values are not known yet. */
export function carrySelectionToCluster(selected: string[], available: string[] | undefined): string[] {
  if (!available) return selected;
  const known = new Set(available);
  return selected.filter((value) => known.has(value));
}

/** The chosen dates moved inside the new cluster's data range; the default window when none were chosen. */
export function carryDatesToCluster(
  start: string,
  end: string,
  range: DateRange | null | undefined,
): { start: string; end: string } {
  if (!start && !end) return defaultDateRange(range) ?? { start, end };
  return { start: clampDate(start, range), end: clampDate(end, range) };
}
