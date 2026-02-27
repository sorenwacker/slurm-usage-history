import { useState, useEffect, useMemo } from 'react';
import type { MetadataResponse } from '../types';

export interface ReportFiltersState {
  reportHostname: string;
  reportType: 'monthly' | 'quarterly' | 'annual';
  selectedYear: number;
  selectedMonth: number;
  selectedQuarter: number;
  downloadFormat: 'pdf' | 'csv' | 'json';
}

export interface ReportFiltersActions {
  setReportHostname: (value: string) => void;
  setReportType: (value: 'monthly' | 'quarterly' | 'annual') => void;
  setSelectedYear: (value: number) => void;
  setSelectedMonth: (value: number) => void;
  setSelectedQuarter: (value: number) => void;
  setDownloadFormat: (value: 'pdf' | 'csv' | 'json') => void;
}

export interface UseReportFiltersResult {
  state: ReportFiltersState;
  actions: ReportFiltersActions;
  availableYears: number[];
  reportDateRange: { min_date?: string; max_date?: string } | null;
}

export function useReportFilters(
  metadata: MetadataResponse | undefined,
  activeTab: 'overview' | 'reports',
  selectedHostname: string
): UseReportFiltersResult {
  const [reportHostname, setReportHostname] = useState<string>('');
  const [reportType, setReportType] = useState<'monthly' | 'quarterly' | 'annual'>('monthly');
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState<number>(new Date().getMonth() + 1);
  const [selectedQuarter, setSelectedQuarter] = useState<number>(Math.ceil((new Date().getMonth() + 1) / 3));
  const [downloadFormat, setDownloadFormat] = useState<'pdf' | 'csv' | 'json'>('pdf');

  const reportDateRange = metadata && reportHostname ? metadata.date_ranges[reportHostname] : null;

  const defaultReportYearMonth = useMemo(() => {
    if (reportDateRange?.max_date) {
      const maxDate = new Date(reportDateRange.max_date);
      return {
        year: maxDate.getFullYear(),
        month: maxDate.getMonth() + 1,
      };
    }
    return {
      year: new Date().getFullYear(),
      month: new Date().getMonth() + 1,
    };
  }, [reportDateRange?.max_date]);

  const reportMinYear = reportDateRange?.min_date ? new Date(reportDateRange.min_date).getFullYear() : 2020;
  const reportMaxYear = reportDateRange?.max_date ? new Date(reportDateRange.max_date).getFullYear() : new Date().getFullYear();
  const availableYears = Array.from({ length: reportMaxYear - reportMinYear + 1 }, (_, i) => reportMinYear + i);

  // Initialize report hostname from dashboard hostname when reports tab is opened
  useEffect(() => {
    if (activeTab === 'reports' && selectedHostname && !reportHostname) {
      setReportHostname(selectedHostname);
    }
  }, [activeTab, selectedHostname, reportHostname]);

  // Update year/month when report hostname changes
  useEffect(() => {
    setSelectedYear(defaultReportYearMonth.year);
    setSelectedMonth(defaultReportYearMonth.month);
    setSelectedQuarter(Math.ceil(defaultReportYearMonth.month / 3));
  }, [defaultReportYearMonth.year, defaultReportYearMonth.month]);

  return {
    state: {
      reportHostname,
      reportType,
      selectedYear,
      selectedMonth,
      selectedQuarter,
      downloadFormat,
    },
    actions: {
      setReportHostname,
      setReportType,
      setSelectedYear,
      setSelectedMonth,
      setSelectedQuarter,
      setDownloadFormat,
    },
    availableYears,
    reportDateRange,
  };
}
