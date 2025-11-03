import axios from 'axios';
import type {
  FilterRequest,
  FilterResponse,
  MetadataResponse,
  HealthResponse,
  ClusterStats,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8100';

const apiClient = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardApi = {
  getHealth: async (): Promise<HealthResponse> => {
    const response = await apiClient.get<HealthResponse>('/dashboard/health');
    return response.data;
  },

  getMetadata: async (): Promise<MetadataResponse> => {
    const response = await apiClient.get<MetadataResponse>('/dashboard/metadata');
    return response.data;
  },

  filterData: async (request: FilterRequest): Promise<FilterResponse> => {
    const response = await apiClient.post<FilterResponse>('/dashboard/filter', request);
    return response.data;
  },

  getClusterStats: async (
    hostname: string,
    startDate?: string,
    endDate?: string
  ): Promise<ClusterStats> => {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await apiClient.get<ClusterStats>(
      `/dashboard/stats/${hostname}?${params.toString()}`
    );
    return response.data;
  },
};

export default apiClient;
