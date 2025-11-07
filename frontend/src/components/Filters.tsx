import React, { useState } from 'react';
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
  selectedUsers: string[];
  setSelectedUsers: (users: string[]) => void;
  selectedQos: string[];
  setSelectedQos: (qos: string[]) => void;
  selectedStates: string[];
  setSelectedStates: (states: string[]) => void;
  colorBy: string;
  setColorBy: (colorBy: string) => void;
  accountSegments: number;
  setAccountSegments: (segments: number) => void;
  periodType: string;
  setPeriodType: (periodType: string) => void;
  currentPeriodType: string;
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
  selectedUsers,
  setSelectedUsers,
  selectedQos,
  setSelectedQos,
  selectedStates,
  setSelectedStates,
  colorBy,
  setColorBy,
  accountSegments,
  setAccountSegments,
  periodType,
  setPeriodType,
  currentPeriodType,
}) => {
  // Individual collapse states for each filter category
  const [isPartitionsExpanded, setIsPartitionsExpanded] = useState(false);
  const [isAccountsExpanded, setIsAccountsExpanded] = useState(false);
  const [isUsersExpanded, setIsUsersExpanded] = useState(false);
  const [isQosExpanded, setIsQosExpanded] = useState(false);
  const [isStatesExpanded, setIsStatesExpanded] = useState(false);

  // Search states for each filter
  const [partitionSearch, setPartitionSearch] = useState('');
  const [accountSearch, setAccountSearch] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [qosSearch, setQosSearch] = useState('');
  const [stateSearch, setStateSearch] = useState('');

  const dateRange = metadata && selectedHostname ? metadata.date_ranges[selectedHostname] : null;

  const hasActiveFilters =
    selectedPartitions.length > 0 ||
    selectedAccounts.length > 0 ||
    selectedUsers.length > 0 ||
    selectedQos.length > 0 ||
    selectedStates.length > 0;

  const clearAllFilters = () => {
    setSelectedPartitions([]);
    setSelectedAccounts([]);
    setSelectedUsers([]);
    setSelectedQos([]);
    setSelectedStates([]);
  };

  // Helper function to filter items based on search
  const filterItems = (items: string[], search: string): string[] => {
    if (!search.trim()) return items;
    return items.filter(item =>
      item.toLowerCase().includes(search.toLowerCase())
    );
  };

  // Helper to toggle item selection
  const toggleItem = (item: string, selected: string[], setter: (items: string[]) => void) => {
    if (selected.includes(item)) {
      setter(selected.filter(i => i !== item));
    } else {
      setter([...selected, item]);
    }
  };

  // Component for searchable checkbox list with collapse
  const SearchableCheckboxList: React.FC<{
    label: string;
    items: string[];
    selected: string[];
    setSelected: (items: string[]) => void;
    search: string;
    setSearch: (search: string) => void;
    isExpanded: boolean;
    setIsExpanded: (expanded: boolean) => void;
  }> = ({ label, items, selected, setSelected, search, setSearch, isExpanded, setIsExpanded }) => {
    const filteredItems = filterItems(items, search);
    const allFiltered = filteredItems.length === selected.filter(s => filteredItems.includes(s)).length && filteredItems.length > 0;

    const toggleAll = () => {
      if (allFiltered) {
        setSelected(selected.filter(s => !filteredItems.includes(s)));
      } else {
        setSelected([...new Set([...selected, ...filteredItems])]);
      }
    };

    return (
      <div className="filter-group">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
          <div
            onClick={() => setIsExpanded(!isExpanded)}
            style={{ display: 'flex', alignItems: 'center', cursor: 'pointer', flex: 1 }}
          >
            <span style={{ marginRight: '0.5rem', fontSize: '0.9rem' }}>
              {isExpanded ? '▼' : '▶'}
            </span>
            <label style={{ cursor: 'pointer', margin: 0 }}>{label}</label>
            {selected.length > 0 && (
              <span style={{
                marginLeft: '0.5rem',
                fontSize: '0.75rem',
                color: '#6366f1',
                fontWeight: 'bold'
              }}>
                ({selected.length} selected)
              </span>
            )}
          </div>
          {selected.length > 0 && (
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                setSelected([]);
              }}
              style={{
                fontSize: '0.75rem',
                padding: '0.2rem 0.5rem',
                background: '#dc3545',
                color: 'white',
                border: 'none',
                borderRadius: '3px',
                cursor: 'pointer',
              }}
            >
              Clear
            </button>
          )}
        </div>
        {isExpanded && (
          <>
            <input
              type="text"
              placeholder={`Search ${label.toLowerCase()}...`}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem',
                borderRadius: '4px',
                border: '1px solid #ccc',
                fontSize: '0.875rem',
                marginBottom: '0.5rem',
              }}
            />
            <div style={{
              maxHeight: '200px',
              overflowY: 'auto',
              border: '1px solid #dee2e6',
              borderRadius: '4px',
              padding: '0.5rem',
            }}>
              {filteredItems.length > 1 && (
                <label style={{ display: 'flex', alignItems: 'center', padding: '0.25rem 0', cursor: 'pointer', fontWeight: 'bold', borderBottom: '1px solid #e0e0e0', marginBottom: '0.25rem' }}>
                  <input
                    type="checkbox"
                    checked={allFiltered}
                    onChange={toggleAll}
                    style={{ marginRight: '0.5rem' }}
                  />
                  Select All ({filteredItems.length})
                </label>
              )}
              {filteredItems.length === 0 && (
                <div style={{ color: '#666', fontSize: '0.875rem', padding: '0.5rem', textAlign: 'center' }}>
                  No items found
                </div>
              )}
              {filteredItems.map((item) => (
                <label key={item} style={{ display: 'flex', alignItems: 'center', padding: '0.25rem 0', cursor: 'pointer' }}>
                  <input
                    type="checkbox"
                    checked={selected.includes(item)}
                    onChange={() => toggleItem(item, selected, setSelected)}
                    style={{ marginRight: '0.5rem' }}
                  />
                  {item}
                </label>
              ))}
            </div>
          </>
        )}
      </div>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
      {/* Always visible: Cluster selection */}
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

      {/* Always visible: Date range */}
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

      {/* Always visible: Time Period */}
      <div className="filter-group">
        <label htmlFor="period-type" title="Auto mode selects granularity based on date range">
          Time Period
        </label>
        <select
          id="period-type"
          value={periodType}
          onChange={(e) => setPeriodType(e.target.value)}
          title="Auto mode selects granularity based on date range"
        >
          <option value="auto">Auto (currently: {currentPeriodType})</option>
          <option value="day">Daily</option>
          <option value="week">Weekly</option>
          <option value="month">Monthly</option>
          <option value="year">Yearly</option>
        </select>
      </div>

      {/* Always visible: Color By */}
      <div className="filter-group">
        <label htmlFor="color-by">Color By</label>
        <select
          id="color-by"
          value={colorBy}
          onChange={(e) => setColorBy(e.target.value)}
        >
          <option value="">None (default)</option>
          <option value="Account">Account</option>
          <option value="Partition">Partition</option>
          <option value="State">State</option>
          <option value="QOS">QoS</option>
          <option value="User">User</option>
        </select>
      </div>

      {colorBy === 'Account' && (
        <div className="filter-group">
          <label>Account Name Format</label>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="radio"
                name="account-segments"
                value="0"
                checked={accountSegments === 0}
                onChange={() => setAccountSegments(0)}
              />
              <span>Full names</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="radio"
                name="account-segments"
                value="1"
                checked={accountSegments === 1}
                onChange={() => setAccountSegments(1)}
              />
              <span>First segment</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="radio"
                name="account-segments"
                value="2"
                checked={accountSegments === 2}
                onChange={() => setAccountSegments(2)}
              />
              <span>First two segments</span>
            </label>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}>
              <input
                type="radio"
                name="account-segments"
                value="3"
                checked={accountSegments === 3}
                onChange={() => setAccountSegments(3)}
              />
              <span>First three segments</span>
            </label>
          </div>
        </div>
      )}

      {/* Separator and Clear All button */}
      {hasActiveFilters && (
        <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '0.5rem' }}>
          <button
            type="button"
            onClick={clearAllFilters}
            style={{
              fontSize: '0.75rem',
              padding: '0.3rem 0.6rem',
              background: '#6366f1',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontWeight: 500,
            }}
            onMouseOver={(e) => (e.currentTarget.style.background = '#4f46e5')}
            onMouseOut={(e) => (e.currentTarget.style.background = '#6366f1')}
          >
            Clear All Filters
          </button>
        </div>
      )}

      <hr style={{ margin: '0.5rem 0', borderColor: '#dee2e6' }} />

      {/* Collapsible filter categories */}
      {selectedHostname && metadata?.partitions[selectedHostname] && (
        <SearchableCheckboxList
          label="Partitions"
          items={metadata.partitions[selectedHostname]}
          selected={selectedPartitions}
          setSelected={setSelectedPartitions}
          search={partitionSearch}
          setSearch={setPartitionSearch}
          isExpanded={isPartitionsExpanded}
          setIsExpanded={setIsPartitionsExpanded}
        />
      )}

      {selectedHostname && metadata?.accounts[selectedHostname] && (
        <SearchableCheckboxList
          label="Accounts"
          items={metadata.accounts[selectedHostname]}
          selected={selectedAccounts}
          setSelected={setSelectedAccounts}
          search={accountSearch}
          setSearch={setAccountSearch}
          isExpanded={isAccountsExpanded}
          setIsExpanded={setIsAccountsExpanded}
        />
      )}

      {selectedHostname && metadata?.users[selectedHostname] && (
        <SearchableCheckboxList
          label="Users"
          items={metadata.users[selectedHostname]}
          selected={selectedUsers}
          setSelected={setSelectedUsers}
          search={userSearch}
          setSearch={setUserSearch}
          isExpanded={isUsersExpanded}
          setIsExpanded={setIsUsersExpanded}
        />
      )}

      {selectedHostname && metadata?.qos[selectedHostname] && (
        <SearchableCheckboxList
          label="QoS"
          items={metadata.qos[selectedHostname]}
          selected={selectedQos}
          setSelected={setSelectedQos}
          search={qosSearch}
          setSearch={setQosSearch}
          isExpanded={isQosExpanded}
          setIsExpanded={setIsQosExpanded}
        />
      )}

      {selectedHostname && metadata?.states[selectedHostname] && (
        <SearchableCheckboxList
          label="Job States"
          items={metadata.states[selectedHostname]}
          selected={selectedStates}
          setSelected={setSelectedStates}
          search={stateSearch}
          setSearch={setStateSearch}
          isExpanded={isStatesExpanded}
          setIsExpanded={setIsStatesExpanded}
        />
      )}
    </div>
  );
};

export default Filters;
