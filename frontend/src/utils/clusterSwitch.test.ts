import { describe, expect, it } from 'vitest';
import { carryDatesToCluster, carrySelectionToCluster } from './clusterSwitch';

describe('carrySelectionToCluster', () => {
  it('keeps the selected values the new cluster has and drops the others', () => {
    expect(carrySelectionToCluster(['gpu', 'cpu', 'bigmem'], ['cpu', 'gpu', 'general'])).toEqual(['gpu', 'cpu']);
  });

  it('keeps everything when the new cluster\'s values are not known yet', () => {
    expect(carrySelectionToCluster(['gpu'], undefined)).toEqual(['gpu']);
  });

  it('returns an empty selection unchanged', () => {
    expect(carrySelectionToCluster([], ['cpu'])).toEqual([]);
  });
});

describe('carryDatesToCluster', () => {
  const range = { min_date: '2026-08-20', max_date: '2026-10-11' };

  it('keeps dates that lie inside the new cluster\'s data range', () => {
    expect(carryDatesToCluster('2026-09-01', '2026-09-30', range)).toEqual({ start: '2026-09-01', end: '2026-09-30' });
  });

  it('moves dates outside the new cluster\'s data range to its bounds', () => {
    expect(carryDatesToCluster('2026-01-01', '2026-12-31', range)).toEqual({ start: '2026-08-20', end: '2026-10-11' });
  });

  it('falls back to the default window when no dates were chosen yet', () => {
    expect(carryDatesToCluster('', '', range)).toEqual({ start: '2026-08-30', end: '2026-10-11' });
  });

  it('keeps the dates when the new cluster has no data range', () => {
    expect(carryDatesToCluster('2026-09-01', '2026-09-30', undefined)).toEqual({ start: '2026-09-01', end: '2026-09-30' });
  });
});
