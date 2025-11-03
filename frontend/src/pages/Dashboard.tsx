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

  // Helper function to calculate date 6 weeks ago from max date
  const calculateStartDate = (maxDate: string): string => {
    const date = new Date(maxDate);
    // Go back 6 weeks (42 days)
    date.setDate(date.getDate() - 42);
    return date.toISOString().split('T')[0];
  };

  // Set initial hostname and dates when metadata loads
  useEffect(() => {
    if (metadata && metadata.hostnames.length > 0 && !selectedHostname) {
      const firstHostname = metadata.hostnames[0];
      setSelectedHostname(firstHostname);

      // Set date range - default to last 6 weeks
      const dateRange = metadata.date_ranges[firstHostname];
      if (dateRange && dateRange.max_date) {
        const calculatedStartDate = calculateStartDate(dateRange.max_date);
        setStartDate(calculatedStartDate);
        setEndDate(dateRange.max_date);
      }
    }
  }, [metadata, selectedHostname]);

  // Update dates when hostname changes
  useEffect(() => {
    if (metadata && selectedHostname) {
      const dateRange = metadata.date_ranges[selectedHostname];
      if (dateRange && dateRange.max_date) {
        // Default to last 6 weeks for new hostname
        const calculatedStartDate = calculateStartDate(dateRange.max_date);
        setStartDate(calculatedStartDate);
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
          <div className="loading-screen">
            <div className="loading-spinner"></div>
            <h2>Loading Dashboard...</h2>
            <p>Fetching cluster metadata from backend</p>
            <p className="loading-detail">API: http://localhost:8100</p>
          </div>
        </div>
      </div>
    );
  }

  if (!metadata || metadata.hostnames.length === 0) {
    return (
      <div className="app">
        <Header />
        <div className="container">
          <div className="error-screen">
            <h2>No Data Available</h2>
            <p>No cluster data found. Please ensure data files are in the correct location.</p>
          </div>
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
