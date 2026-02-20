import { useState, useEffect } from 'react';

export interface ChartColors {
  gridColor: string;
  textColor: string;
  bgColor: string;
  hoverBgColor: string;
  hoverBorderColor: string;
  hoverTextColor: string;
  legendBgColor: string;
  legendBorderColor: string;
}

const lightColors: ChartColors = {
  gridColor: 'rgba(128, 128, 128, 0.1)',
  textColor: '#333',
  bgColor: 'rgba(0, 0, 0, 0)',
  hoverBgColor: 'white',
  hoverBorderColor: '#ddd',
  hoverTextColor: 'black',
  legendBgColor: 'rgba(255, 255, 255, 0.9)',
  legendBorderColor: '#ddd',
};

const darkColors: ChartColors = {
  gridColor: 'rgba(148, 163, 184, 0.15)',
  textColor: '#e2e8f0',
  bgColor: 'rgba(0, 0, 0, 0)',
  hoverBgColor: '#1e293b',
  hoverBorderColor: '#475569',
  hoverTextColor: '#f1f5f9',
  legendBgColor: 'rgba(30, 41, 59, 0.95)',
  legendBorderColor: '#475569',
};

export const useDarkMode = (): { isDark: boolean; chartColors: ChartColors } => {
  const [isDark, setIsDark] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = (e: MediaQueryListEvent) => {
      setIsDark(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return {
    isDark,
    chartColors: isDark ? darkColors : lightColors,
  };
};

export default useDarkMode;
