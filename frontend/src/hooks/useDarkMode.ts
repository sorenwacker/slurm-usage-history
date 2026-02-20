import { useState, useEffect, useCallback } from 'react';

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

type ThemeMode = 'light' | 'dark' | 'system';

const STORAGE_KEY = 'slurm-dashboard-theme';

const getSystemPreference = (): boolean => {
  if (typeof window !== 'undefined') {
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  }
  return false;
};

const getStoredTheme = (): ThemeMode => {
  if (typeof window !== 'undefined') {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark' || stored === 'system') {
      return stored;
    }
  }
  return 'system';
};

export const useDarkMode = (): {
  isDark: boolean;
  mode: ThemeMode;
  setMode: (mode: ThemeMode) => void;
  toggle: () => void;
  chartColors: ChartColors;
} => {
  const [mode, setModeState] = useState<ThemeMode>(getStoredTheme);
  const [systemDark, setSystemDark] = useState(getSystemPreference);

  // Calculate actual dark state based on mode
  const isDark = mode === 'system' ? systemDark : mode === 'dark';

  // Apply theme class to document
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [isDark]);

  // Listen for system preference changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = (e: MediaQueryListEvent) => {
      setSystemDark(e.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  const setMode = useCallback((newMode: ThemeMode) => {
    setModeState(newMode);
    localStorage.setItem(STORAGE_KEY, newMode);
  }, []);

  const toggle = useCallback(() => {
    // Cycle through: system -> light -> dark -> system
    const nextMode: ThemeMode = mode === 'system' ? 'light' : mode === 'light' ? 'dark' : 'system';
    setMode(nextMode);
  }, [mode, setMode]);

  return {
    isDark,
    mode,
    setMode,
    toggle,
    chartColors: isDark ? darkColors : lightColors,
  };
};

export default useDarkMode;
