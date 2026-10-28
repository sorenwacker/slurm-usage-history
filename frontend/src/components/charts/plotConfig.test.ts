import { describe, expect, it } from 'vitest';
import { withLocalOnlyConfig } from './plotConfig';

describe('withLocalOnlyConfig', () => {
  it('removes the modebar button that sends chart data to plotly cloud', () => {
    expect(withLocalOnlyConfig({ responsive: true })).toEqual({ responsive: true, showSendToCloud: false });
  });

  it('keeps the button off even when a chart asks for it', () => {
    expect(withLocalOnlyConfig({ showSendToCloud: true }).showSendToCloud).toBe(false);
  });

  it('applies to charts that pass no config', () => {
    expect(withLocalOnlyConfig(undefined)).toEqual({ showSendToCloud: false });
  });
});
