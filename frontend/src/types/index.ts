export interface JobRecord {
  JobID: string;
  User: string;
  Account: string;
  Partition: string;
  State: string;
  QOS?: string;
  Submit: string;
  Start?: string;
  End?: string;
  CPUHours: number;
  GPUHours: number;
  AllocCPUS: number;
  AllocGPUS: number;
  AllocNodes: number;
  NodeList?: string;
  SubmitYearMonth?: string;
  SubmitYearWeek?: string;
  SubmitYear?: number;
}

export interface FilterRequest {
  hostname: string;
  start_date?: string;
  end_date?: string;
  partitions?: string[];
  accounts?: string[];
  users?: string[];
  qos?: string[];
  states?: string[];
  complete_periods_only?: boolean;
  period_type?: string;
}

export interface FilterResponse {
  total_jobs: number;
  total_cpu_hours: number;
  total_gpu_hours: number;
  total_users: number;
  data: JobRecord[];
}

export interface MetadataResponse {
  hostnames: string[];
  partitions: Record<string, string[]>;
  accounts: Record<string, string[]>;
  users: Record<string, string[]>;
  qos: Record<string, string[]>;
  states: Record<string, string[]>;
  date_ranges: Record<string, { min_date: string; max_date: string }>;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  data_loaded: boolean;
  hostnames: string[];
}

export interface ClusterStats {
  hostname: string;
  total_jobs: number;
  total_cpu_hours: number;
  total_gpu_hours: number;
  total_users: number;
  partitions: string[];
}
