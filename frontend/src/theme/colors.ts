/**
 * Centralized color theme for charts and visualizations.
 * Keep in sync with backend/app/theme_colors.py
 */

// Primary metric colors - consistent across all views
export const COLORS = {
  total_jobs: '#6f42c1',      // Purple
  cpu_hours: '#04A5D5',       // Blue
  gpu_hours: '#EC7300',       // Orange
  users: '#28a745',           // Green
  success: '#28a745',         // Green
  duration: '#2ecc71',        // Light green
  waiting: '#e74c3c',         // Red
  failed: '#dc3545',          // Dark red
};

// Chart-specific color palettes
export const PARTITION_COLORS = [
  '#6f42c1',  // Purple
  '#28a745',  // Green
  '#fd7e14',  // Orange
  '#dc3545',  // Red
  '#17a2b8',  // Cyan
  '#ffc107',  // Yellow
];

export const STATE_COLORS: Record<string, string> = {
  COMPLETED: '#28a745',       // Green
  FAILED: '#dc3545',          // Red
  TIMEOUT: '#fd7e14',         // Orange
  CANCELLED: '#6c757d',       // Gray
  PENDING: '#ffc107',         // Yellow
  RUNNING: '#17a2b8',         // Cyan
};

// Section header colors for reports
export const SECTION_COLORS = {
  summary: '#3498db',          // Blue
  duration: '#2ecc71',         // Green
  waiting: '#e74c3c',          // Red
  resources: '#9b59b6',        // Purple
};
