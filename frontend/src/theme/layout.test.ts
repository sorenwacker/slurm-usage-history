import { readFileSync } from 'node:fs';
import { join } from 'node:path';
import { describe, expect, it } from 'vitest';

const css = readFileSync(join(__dirname, '..', 'App.css'), 'utf8').replace(/\/\*[\s\S]*?\*\//g, '');

/** Returns the declaration blocks of every rule whose selector list contains `selector`. */
function blocksFor(selector: string): string[] {
  return [...css.matchAll(/([^{}]+)\{([^{}]*)\}/g)]
    .filter(([, selectors]) => selectors.split(',').some((s) => s.trim() === selector))
    .map(([, , block]) => block);
}

describe('dashboard layout', () => {
  it('lets the main content fill the row instead of capping it by the sidebar width', () => {
    const blocks = blocksFor('.main-content');
    expect(blocks.length).toBeGreaterThan(0);
    expect(blocks.filter((b) => b.includes('--sidebar-width'))).toEqual([]);
  });

  it('lets the main content shrink below its charts so a wide chart cannot push it past the viewport', () => {
    expect(blocksFor('.main-content').some((b) => /min-width:\s*0\b/.test(b))).toBe(true);
  });
});

describe('efficiency charts', () => {
  it('span the full content width at every container width', () => {
    const multiColumn = blocksFor('.efficiency-row').filter((b) => /grid-template-columns:\s*(1fr\s+1fr|repeat\()/.test(b));
    expect(multiColumn).toEqual([]);
  });
});

describe('jobs section', () => {
  const section = readFileSync(join(__dirname, '..', 'components', 'charts', 'sections', 'UsersJobsSection.tsx'), 'utf8');

  it('gives Nodes per Job its own full-width row below the jobs charts', () => {
    const rowsBeforeNodes = [...section.slice(0, section.indexOf('data.nodes_per_job')).matchAll(/className="(chart-row[^"]*)"/g)]
      .map((m) => m[1]);
    expect(rowsBeforeNodes.at(-1)).toBe('chart-row full-width');
    expect(section.includes('chart-row-3col')).toBe(false);
  });
});
