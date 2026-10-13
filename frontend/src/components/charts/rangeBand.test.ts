import { describe, expect, it } from 'vitest';
import { rangeBandPolygon } from './rangeBand';

describe('rangeBandPolygon', () => {
  it('traces the upper bound forward and the lower bound back for a contiguous band', () => {
    expect(rangeBandPolygon(['d1', 'd2', 'd3'], [1, 2, 3], [4, 5, 6])).toEqual({
      x: ['d1', 'd2', 'd3', 'd3', 'd2', 'd1'],
      y: [4, 5, 6, 3, 2, 1],
    });
  });

  it('closes one polygon per contiguous run and separates runs with a null, never bridging a gap', () => {
    const band = rangeBandPolygon(
      ['d1', 'd2', 'd3', 'd4', 'd5'],
      [1, 2, null, null, 5],
      [10, 20, null, null, 400],
    );
    expect(band).toEqual({
      x: ['d1', 'd2', 'd2', 'd1', null, 'd5', 'd5'],
      y: [10, 20, 2, 1, null, 400, 5],
    });
  });

  it('treats a period with only one bound as a gap', () => {
    expect(rangeBandPolygon(['d1', 'd2'], [1, null], [4, 5])).toEqual({ x: ['d1', 'd1'], y: [4, 1] });
  });

  it('returns an empty polygon when no period has both bounds', () => {
    expect(rangeBandPolygon(['d1'], [null], [null])).toEqual({ x: [], y: [] });
  });
});
