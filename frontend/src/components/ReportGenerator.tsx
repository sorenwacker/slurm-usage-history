import React, { useState, useEffect, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { reportsApi } from '../api/client';
import type { MetadataResponse } from '../types';
import ReportSummaryCards from './reports/ReportSummaryCards';
import ReportTimelines from './reports/ReportTimelines';
import ReportDistributions from './reports/ReportDistributions';
import ReportBreakdowns from './reports/ReportBreakdowns';

interface ReportGeneratorProps {
  metadata: MetadataResponse | undefined;
  selectedHostname: string;
  isSidebar?: boolean;
}

interface ReportData {
  report_type: string;
  hostname: string;
  period: {
    start_date: string;
    end_date: string;
  };
  summary: {
    total_jobs: number;
    total_cpu_hours: number;
    total_gpu_hours: number;
    total_users: number;
    avg_job_duration_hours?: number;
    median_job_duration_hours?: number;
    avg_waiting_time_hours?: number;
    median_waiting_time_hours?: number;
    completed_jobs?: number;
    failed_jobs?: number;
    success_rate?: number;
  };
  comparison?: {
    previous_period_start: string;
    previous_period_end: string;
    jobs_change_percent: number;
    cpu_hours_change_percent: number;
    gpu_hours_change_percent: number;
    users_change_percent: number;
    previous_timeline: Array<{
      date: string;
      jobs: number;
      cpu_hours: number;
      gpu_hours: number;
      users: number;
    }>;
  } | null;
  job_duration_stats?: {
    mean: number;
    median: number;
    p25: number;
    p75: number;
    p90: number;
    min: number;
    max: number;
  };
  waiting_time_stats?: {
    mean: number;
    median: number;
    p25: number;
    p75: number;
    p90: number;
    min: number;
    max: number;
  };
  by_account: Array<{
    account: string;
    jobs: number;
    cpu_hours: number;
    gpu_hours: number;
    users: number;
  }>;
  // by_user is intentionally empty to protect user privacy
  // Only aggregate metrics (total_users count) are provided
  by_user: Array<{
    user: string;
    jobs: number;
    cpu_hours: number;
    gpu_hours: number;
  }>;
  by_partition: Array<{
    partition: string;
    jobs: number;
    cpu_hours: number;
    gpu_hours: number;
    users: number;
  }>;
  by_state: Array<{
    state: string;
    jobs: number;
  }>;
  timeline: Array<{
    date: string;
    jobs: number;
    cpu_hours: number;
    gpu_hours: number;
    users: number;
  }>;
  generated_at: string;
}

type ReportType = 'monthly' | 'quarterly' | 'annual';
type ReportFormat = 'pdf' | 'csv' | 'json';

const ReportGenerator: React.FC<ReportGeneratorProps> = ({ metadata, selectedHostname: parentHostname }) => {
  // Manage hostname internally for reports
  const [reportHostname, setReportHostname] = useState<string>(parentHostname || '');

  // Initialize report hostname from parent when available
  useEffect(() => {
    if (parentHostname && !reportHostname) {
      setReportHostname(parentHostname);
    }
  }, [parentHostname, reportHostname]);

  // Get available periods for the selected hostname
  const dateRange = metadata && reportHostname ? metadata.date_ranges[reportHostname] : null;

  // Calculate default year/month from most recent data
  const defaultYearMonth = useMemo(() => {
    if (dateRange?.max_date) {
      const maxDate = new Date(dateRange.max_date);
      return {
        year: maxDate.getFullYear(),
        month: maxDate.getMonth() + 1, // JavaScript months are 0-indexed
      };
    }
    return {
      year: new Date().getFullYear(),
      month: new Date().getMonth() + 1,
    };
  }, [dateRange?.max_date]);

  const [reportType, setReportType] = useState<ReportType>('monthly');
  const [selectedYear, setSelectedYear] = useState<number>(defaultYearMonth.year);
  const [selectedMonth, setSelectedMonth] = useState<number>(defaultYearMonth.month);
  const [selectedQuarter, setSelectedQuarter] = useState<number>(Math.ceil(defaultYearMonth.month / 3));
  const [downloadFormat, setDownloadFormat] = useState<ReportFormat>('pdf');

  // Update year/month when hostname changes
  useEffect(() => {
    setSelectedYear(defaultYearMonth.year);
    setSelectedMonth(defaultYearMonth.month);
  }, [defaultYearMonth.year, defaultYearMonth.month]);

  const minYear = dateRange?.min_date ? new Date(dateRange.min_date).getFullYear() : 2020;
  const maxYear = dateRange?.max_date ? new Date(dateRange.max_date).getFullYear() : new Date().getFullYear();
  const availableYears = Array.from({ length: maxYear - minYear + 1 }, (_, i) => minYear + i);

  const months = [
    { value: 1, label: 'January' },
    { value: 2, label: 'February' },
    { value: 3, label: 'March' },
    { value: 4, label: 'April' },
    { value: 5, label: 'May' },
    { value: 6, label: 'June' },
    { value: 7, label: 'July' },
    { value: 8, label: 'August' },
    { value: 9, label: 'September' },
    { value: 10, label: 'October' },
    { value: 11, label: 'November' },
    { value: 12, label: 'December' },
  ];

  // Determine if a period is complete based on current date
  const isCompletePeriod = useMemo(() => {
    const now = new Date();
    const currentYear = now.getFullYear();
    const currentMonth = now.getMonth() + 1; // 1-indexed
    const currentQuarter = Math.ceil(currentMonth / 3);

    return {
      isMonthComplete: (year: number, month: number) => {
        if (year < currentYear) return true;
        if (year > currentYear) return false;
        return month < currentMonth; // Only previous months are complete
      },
      isQuarterComplete: (year: number, quarter: number) => {
        if (year < currentYear) return true;
        if (year > currentYear) return false;
        return quarter < currentQuarter; // Only previous quarters are complete
      },
      isYearComplete: (year: number) => {
        return year < currentYear; // Only previous years are complete
      },
    };
  }, []);

  // Fetch report preview
  const {
    data: reportData,
    isLoading,
    error,
  } = useQuery<ReportData>({
    queryKey: ['reportPreview', reportHostname, reportType, selectedYear, selectedMonth, selectedQuarter],
    queryFn: () => reportsApi.previewReport(
      reportHostname,
      reportType,
      selectedYear,
      reportType === 'monthly' ? selectedMonth : undefined,
      reportType === 'quarterly' ? selectedQuarter : undefined
    ),
    enabled: !!reportHostname,
  });

  const handleDownload = () => {
    reportsApi.downloadReport(
      reportHostname,
      reportType,
      selectedYear,
      reportType === 'monthly' ? selectedMonth : undefined,
      reportType === 'quarterly' ? selectedQuarter : undefined,
      downloadFormat
    );
  };

  return (
    <>
      {/* Report Generator Card - All Controls */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginBottom: '1.5rem' }}>Report Generator</h3>

        {/* Cluster Selector */}
        <div style={{ marginBottom: '1.5rem' }}>
          <label htmlFor="report-cluster" style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
            Select Cluster
          </label>
          <select
            id="report-cluster"
            value={reportHostname}
            onChange={(e) => setReportHostname(e.target.value)}
            style={{
              padding: '0.5rem',
              borderRadius: '4px',
              border: '1px solid var(--border-color)',
              fontSize: '1rem',
              width: '100%',
              maxWidth: '300px',
              background: 'var(--bg-color)',
              color: 'var(--text-color)',
            }}
          >
            <option value="">Select cluster...</option>
            {metadata?.hostnames.map((hostname) => (
              <option key={hostname} value={hostname}>
                {hostname}
              </option>
            ))}
          </select>
        </div>

        {/* Report Configuration - only shown when cluster is selected */}
        {reportHostname && (
          <>
            <hr style={{ margin: '1.5rem 0', border: 'none', borderTop: '1px solid var(--border-color)' }} />

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
              {/* Report Type */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: 'var(--text-color)' }}>
                  Report Type
                </label>
                <select
                  value={reportType}
                  onChange={(e) => setReportType(e.target.value as ReportType)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-color)',
                    color: 'var(--text-color)',
                  }}
                >
                  <option value="monthly">Monthly Report</option>
                  <option value="quarterly">Quarterly Report</option>
                  <option value="annual">Annual Report</option>
                </select>
              </div>

              {/* Year */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: 'var(--text-color)' }}>
                  Year
                </label>
                <select
                  value={selectedYear}
                  onChange={(e) => setSelectedYear(parseInt(e.target.value))}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-color)',
                    color: 'var(--text-color)',
                  }}
                >
                  {availableYears.map((year) => {
                    const disabled = reportType === 'annual' && !isCompletePeriod.isYearComplete(year);
                    return (
                      <option key={year} value={year} disabled={disabled}>
                        {year}{disabled ? ' (incomplete)' : ''}
                      </option>
                    );
                  })}
                </select>
              </div>

              {/* Month (only for monthly reports) */}
              {reportType === 'monthly' && (
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: 'var(--text-color)' }}>
                    Month
                  </label>
                  <select
                    value={selectedMonth}
                    onChange={(e) => setSelectedMonth(parseInt(e.target.value))}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      borderRadius: '4px',
                      border: '1px solid var(--border-color)',
                      background: 'var(--bg-color)',
                      color: 'var(--text-color)',
                    }}
                  >
                    {months.map((month) => {
                      const disabled = !isCompletePeriod.isMonthComplete(selectedYear, month.value);
                      return (
                        <option key={month.value} value={month.value} disabled={disabled}>
                          {month.label}{disabled ? ' (incomplete)' : ''}
                        </option>
                      );
                    })}
                  </select>
                </div>
              )}

              {/* Quarter (only for quarterly reports) */}
              {reportType === 'quarterly' && (
                <div>
                  <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: 'var(--text-color)' }}>
                    Quarter
                  </label>
                  <select
                    value={selectedQuarter}
                    onChange={(e) => setSelectedQuarter(parseInt(e.target.value))}
                    style={{
                      width: '100%',
                      padding: '0.5rem',
                      borderRadius: '4px',
                      border: '1px solid var(--border-color)',
                      background: 'var(--bg-color)',
                      color: 'var(--text-color)',
                    }}
                  >
                    <option value={1} disabled={!isCompletePeriod.isQuarterComplete(selectedYear, 1)}>
                      Q1 (Jan - Mar){!isCompletePeriod.isQuarterComplete(selectedYear, 1) ? ' (incomplete)' : ''}
                    </option>
                    <option value={2} disabled={!isCompletePeriod.isQuarterComplete(selectedYear, 2)}>
                      Q2 (Apr - Jun){!isCompletePeriod.isQuarterComplete(selectedYear, 2) ? ' (incomplete)' : ''}
                    </option>
                    <option value={3} disabled={!isCompletePeriod.isQuarterComplete(selectedYear, 3)}>
                      Q3 (Jul - Sep){!isCompletePeriod.isQuarterComplete(selectedYear, 3) ? ' (incomplete)' : ''}
                    </option>
                    <option value={4} disabled={!isCompletePeriod.isQuarterComplete(selectedYear, 4)}>
                      Q4 (Oct - Dec){!isCompletePeriod.isQuarterComplete(selectedYear, 4) ? ' (incomplete)' : ''}
                    </option>
                  </select>
                </div>
              )}

              {/* Download Format */}
              <div>
                <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500', color: 'var(--text-color)' }}>
                  Download Format
                </label>
                <select
                  value={downloadFormat}
                  onChange={(e) => setDownloadFormat(e.target.value as ReportFormat)}
                  style={{
                    width: '100%',
                    padding: '0.5rem',
                    borderRadius: '4px',
                    border: '1px solid var(--border-color)',
                    background: 'var(--bg-color)',
                    color: 'var(--text-color)',
                  }}
                >
                  <option value="json">JSON</option>
                  <option value="csv">CSV</option>
                  <option value="pdf">PDF</option>
                </select>
              </div>
            </div>

            {/* Download Button */}
            <button
              onClick={handleDownload}
              className="no-print"
              style={{
                padding: '0.75rem 1.5rem',
                background: '#04A5D5',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontWeight: '600',
                fontSize: '1rem',
              }}
            >
              Download Report
            </button>
          </>
        )}

        {!reportHostname && (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem', margin: '1rem 0 0 0' }}>
            Please select a cluster to generate reports
          </p>
        )}
      </div>

      {/* Report Content - only shown when hostname is selected */}
      {reportHostname && (
        <>
      {/* Print-friendly A4 CSS */}
      <style>{`
        @media print {
          @page {
            size: A4;
            margin: 20mm;
          }
          body {
            print-color-adjust: exact;
            -webkit-print-color-adjust: exact;
          }
          .no-print {
            display: none !important;
          }
          .page-break {
            page-break-before: always;
            break-before: page;
          }
          .page-break-avoid {
            page-break-inside: avoid;
            break-inside: avoid;
          }
        }
      `}</style>

      {/* Report Preview */}
      {isLoading && (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          <div className="loading-spinner"></div>
          <p>Loading report preview...</p>
        </div>
      )}

      {error && (
        <div style={{
          background: '#fee',
          border: '1px solid #fcc',
          padding: '1rem',
          borderRadius: '4px',
          color: '#c00',
        }}>
          Error loading report: {error instanceof Error ? error.message : 'Unknown error'}
        </div>
      )}

      {reportData && (
        <div style={{
          maxWidth: '210mm',
          margin: '0 auto',
          background: 'white',
          padding: '20mm',
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: '4px',
        }}>
          {/* Report Header */}
          <div style={{
            background: 'var(--card-bg)',
            padding: '1.5rem',
            borderRadius: '8px',
            marginBottom: '1.5rem',
            border: '1px solid var(--border-color)',
          }}>
            <h2 style={{ marginTop: 0, marginBottom: '0.5rem', color: '#000000' }}>
              {reportData.report_type}
            </h2>
            <p style={{ margin: 0, color: '#000000' }}>
              Cluster: <strong>{reportData.hostname}</strong> |
              Period: <strong>{reportData.period.start_date}</strong> to <strong>{reportData.period.end_date}</strong>
            </p>
          </div>

          {/* Summary Statistics Cards */}
          <ReportSummaryCards reportData={reportData} reportType={reportType} />

          {/* Timeline Charts */}
          <ReportTimelines
            timeline={reportData.timeline}
            previousTimeline={reportData.comparison?.previous_timeline}
            totalGpuHours={reportData.summary.total_gpu_hours}
            reportType={reportType}
          />

          {/* Breakdowns Section */}
          <ReportBreakdowns
            byAccount={reportData.by_account}
            byPartition={reportData.by_partition}
            byState={reportData.by_state}
            totalJobs={reportData.summary.total_jobs}
            totalGpuHours={reportData.summary.total_gpu_hours}
          />

          {/* Distribution Statistics */}
          <ReportDistributions
            jobDurationStats={reportData.job_duration_stats}
            waitingTimeStats={reportData.waiting_time_stats}
            timeline={reportData.timeline}
            totalGpuHours={reportData.summary.total_gpu_hours}
          />

        </div>
      )}
      </>
    )}
    </>
  );
};

export default ReportGenerator;
