import pytest
from slurm_usage_history.tools import unpack_nodelist_string


def test_unpack_nodelist_with_range():
    """Test unpacking node list with range notation."""
    result = unpack_nodelist_string("gpu[08-09,11,14]")
    assert result == ["gpu08", "gpu09", "gpu11", "gpu14"]


def test_unpack_nodelist_with_single_digit():
    """Test that single digit nodes are zero-padded."""
    result = unpack_nodelist_string("gpu[5,6,7]")
    assert result == ["gpu05", "gpu06", "gpu07"]


def test_unpack_nodelist_with_two_digit():
    """Test that two digit nodes remain properly formatted."""
    result = unpack_nodelist_string("gpu[30,31,32]")
    assert result == ["gpu30", "gpu31", "gpu32"]


def test_unpack_nodelist_mixed():
    """Test mixed single and double digit nodes."""
    result = unpack_nodelist_string("gpu[5,10,30]")
    assert result == ["gpu05", "gpu10", "gpu30"]


def test_unpack_nodelist_single_node():
    """Test single node without brackets."""
    result = unpack_nodelist_string("gpu16")
    assert result == ["gpu16"]


def test_unpack_nodelist_none():
    """Test handling of None or empty input."""
    result = unpack_nodelist_string(None)
    assert result == []

    result = unpack_nodelist_string("None assigned")
    assert result == []


def test_unpack_nodelist_with_range_and_singles():
    """Test combination of ranges and single values."""
    result = unpack_nodelist_string("gpu[5-7,10,30-32]")
    assert result == ["gpu05", "gpu06", "gpu07", "gpu10", "gpu30", "gpu31", "gpu32"]
