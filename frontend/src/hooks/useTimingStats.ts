import { useMemo } from 'react';
import type { AggregatedChartsResponse } from '../types';

export interface TimingStats {
  waitMedian: number | null;
  waitP95: number | null;
  waitMax: number | null;
  durationMedian: number | null;
  durationP95: number | null;
  durationMax: number | null;
}

export function useTimingStats(data: AggregatedChartsResponse | undefined): TimingStats | null {
  return useMemo(() => {
    if (!data) return null;

    const calcAverage = (arr: number[] | undefined): number | null => {
      if (!arr || arr.length === 0) return null;
      const valid = arr.filter(v => v != null && !isNaN(v));
      if (valid.length === 0) return null;
      return valid.reduce((a, b) => a + b, 0) / valid.length;
    };

    const calcMax = (arr: number[] | undefined): number | null => {
      if (!arr || arr.length === 0) return null;
      const valid = arr.filter(v => v != null && !isNaN(v));
      if (valid.length === 0) return null;
      return Math.max(...valid);
    };

    const waitStats = data.waiting_times_trends?.stats;
    const durationStats = data.job_duration_trends?.stats;

    return {
      waitMedian: calcAverage(waitStats?.median),
      waitP95: calcAverage(waitStats?.p95),
      waitMax: calcMax(waitStats?.max),
      durationMedian: calcAverage(durationStats?.median),
      durationP95: calcAverage(durationStats?.p95),
      durationMax: calcMax(durationStats?.max),
    };
  }, [data]);
}

export function formatHours(hours: number | null): string {
  if (hours === null) return '-';
  if (hours < 1) return `${Math.round(hours * 60)}m`;
  if (hours < 24) return `${hours.toFixed(1)}h`;
  return `${(hours / 24).toFixed(1)}d`;
}
