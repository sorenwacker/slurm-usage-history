import React from 'react';
import { COLORS } from '../../theme/colors';
import { formatNumber, formatCompact, getPeriodLabel } from './reportHelpers';

interface Summary {
  total_jobs: number;
  total_cpu_hours: number;
  total_gpu_hours: number;
  total_users: number;
}

interface Comparison {
  jobs_change_percent: number;
  cpu_hours_change_percent: number;
  gpu_hours_change_percent: number;
  users_change_percent: number;
}

interface ReportOverviewProps {
  summary: Summary;
  comparison?: Comparison | null;
  reportType: 'monthly' | 'quarterly' | 'annual';
}

const ReportOverview: React.FC<ReportOverviewProps> = ({ summary, comparison, reportType }) => {
  const renderComparisonIndicator = (changePercent: number, periodLabel: string) => {
    if (changePercent === 0) {
      return (
        <div style={{ fontSize: '0.7rem', color: '#6b7280', marginTop: '0.25rem' }}>
          0.0% → vs previous {periodLabel}
        </div>
      );
    }

    const isPositive = changePercent > 0;
    const color = isPositive ? '#22c55e' : '#ef4444';
    const arrow = isPositive ? '↑' : '↓';
    const sign = isPositive ? '+' : '';

    return (
      <div style={{ fontSize: '0.7rem', color: color, marginTop: '0.25rem', fontWeight: 600 }}>
        {sign}{changePercent.toFixed(1)}% {arrow} vs previous {periodLabel}
      </div>
    );
  };

  return (
    <>
      <h3 style={{ marginTop: '2rem', marginBottom: '1rem', color: '#000' }}>Executive Summary</h3>
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem',
        marginBottom: '2rem',
      }}>
        {/* Total Jobs */}
        <div style={{
          background: 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)',
          padding: '1rem',
          borderRadius: '6px',
          border: '1px solid #e0e0e0',
        }}>
          <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.25rem', fontWeight: 600 }}>
            Total Jobs
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: COLORS.total_jobs }}>
            {formatCompact(summary.total_jobs)}
          </div>
          <div style={{ fontSize: '0.7rem', color: '#888', marginTop: '0.25rem' }}>
            {formatNumber(summary.total_jobs)} jobs submitted
          </div>
          {comparison && renderComparisonIndicator(
            comparison.jobs_change_percent,
            getPeriodLabel(reportType)
          )}
        </div>

        {/* Total CPU Hours */}
        <div style={{
          background: 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)',
          padding: '1rem',
          borderRadius: '6px',
          border: '1px solid #e0e0e0',
        }}>
          <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.25rem', fontWeight: 600 }}>
            Total CPU Hours
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: COLORS.cpu_hours }}>
            {formatCompact(summary.total_cpu_hours)}
          </div>
          <div style={{ fontSize: '0.7rem', color: '#888', marginTop: '0.25rem' }}>
            {formatNumber(summary.total_cpu_hours)} hours
          </div>
          {comparison && renderComparisonIndicator(
            comparison.cpu_hours_change_percent,
            getPeriodLabel(reportType)
          )}
        </div>

        {/* Total GPU Hours */}
        <div style={{
          background: 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)',
          padding: '1rem',
          borderRadius: '6px',
          border: '1px solid #e0e0e0',
        }}>
          <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.25rem', fontWeight: 600 }}>
            Total GPU Hours
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: COLORS.gpu_hours }}>
            {formatCompact(summary.total_gpu_hours)}
          </div>
          <div style={{ fontSize: '0.7rem', color: '#888', marginTop: '0.25rem' }}>
            {formatNumber(summary.total_gpu_hours)} hours
          </div>
          {comparison && renderComparisonIndicator(
            comparison.gpu_hours_change_percent,
            getPeriodLabel(reportType)
          )}
        </div>

        {/* Total Active Users */}
        <div style={{
          background: 'linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%)',
          padding: '1rem',
          borderRadius: '6px',
          border: '1px solid #e0e0e0',
        }}>
          <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.25rem', fontWeight: 600 }}>
            Total Active Users
          </div>
          <div style={{ fontSize: '1.5rem', fontWeight: 700, color: COLORS.users }}>
            {formatCompact(summary.total_users)}
          </div>
          <div style={{ fontSize: '0.7rem', color: '#888', marginTop: '0.25rem' }}>
            Unique users in period
          </div>
          {comparison && renderComparisonIndicator(
            comparison.users_change_percent,
            getPeriodLabel(reportType)
          )}
        </div>
      </div>
    </>
  );
};

export default ReportOverview;
