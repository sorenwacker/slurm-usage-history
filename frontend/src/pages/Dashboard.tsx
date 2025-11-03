import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dashboardApi } from '../api/client';
import Header from '../components/Header';
import Filters from '../components/Filters';
import StatsCards from '../components/StatsCards';
import Charts from '../components/Charts';
import type { FilterRequest } from '../types';

const Dashboard: React.FC = () => {
  const [selectedHostname, setSelectedHostname] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [selectedPartitions, setSelectedPartitions] = useState<string[]>([]);
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [selectedStates, setSelectedStates] = useState<string[]>([]);

  // Fetch metadata
  const { data: metadata, isLoading: metadataLoading } = useQuery({
    queryKey: ['metadata'],
    queryFn: dashboardApi.getMetadata,
  });

  // Set initial hostname and dates when metadata loads
  useEffect(() => {
    if (metadata && metadata.hostnames.length > 0 && !selectedHostname) {
      const firstHostname = metadata.hostnames[0];
      setSelectedHostname(firstHostname);

      // Set date range
      const dateRange = metadata.date_ranges[firstHostname];
      if (dateRange) {
        setStartDate(dateRange.min_date);
        setEndDate(dateRange.max_date);
      }
    }
  }, [metadata, selectedHostname]);

  // Update dates when hostname changes
  useEffect(() => {
    if (metadata && selectedHostname) {
      const dateRange = metadata.date_ranges[selectedHostname];
      if (dateRange) {
        setStartDate(dateRange.min_date);
        setEndDate(dateRange.max_date);
      }
      // Reset filters when changing hostname
      setSelectedPartitions([]);
      setSelectedAccounts([]);
      setSelectedStates([]);
    }
  }, [selectedHostname, metadata]);

  // Fetch filtered data
  const filterRequest: FilterRequest = {
    hostname: selectedHostname,
    start_date: startDate,
    end_date: endDate,
    partitions: selectedPartitions.length > 0 ? selectedPartitions : undefined,
    accounts: selectedAccounts.length > 0 ? selectedAccounts : undefined,
    states: selectedStates.length > 0 ? selectedStates : undefined,
  };

  const {
    data: filteredData,
    isLoading: dataLoading,
    error: dataError,
  } = useQuery({
    queryKey: ['filteredData', filterRequest],
    queryFn: () => dashboardApi.filterData(filterRequest),
    enabled: !!selectedHostname,
  });

  if (metadataLoading) {
    return (
      <div className="app">
        <Header />
        <div className="container">
          <div className="loading">Loading dashboard...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="app">
      <Header />
      <div className="container">
        {dataError && (
          <div className="error">
            Error loading data: {dataError instanceof Error ? dataError.message : 'Unknown error'}
          </div>
        )}

        <Filters
          metadata={metadata}
          selectedHostname={selectedHostname}
          setSelectedHostname={setSelectedHostname}
          startDate={startDate}
          setStartDate={setStartDate}
          endDate={endDate}
          setEndDate={setEndDate}
          selectedPartitions={selectedPartitions}
          setSelectedPartitions={setSelectedPartitions}
          selectedAccounts={selectedAccounts}
          setSelectedAccounts={setSelectedAccounts}
          selectedStates={selectedStates}
          setSelectedStates={setSelectedStates}
        />

        {dataLoading ? (
          <div className="loading">Loading data...</div>
        ) : (
          <>
            <StatsCards data={filteredData} />
            <Charts data={filteredData} />
          </>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
