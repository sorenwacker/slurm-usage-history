"""Node usage chart generators for CPU and GPU usage by node."""
from typing import Any

import numpy as np
import pandas as pd

# Import cluster config for node name normalization
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from backend.app.config import get_cluster_config


def generate_node_usage(
    df: pd.DataFrame,
    cluster: str | None = None,
    color_by: str | None = None,
    hide_unused: bool = True,
    sort_by_usage: bool = False,
) -> dict[str, Any]:
    """Aggregate CPU and GPU usage by node.

    Args:
        df: Input DataFrame
        cluster: Cluster name for node normalization (e.g., "DAIC")
        color_by: Optional dimension to group by (Account, Partition, State, QOS, User)
        hide_unused: Hide nodes with 0 usage
        sort_by_usage: Sort nodes by usage (default: alphabetical)

    Returns:
        Dictionary with cpu_usage and gpu_usage data
    """
    if "NodeList" not in df.columns:
        return {
            "cpu_usage": {"x": [], "y": [], "series": []},
            "gpu_usage": {"x": [], "y": [], "series": []},
        }

    # Explode NodeList to get one row per node
    cols = ["NodeList", "CPUHours", "GPUHours"]
    if color_by and color_by in df.columns:
        cols.append(color_by)

    node_df = df[cols].copy()

    # NodeList can be:
    # 1. A numpy array like array(['node1', 'node2'])
    # 2. A list like ['node1', 'node2']
    # 3. A comma-separated string like "node1,node2"
    # The data has already been expanded by unpack_nodelist_string during ingestion
    def process_nodelist(val):
        # If it's a numpy array, convert to list
        if isinstance(val, np.ndarray):
            return val.tolist()
        # If it's already a list or tuple, use as is
        elif isinstance(val, (list, tuple)):
            return list(val)
        # Otherwise it's a string, split on commas
        else:
            return str(val).split(",")

    node_df["NodeList"] = node_df["NodeList"].apply(process_nodelist)
    node_df = node_df.explode("NodeList")
    node_df = node_df[node_df["NodeList"].notna()]
    node_df["NodeList"] = node_df["NodeList"].astype(str).str.strip()

    # Normalize node names using cluster config
    if cluster:
        config = get_cluster_config()
        node_df["NodeList"] = node_df["NodeList"].apply(
            lambda name: config.normalize_node_name(cluster, name)
        )

    if node_df.empty:
        return {
            "cpu_usage": {"x": [], "y": [], "series": []},
            "gpu_usage": {"x": [], "y": [], "series": []},
        }

    # Group by node (and optionally color_by dimension)
    if color_by and color_by in node_df.columns:
        groupby_cols = ["NodeList", color_by]
        cpu_grouped = node_df.groupby(groupby_cols)["CPUHours"].sum().reset_index()
        gpu_grouped = node_df.groupby(groupby_cols)["GPUHours"].sum().reset_index()
    else:
        cpu_grouped = node_df.groupby("NodeList")["CPUHours"].sum().reset_index()
        gpu_grouped = node_df.groupby("NodeList")["GPUHours"].sum().reset_index()

    # Hide unused nodes if requested
    if hide_unused:
        cpu_grouped = cpu_grouped[cpu_grouped["CPUHours"] > 0]
        gpu_grouped = gpu_grouped[gpu_grouped["GPUHours"] > 0]

    # Sort nodes
    if sort_by_usage:
        if color_by and color_by in cpu_grouped.columns:
            cpu_total_per_node = cpu_grouped.groupby("NodeList")["CPUHours"].sum().sort_values(ascending=False)
            gpu_total_per_node = gpu_grouped.groupby("NodeList")["GPUHours"].sum().sort_values(ascending=False)
        else:
            cpu_total_per_node = cpu_grouped.set_index("NodeList")["CPUHours"].sort_values(ascending=False)
            gpu_total_per_node = gpu_grouped.set_index("NodeList")["GPUHours"].sort_values(ascending=False)
        cpu_sorted_nodes = cpu_total_per_node.index.tolist()
        gpu_sorted_nodes = gpu_total_per_node.index.tolist()
    else:
        # Alphabetical sort (natural sort would be better but requires natsort library)
        cpu_sorted_nodes = sorted(cpu_grouped["NodeList"].unique())
        gpu_sorted_nodes = sorted(gpu_grouped["NodeList"].unique())

    # Build response
    if color_by and color_by in cpu_grouped.columns:
        # Multi-series for stacked bar chart
        cpu_series = []
        top_groups = cpu_grouped.groupby(color_by)["CPUHours"].sum().nlargest(10).index.tolist()
        for group in top_groups:
            group_data = cpu_grouped[cpu_grouped[color_by] == group]
            data = []
            for node in cpu_sorted_nodes:
                node_value = group_data[group_data["NodeList"] == node]["CPUHours"].sum()
                data.append(float(node_value) if node_value > 0 else 0.0)
            cpu_series.append({
                "name": str(group),
                "data": data,
            })

        gpu_series = []
        top_groups = gpu_grouped.groupby(color_by)["GPUHours"].sum().nlargest(10).index.tolist()
        for group in top_groups:
            group_data = gpu_grouped[gpu_grouped[color_by] == group]
            data = []
            for node in gpu_sorted_nodes:
                node_value = group_data[group_data["NodeList"] == node]["GPUHours"].sum()
                data.append(float(node_value) if node_value > 0 else 0.0)
            gpu_series.append({
                "name": str(group),
                "data": data,
            })

        return {
            "cpu_usage": {
                "x": cpu_sorted_nodes,
                "series": cpu_series,
            },
            "gpu_usage": {
                "x": gpu_sorted_nodes,
                "series": gpu_series,
            },
        }
    else:
        # Single series
        cpu_data = []
        for node in cpu_sorted_nodes:
            value = cpu_grouped[cpu_grouped["NodeList"] == node]["CPUHours"].sum()
            cpu_data.append(float(value))

        gpu_data = []
        for node in gpu_sorted_nodes:
            value = gpu_grouped[gpu_grouped["NodeList"] == node]["GPUHours"].sum()
            gpu_data.append(float(value))

        return {
            "cpu_usage": {
                "x": cpu_sorted_nodes,
                "y": cpu_data,
            },
            "gpu_usage": {
                "x": gpu_sorted_nodes,
                "y": gpu_data,
            },
        }
