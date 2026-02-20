import React, { useState, useEffect, useMemo, useRef } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { dashboardApi, reportsApi, authApi } from '../api/client';
import Header from '../components/Header';
import Footer from '../components/Footer';
import Filters from '../components/Filters';
import StatsCards from '../components/StatsCards';
import Charts from '../components/Charts';
import ReportControls from '../components/ReportControls';
import ReportPreview from '../components/ReportPreview';
import type { FilterRequest } from '../types';
import type { ReportData } from '../components/ReportPreview';

const Dashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'reports'>('overview');
  const queryClient = useQueryClient();

  // Fetch current user info to check admin status
  const { data: userInfo } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authApi.getCurrentUser,
  });

  // Handler for dev admin toggle - refetches user info
  const handleDevAdminToggle = () => {
    queryClient.invalidateQueries({ queryKey: ['currentUser'] });
  };
  const [selectedHostname, setSelectedHostname] = useState<string>('');
  const previousHostname = useRef<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [selectedPartitions, setSelectedPartitions] = useState<string[]>([]);
  const [selectedAccounts, setSelectedAccounts] = useState<string[]>([]);
  const [selectedUsers, setSelectedUsers] = useState<string[]>([]);
  const [selectedQos, setSelectedQos] = useState<string[]>([]);
  const [selectedStates, setSelectedStates] = useState<string[]>([]);
  const [colorBy, setColorBy] = useState<string>(''); // Color/group by dimension
  const [accountSegments, setAccountSegments] = useState<number>(3); // Account name formatting (0=full, 1-3=segments)
  const [periodType, setPeriodType] = useState<string>('auto'); // Time aggregation: auto, day, week, month, year
  const [hideUnusedNodes, setHideUnusedNodes] = useState<boolean>(true); // Hide nodes with 0 usage
  const [sortByUsage, setSortByUsage] = useState<boolean>(false); // Sort nodes by usage
  const [normalizeNodeUsage, setNormalizeNodeUsage] = useState<boolean>(false); // Normalize to 100% capacity

  // Report state
  const [reportHostname, setReportHostname] = useState<string>('');
  const [reportType, setReportType] = useState<'monthly' | 'quarterly' | 'annual'>('monthly');
  const [selectedYear, setSelectedYear] = useState<number>(new Date().getFullYear());
  const [selectedMonth, setSelectedMonth] = useState<number>(new Date().getMonth() + 1);
  const [selectedQuarter, setSelectedQuarter] = useState<number>(Math.ceil((new Date().getMonth() + 1) / 3));
  const [downloadFormat, setDownloadFormat] = useState<'pdf' | 'csv' | 'json'>('pdf');

  // Helper function to calculate start date (6 weeks before max_date)
  const calculateStartDate = (maxDate: string): string => {
    const date = new Date(maxDate);
    date.setDate(date.getDate() - 42); // 6 weeks = 42 days
    return date.toISOString().split('T')[0];
  };

  // Helper function to automatically determine period type based on date range
  const calculatePeriodType = (start: string, end: string): string => {
    if (!start || !end) return 'month';

    const startDate = new Date(start);
    const endDate = new Date(end);
    const diffTime = Math.abs(endDate.getTime() - startDate.getTime());
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    // Automatic period selection based on date range
    if (diffDays <= 60) {
      return 'day';  // Up to 2 months: daily granularity
    } else if (diffDays <= 180) {
      return 'week';  // 2-6 months: weekly granularity
    } else if (diffDays <= 730) {
      return 'month';  // 6-24 months: monthly granularity
    } else {
      return 'year';  // More than 24 months: yearly granularity
    }
  };

  // Determine actual period type to use (auto or manual selection)
  const actualPeriodType = periodType === 'auto'
    ? calculatePeriodType(startDate, endDate)
    : periodType;

  // Fetch full cluster list (never filtered by hostname)
  const { data: allClustersMetadata } = useQuery({
    queryKey: ['allClusters'],
    queryFn: () => dashboardApi.getMetadata({}),
    refetchOnMount: true,
    staleTime: 0,
    placeholderData: (previousData) => previousData,
  });

  // Fetch metadata - refetch when hostname or date range changes to update filter options
  const { data: metadata, isLoading: metadataLoading } = useQuery({
    queryKey: ['metadata', selectedHostname, startDate, endDate],
    queryFn: () => dashboardApi.getMetadata({
      hostname: selectedHostname || undefined,
      start_date: startDate || undefined,
      end_date: endDate || undefined,
    }),
    refetchOnMount: true,
    staleTime: 0,
    placeholderData: (previousData) => previousData,
  });

  // Combine metadata: use full cluster list from allClustersMetadata, but filtered data from metadata
  const combinedMetadata = useMemo(() => {
    if (!allClustersMetadata) return metadata;
    if (!metadata) return allClustersMetadata;

    return {
      ...metadata,
      hostnames: allClustersMetadata.hostnames,  // Always show all clusters in dropdown
      date_ranges: {
        ...allClustersMetadata.date_ranges,  // Include all cluster date ranges
        ...metadata.date_ranges,  // Override with filtered ranges if available
      },
    };
  }, [allClustersMetadata, metadata]);

  // Set initial hostname and dates when metadata loads
  useEffect(() => {
    if (allClustersMetadata && allClustersMetadata.hostnames.length > 0 && !selectedHostname) {
      const firstHostname = allClustersMetadata.hostnames[0];
      setSelectedHostname(firstHostname);

      // Set date range - default to last 6 weeks
      const dateRange = allClustersMetadata.date_ranges[firstHostname];
      if (dateRange && dateRange.max_date) {
        const calculatedStartDate = calculateStartDate(dateRange.max_date);
        setStartDate(calculatedStartDate);
        setEndDate(dateRange.max_date);
      }
    }
  }, [allClustersMetadata, selectedHostname]);

  // Update dates when hostname changes (but not on every metadata refetch)
  useEffect(() => {
    // Only run when hostname actually changes
    if (selectedHostname && selectedHostname !== previousHostname.current) {
      // Get the latest metadata for the new hostname
      if (allClustersMetadata && allClustersMetadata.date_ranges[selectedHostname]) {
        const dateRange = allClustersMetadata.date_ranges[selectedHostname];
        if (dateRange.max_date) {
          // Default to last 6 weeks for new hostname
          const calculatedStartDate = calculateStartDate(dateRange.max_date);
          setStartDate(calculatedStartDate);
          setEndDate(dateRange.max_date);
        }
      }
      // Reset filters when changing hostname
      setSelectedPartitions([]);
      setSelectedAccounts([]);
      setSelectedUsers([]);
      setSelectedQos([]);
      setSelectedStates([]);

      // Update the ref to track current hostname
      previousHostname.current = selectedHostname;
    }
  }, [selectedHostname, allClustersMetadata]);

  // Report-related logic
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

  // Fetch report preview
  const {
    data: reportData,
    isLoading: reportLoading,
    error: reportError,
  } = useQuery<ReportData>({
    queryKey: ['reportPreview', reportHostname, reportType, selectedYear, selectedMonth, selectedQuarter],
    queryFn: () => reportsApi.previewReport(
      reportHostname,
      reportType,
      selectedYear,
      reportType === 'monthly' ? selectedMonth : undefined,
      reportType === 'quarterly' ? selectedQuarter : undefined
    ),
    enabled: !!reportHostname && activeTab === 'reports',
  });

  const handleDownloadReport = () => {
    reportsApi.downloadReport(
      reportHostname,
      reportType,
      selectedYear,
      reportType === 'monthly' ? selectedMonth : undefined,
      reportType === 'quarterly' ? selectedQuarter : undefined,
      downloadFormat
    );
  };

  // Fetch aggregated chart data (fast API - 43,000x smaller payload!)
  const filterRequest: FilterRequest = {
    hostname: selectedHostname,
    start_date: startDate,
    end_date: endDate,
    partitions: selectedPartitions.length > 0 ? selectedPartitions : undefined,
    accounts: selectedAccounts.length > 0 ? selectedAccounts : undefined,
    users: selectedUsers.length > 0 ? selectedUsers : undefined,
    qos: selectedQos.length > 0 ? selectedQos : undefined,
    states: selectedStates.length > 0 ? selectedStates : undefined,
    period_type: actualPeriodType,  // Use the calculated or manually selected period type
    color_by: colorBy || undefined,  // Group/color charts by selected dimension
    account_segments: accountSegments > 0 ? accountSegments : undefined,  // Format account names
    // Note: hide_unused_nodes, sort_by_usage, and normalize_node_usage are handled client-side in Charts component
  };

  const {
    data: chartsData,
    isLoading: dataLoading,
    error: dataError,
  } = useQuery({
    queryKey: ['aggregatedCharts', filterRequest],
    queryFn: async () => {
      const queryStart = Date.now();
      console.log('═══════════════════════════════════════════════════════');
      console.log('🔄 FETCHING DASHBOARD DATA');
      console.log('═══════════════════════════════════════════════════════');
      console.log(`🖥️  Cluster: ${filterRequest.hostname}`);
      console.log(`📅 Date range: ${filterRequest.start_date} → ${filterRequest.end_date}`);
      console.log(`📊 Period type: ${filterRequest.period_type}`);
      console.log(`🎨 Color by: ${filterRequest.color_by || 'None'}`);
      console.log(`📝 Account segments: ${filterRequest.account_segments || 'Full names'}`);
      if (filterRequest.partitions?.length) console.log(`🔧 Partitions: ${filterRequest.partitions.join(', ')}`);
      if (filterRequest.accounts?.length) console.log(`👥 Accounts: ${filterRequest.accounts.join(', ')}`);
      if (filterRequest.users?.length) console.log(`👤 Users: ${filterRequest.users.join(', ')}`);
      if (filterRequest.qos?.length) console.log(`⚡ QOS: ${filterRequest.qos.join(', ')}`);
      if (filterRequest.states?.length) console.log(`📌 States: ${filterRequest.states.join(', ')}`);

      const result = await dashboardApi.getAggregatedCharts(filterRequest);
      const queryTime = Date.now() - queryStart;

      console.log(`⏱️  API response time: ${queryTime}ms`);
      console.log(`✅ Received ${result.summary.total_jobs.toLocaleString()} jobs`);
      console.log('═══════════════════════════════════════════════════════');

      return result;
    },
    enabled: !!selectedHostname,
  });

  if (metadataLoading) {
    return (
      <div className="app">
        <Header userInfo={userInfo} onDevAdminToggle={handleDevAdminToggle} />
        <div className="container">
          <div className="loading-screen">
            <div className="loading-spinner"></div>
            <h2>Loading Dashboard...</h2>
            <p>Fetching cluster metadata from backend</p>
            <p className="loading-detail">API: http://localhost:8100</p>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  if (!metadata || metadata.hostnames.length === 0) {
    return (
      <div className="app">
        <Header userInfo={userInfo} onDevAdminToggle={handleDevAdminToggle} />
        <div className="container">
          <div className="error-screen">
            <h2>No Data Available</h2>
            <p>No cluster data found. Please ensure data files are in the correct location.</p>
          </div>
        </div>
        <Footer />
      </div>
    );
  }

  return (
    <div className="app">
      <Header activeTab={activeTab} onTabChange={setActiveTab} userInfo={userInfo} onDevAdminToggle={handleDevAdminToggle} />
      <div className="dashboard-layout">
        {/* Sidebar for both overview and reports */}
        <div className="sidebar">
          {activeTab === 'overview' ? (
            <Filters
              metadata={combinedMetadata}
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
              selectedUsers={selectedUsers}
              setSelectedUsers={setSelectedUsers}
              selectedQos={selectedQos}
              setSelectedQos={setSelectedQos}
              selectedStates={selectedStates}
              setSelectedStates={setSelectedStates}
              colorBy={colorBy}
              setColorBy={setColorBy}
              accountSegments={accountSegments}
              setAccountSegments={setAccountSegments}
              isAdmin={userInfo?.is_admin ?? false}
              periodType={periodType}
              setPeriodType={setPeriodType}
              currentPeriodType={actualPeriodType}
            />
          ) : (
            <ReportControls
              metadata={metadata}
              reportHostname={reportHostname}
              setReportHostname={setReportHostname}
              reportType={reportType}
              setReportType={setReportType}
              selectedYear={selectedYear}
              setSelectedYear={setSelectedYear}
              selectedMonth={selectedMonth}
              setSelectedMonth={setSelectedMonth}
              selectedQuarter={selectedQuarter}
              setSelectedQuarter={setSelectedQuarter}
              downloadFormat={downloadFormat}
              setDownloadFormat={setDownloadFormat}
              onDownload={handleDownloadReport}
              availableYears={availableYears}
            />
          )}
        </div>
        <div className="main-content">
          {/* Tab Content */}
          {activeTab === 'overview' ? (
            <>
              {dataError && (
                <div className="error">
                  Error loading data: {dataError instanceof Error ? dataError.message : 'Unknown error'}
                </div>
              )}

              {dataLoading ? (
                <div className="loading-screen">
                  <div className="loading-spinner"></div>
                  <h2>Loading Charts...</h2>
                  <p>Aggregating data for {selectedHostname}</p>
                  <p className="loading-detail">Period: {startDate} to {endDate} ({actualPeriodType})</p>
                </div>
              ) : (
                <>
                  <StatsCards data={chartsData} />
                  <Charts
                    data={chartsData}
                    hideUnusedNodes={hideUnusedNodes}
                    setHideUnusedNodes={setHideUnusedNodes}
                    sortByUsage={sortByUsage}
                    setSortByUsage={setSortByUsage}
                    normalizeNodeUsage={normalizeNodeUsage}
                    setNormalizeNodeUsage={setNormalizeNodeUsage}
                    colorBy={colorBy}
                    periodType={actualPeriodType}
                  />
                </>
              )}
            </>
          ) : (
            <ReportPreview
              reportData={reportData}
              isLoading={reportLoading}
              error={reportError}
              reportType={reportType}
            />
          )}
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default Dashboard;
