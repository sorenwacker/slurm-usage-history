import { useMemo } from 'react';
import type { AggregatedChartsResponse, ChartData } from '../types';

interface ProcessedNodeData {
  cpu: ChartData | null;
  gpu: ChartData | null;
}

interface ClusterUtilization {
  cpu: number | null;
  gpu: number | null;
}

export function useProcessedNodeData(
  data: AggregatedChartsResponse | undefined,
  hideUnusedNodes: boolean,
  sortByUsage: boolean,
  normalizeNodeUsage: boolean
): ProcessedNodeData {
  return useMemo(() => {
    if (!data) return { cpu: null, gpu: null };

    const normalizeValue = (value: number, maxCapacity: number): number => {
      if (maxCapacity <= 0) return 0;
      return Math.min(100, (value / maxCapacity) * 100);
    };

    const filterAndSortNodeData = (nodeData: ChartData, resourceType: 'cpu' | 'gpu'): ChartData => {
      let indices = nodeData.x.map((_, i) => i);

      const totalHours = nodeData.total_hours || 0;
      const shouldNormalize = normalizeNodeUsage && nodeData.hardware_config && totalHours > 0;

      const getSortValue = (idx: number): number => {
        let rawValue = 0;
        if (nodeData.series) {
          rawValue = nodeData.series.reduce((sum, s) => sum + (s.data[idx] || 0), 0);
        } else if (nodeData.y) {
          rawValue = nodeData.y[idx] as number;
        }

        if (shouldNormalize && nodeData.hardware_config) {
          const node = String(nodeData.x[idx]);
          const hw = nodeData.hardware_config[node];
          if (hw) {
            const capacity = resourceType === 'cpu' ? hw.cpu_cores : hw.gpu_count;
            const maxCapacity = capacity * totalHours;
            return normalizeValue(rawValue, maxCapacity);
          }
        }
        return rawValue;
      };

      if (hideUnusedNodes) {
        indices = indices.filter(i => {
          if (nodeData.series) {
            const total = nodeData.series.reduce((sum, s) => sum + (s.data[i] || 0), 0);
            return total > 0;
          } else if (nodeData.y) {
            return (nodeData.y[i] as number) > 0;
          }
          return true;
        });
      }

      if (sortByUsage) {
        indices.sort((a, b) => {
          const valueA = getSortValue(a);
          const valueB = getSortValue(b);
          return valueB - valueA;
        });
      }

      const filteredNodes = indices.map(i => nodeData.x[i]);
      const filteredHardwareConfig = nodeData.hardware_config
        ? Object.fromEntries(
            filteredNodes.map(node => [node, nodeData.hardware_config![String(node)]])
              .filter(([_, config]) => config !== undefined)
          )
        : undefined;

      let processedY: (string | number)[] | undefined = undefined;
      if (nodeData.y) {
        processedY = indices.map(i => {
          const node = String(nodeData.x[i]);
          const rawValue = nodeData.y![i] as number;
          if (shouldNormalize && filteredHardwareConfig[node]) {
            const hw = filteredHardwareConfig[node];
            const capacity = resourceType === 'cpu' ? hw.cpu_cores : hw.gpu_count;
            const maxCapacity = capacity * totalHours;
            return normalizeValue(rawValue, maxCapacity);
          }
          return rawValue;
        });
      }

      let processedSeries = nodeData.series?.map(s => ({
        ...s,
        data: indices.map(i => {
          const node = String(nodeData.x[i]);
          const rawValue = s.data[i];
          if (shouldNormalize && filteredHardwareConfig && filteredHardwareConfig[node]) {
            const hw = filteredHardwareConfig[node];
            const capacity = resourceType === 'cpu' ? hw.cpu_cores : hw.gpu_count;
            const maxCapacity = capacity * totalHours;
            return normalizeValue(rawValue, maxCapacity);
          }
          return rawValue;
        })
      }));

      return {
        ...nodeData,
        x: filteredNodes,
        y: processedY,
        series: processedSeries,
        normalized: shouldNormalize,
        hardware_config: filteredHardwareConfig,
      };
    };

    return {
      cpu: data.node_cpu_usage ? filterAndSortNodeData(data.node_cpu_usage, 'cpu') : null,
      gpu: data.node_gpu_usage ? filterAndSortNodeData(data.node_gpu_usage, 'gpu') : null
    };
  }, [data, hideUnusedNodes, sortByUsage, normalizeNodeUsage]);
}

export function useClusterUtilization(processedNodeData: ProcessedNodeData): ClusterUtilization {
  return useMemo(() => {
    if (!processedNodeData.cpu?.normalized && !processedNodeData.gpu?.normalized) {
      return { cpu: null, gpu: null };
    }

    const calculateAverage = (nodeData: ChartData | null): number | null => {
      if (!nodeData || !nodeData.normalized) return null;

      let total = 0;
      let count = 0;

      if (nodeData.series && nodeData.series.length > 0) {
        for (let i = 0; i < nodeData.x.length; i++) {
          const nodeTotal = nodeData.series.reduce((sum, s) => sum + (s.data[i] || 0), 0);
          total += nodeTotal;
          count++;
        }
      } else if (nodeData.y) {
        nodeData.y.forEach(val => {
          total += val as number;
          count++;
        });
      }

      return count > 0 ? total / count : null;
    };

    return {
      cpu: calculateAverage(processedNodeData.cpu),
      gpu: calculateAverage(processedNodeData.gpu),
    };
  }, [processedNodeData]);
}
