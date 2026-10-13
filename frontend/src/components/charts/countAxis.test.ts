import { describe, expect, it } from 'vitest';
import { countAxisBars } from './countAxis';

describe('countAxisBars', () => {
  it('fixes the bar width and integer ticks for integer counts, however sparse', () => {
    expect(countAxisBars([1, 3])).toEqual({ width: 0.8, dtick: 1 });
    expect(countAxisBars([1, 2, 4, 8, 16])).toEqual({ width: 0.8, dtick: 1 });
  });

  it('leaves binned labels and non-integer values to the default layout', () => {
    expect(countAxisBars(['1-10', '11-20'])).toBeNull();
    expect(countAxisBars([0.5, 1.5])).toBeNull();
    expect(countAxisBars([])).toBeNull();
  });
});
