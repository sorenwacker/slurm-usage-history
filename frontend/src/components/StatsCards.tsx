import React from 'react';
import type { FilterResponse } from '../types';
import { formatNumber, formatDecimal } from '../utils/format';

interface StatsCardsProps {
  data: FilterResponse | undefined;
}

const StatsCards: React.FC<StatsCardsProps> = ({ data }) => {
  if (!data) {
    return null;
  }

  return (
    <div className="stats-grid">
      <div className="stat-card">
        <h4>Total Active Users</h4>
        <div className="stat-value">{formatNumber(data.total_users)}</div>
      </div>

      <div className="stat-card">
        <h4>Total Jobs</h4>
        <div className="stat-value">{formatNumber(data.total_jobs)}</div>
      </div>

      <div className="stat-card">
        <h4>Total CPU Hours</h4>
        <div className="stat-value">{formatDecimal(data.total_cpu_hours, 0)}</div>
      </div>

      <div className="stat-card">
        <h4>Total GPU Hours</h4>
        <div className="stat-value">{formatDecimal(data.total_gpu_hours, 0)}</div>
      </div>
    </div>
  );
};

export default StatsCards;
