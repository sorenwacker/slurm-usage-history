import React from 'react';
import type { MetadataResponse } from '../types';

interface FiltersProps {
  metadata: MetadataResponse | undefined;
  selectedHostname: string;
  setSelectedHostname: (hostname: string) => void;
  startDate: string;
  setStartDate: (date: string) => void;
  endDate: string;
  setEndDate: (date: string) => void;
  selectedPartitions: string[];
  setSelectedPartitions: (partitions: string[]) => void;
  selectedAccounts: string[];
  setSelectedAccounts: (accounts: string[]) => void;
  selectedStates: string[];
  setSelectedStates: (states: string[]) => void;
}

const Filters: React.FC<FiltersProps> = ({
  metadata,
  selectedHostname,
  setSelectedHostname,
  startDate,
  setStartDate,
  endDate,
  setEndDate,
  selectedPartitions,
  setSelectedPartitions,
  selectedAccounts,
  setSelectedAccounts,
  selectedStates,
  setSelectedStates,
}) => {
  const dateRange = metadata && selectedHostname ? metadata.date_ranges[selectedHostname] : null;

  return (
    <div className="filters">
      <h3>Filters</h3>
      <div className="filter-grid">
        <div className="filter-group">
          <label htmlFor="hostname">Cluster</label>
          <select
            id="hostname"
            value={selectedHostname}
            onChange={(e) => setSelectedHostname(e.target.value)}
          >
            <option value="">Select cluster...</option>
            {metadata?.hostnames.map((hostname) => (
              <option key={hostname} value={hostname}>
                {hostname}
              </option>
            ))}
          </select>
        </div>

        <div className="filter-group">
          <label htmlFor="start-date">Start Date</label>
          <input
            type="date"
            id="start-date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            min={dateRange?.min_date}
            max={dateRange?.max_date}
          />
        </div>

        <div className="filter-group">
          <label htmlFor="end-date">End Date</label>
          <input
            type="date"
            id="end-date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            min={dateRange?.min_date}
            max={dateRange?.max_date}
          />
        </div>

        {selectedHostname && metadata?.partitions[selectedHostname] && (
          <div className="filter-group">
            <label htmlFor="partitions">Partitions</label>
            <select
              id="partitions"
              multiple
              value={selectedPartitions}
              onChange={(e) =>
                setSelectedPartitions(
                  Array.from(e.target.selectedOptions, (option) => option.value)
                )
              }
            >
              {metadata.partitions[selectedHostname].map((partition) => (
                <option key={partition} value={partition}>
                  {partition}
                </option>
              ))}
            </select>
            <small style={{ color: '#666', fontSize: '0.85rem' }}>
              Hold Ctrl/Cmd to select multiple
            </small>
          </div>
        )}

        {selectedHostname && metadata?.accounts[selectedHostname] && (
          <div className="filter-group">
            <label htmlFor="accounts">Accounts</label>
            <select
              id="accounts"
              multiple
              value={selectedAccounts}
              onChange={(e) =>
                setSelectedAccounts(
                  Array.from(e.target.selectedOptions, (option) => option.value)
                )
              }
            >
              {metadata.accounts[selectedHostname].map((account) => (
                <option key={account} value={account}>
                  {account}
                </option>
              ))}
            </select>
            <small style={{ color: '#666', fontSize: '0.85rem' }}>
              Hold Ctrl/Cmd to select multiple
            </small>
          </div>
        )}

        {selectedHostname && metadata?.states[selectedHostname] && (
          <div className="filter-group">
            <label htmlFor="states">Job States</label>
            <select
              id="states"
              multiple
              value={selectedStates}
              onChange={(e) =>
                setSelectedStates(
                  Array.from(e.target.selectedOptions, (option) => option.value)
                )
              }
            >
              {metadata.states[selectedHostname].map((state) => (
                <option key={state} value={state}>
                  {state}
                </option>
              ))}
            </select>
            <small style={{ color: '#666', fontSize: '0.85rem' }}>
              Hold Ctrl/Cmd to select multiple
            </small>
          </div>
        )}
      </div>
    </div>
  );
};

export default Filters;
