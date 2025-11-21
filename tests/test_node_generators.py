import pandas as pd
import pytest
from backend.app.services.charts.node_generators import generate_node_usage


def test_node_name_normalization():
    """Test that node names are properly normalized using cluster config."""
    df = pd.DataFrame({
        "NodeList": [["gpu5"], ["gpu30"], ["Gpu05"], ["GPU10"]],
        "CPUHours": [10.0, 20.0, 15.0, 25.0],
        "GPUHours": [5.0, 10.0, 8.0, 12.0],
    })

    result = generate_node_usage(df, cluster="DAIC")

    cpu_nodes = result["cpu_usage"]["x"]
    gpu_nodes = result["gpu_usage"]["x"]

    assert "gpu05" in cpu_nodes
    assert "gpu30" in cpu_nodes
    assert "gpu10" in cpu_nodes

    assert "gpu05" in gpu_nodes
    assert "gpu30" in gpu_nodes
    assert "gpu10" in gpu_nodes

    # Verify no duplicate nodes after normalization
    assert len(cpu_nodes) == len(set(cpu_nodes))
    assert len(gpu_nodes) == len(set(gpu_nodes))


def test_node_list_expansion():
    """Test that SLURM nodelist expansion works correctly."""
    df = pd.DataFrame({
        "NodeList": [["gpu05", "gpu06"], ["gpu30", "gpu31", "gpu32"]],
        "CPUHours": [10.0, 30.0],
        "GPUHours": [5.0, 15.0],
    })

    result = generate_node_usage(df, cluster="DAIC")

    cpu_nodes = result["cpu_usage"]["x"]

    # Check that all nodes are properly expanded and formatted
    assert "gpu05" in cpu_nodes
    assert "gpu06" in cpu_nodes
    assert "gpu30" in cpu_nodes
    assert "gpu31" in cpu_nodes
    assert "gpu32" in cpu_nodes


def test_node_name_without_cluster():
    """Test that nodes work even without cluster normalization."""
    df = pd.DataFrame({
        "NodeList": [["node1"], ["node2"]],
        "CPUHours": [10.0, 20.0],
        "GPUHours": [5.0, 10.0],
    })

    result = generate_node_usage(df, cluster=None)

    cpu_nodes = result["cpu_usage"]["x"]

    assert "node1" in cpu_nodes
    assert "node2" in cpu_nodes


def test_empty_nodelist():
    """Test handling of empty NodeList."""
    df = pd.DataFrame({
        "CPUHours": [10.0],
        "GPUHours": [5.0],
    })

    result = generate_node_usage(df, cluster="DAIC")

    assert result["cpu_usage"]["x"] == []
    assert result["gpu_usage"]["x"] == []


def test_already_expanded_nodes():
    """Test that pre-expanded node lists (from data ingestion) work correctly."""
    # This mimics what the data looks like after ingestion - already expanded
    df = pd.DataFrame({
        "NodeList": [["gpu06", "gpu07", "gpu08", "gpu10"], ["gpu30", "gpu31"]],
        "CPUHours": [40.0, 20.0],
        "GPUHours": [20.0, 10.0],
    })

    result = generate_node_usage(df, cluster="DAIC")

    cpu_nodes = result["cpu_usage"]["x"]

    # Should have all expanded nodes
    assert "gpu06" in cpu_nodes
    assert "gpu07" in cpu_nodes
    assert "gpu08" in cpu_nodes
    assert "gpu10" in cpu_nodes
    assert "gpu30" in cpu_nodes
    assert "gpu31" in cpu_nodes

    # Should not have any brackets in node names
    for node in cpu_nodes:
        assert "[" not in node
        assert "]" not in node
