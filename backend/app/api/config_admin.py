"""Configuration admin API endpoints for YAML cluster configuration management."""
from pathlib import Path
from typing import Any, Dict

import yaml
from fastapi import APIRouter, HTTPException

from ..config import get_cluster_config, reload_cluster_config

router = APIRouter()


def get_config_path() -> Path:
    """Get path to configuration file."""
    config = get_cluster_config()
    return config.config_path


@router.get("/config")
async def get_configuration():
    """Get current cluster configuration.

    Returns the complete YAML configuration including all clusters,
    node labels, account labels, and settings.
    """
    try:
        config = get_cluster_config()

        return {
            "clusters": config.config.get("clusters", {}),
            "settings": config.config.get("settings", {}),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading configuration: {str(e)}")


@router.get("/config/{cluster_name}")
async def get_cluster_configuration(cluster_name: str):
    """Get configuration for a specific cluster.

    Args:
        cluster_name: Name of the cluster (e.g., "DAIC")

    Returns:
        Cluster configuration including labels and metadata
    """
    try:
        config = get_cluster_config()
        clusters = config.config.get("clusters", {})

        if cluster_name not in clusters:
            raise HTTPException(status_code=404, detail=f"Cluster {cluster_name} not found")

        return clusters[cluster_name]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading cluster configuration: {str(e)}")


@router.post("/config/{cluster_name}/auto-generate")
async def auto_generate_cluster_configuration(cluster_name: str):
    """Auto-generate configuration for a cluster based on existing data.

    This endpoint analyzes the data for a cluster and automatically generates:
    - Node labels from unique node names
    - Account labels from unique account names
    - Partition labels from unique partition names

    Args:
        cluster_name: Name of the cluster

    Returns:
        Generated configuration with stats
    """
    try:
        from .dashboard import get_datastore

        datastore = get_datastore()

        # Check if cluster exists in data
        if cluster_name not in datastore.get_hostnames():
            raise HTTPException(status_code=404, detail=f"No data found for cluster {cluster_name}")

        # Get all data for the cluster
        df = datastore.filter(hostname=cluster_name)

        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for cluster {cluster_name}")

        # Generate node labels from unique node names
        node_labels = {}
        if "NodeList" in df.columns:
            unique_nodes = df["NodeList"].dropna().unique()
            for node in sorted(unique_nodes):
                if node and isinstance(node, str):
                    # Try to detect node type from name
                    node_type = "cpu"
                    if "gpu" in node.lower():
                        node_type = "gpu"
                    elif "login" in node.lower():
                        node_type = "login"
                    elif "storage" in node.lower() or "nas" in node.lower():
                        node_type = "storage"

                    node_labels[node] = {
                        "synonyms": [],
                        "type": node_type,
                        "description": f"{node_type.upper()} Node {node}",
                    }

        # Generate account labels
        account_labels = {}
        if "Account" in df.columns:
            unique_accounts = df["Account"].dropna().unique()
            for account in sorted(unique_accounts):
                if account and isinstance(account, str):
                    account_labels[account] = {
                        "display_name": account,
                        "short_name": account.split("-")[-1].upper() if "-" in account else account,
                    }

        # Generate partition labels
        partition_labels = {}
        if "Partition" in df.columns:
            unique_partitions = df["Partition"].dropna().unique()
            for partition in sorted(unique_partitions):
                if partition and isinstance(partition, str):
                    partition_labels[partition] = {
                        "display_name": f"{partition.capitalize()} Partition",
                        "description": f"{partition} partition",
                    }

        # Create cluster configuration
        cluster_config = {
            "display_name": f"{cluster_name} Cluster",
            "description": f"Auto-generated configuration for {cluster_name}",
            "metadata": {
                "location": "Unknown",
                "owner": "Unknown",
                "contact": "unknown@example.com",
            },
            "node_labels": node_labels,
            "account_labels": account_labels,
            "partition_labels": partition_labels,
        }

        # Load current configuration
        config_path = get_config_path()
        if config_path.exists():
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}
        else:
            config_data = {"clusters": {}, "settings": {}}

        # Ensure clusters key exists
        if "clusters" not in config_data:
            config_data["clusters"] = {}

        # Check if cluster already exists
        if cluster_name in config_data["clusters"]:
            # Merge with existing configuration (don't overwrite existing labels)
            existing = config_data["clusters"][cluster_name]

            # Merge node labels (add new ones, keep existing)
            if "node_labels" in existing:
                for node, config in node_labels.items():
                    if node not in existing["node_labels"]:
                        existing["node_labels"][node] = config
            else:
                existing["node_labels"] = node_labels

            # Merge account labels
            if "account_labels" in existing:
                for account, config in account_labels.items():
                    if account not in existing["account_labels"]:
                        existing["account_labels"][account] = config
            else:
                existing["account_labels"] = account_labels

            # Merge partition labels
            if "partition_labels" in existing:
                for partition, config in partition_labels.items():
                    if partition not in existing["partition_labels"]:
                        existing["partition_labels"][partition] = config
            else:
                existing["partition_labels"] = partition_labels

            cluster_config = existing
        else:
            # Add new cluster configuration
            config_data["clusters"][cluster_name] = cluster_config

        # Write back to file
        with open(config_path, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

        # Reload configuration
        reload_cluster_config()

        return {
            "status": "success",
            "message": f"Configuration auto-generated for cluster {cluster_name}",
            "configuration": cluster_config,
            "stats": {
                "nodes": len(node_labels),
                "accounts": len(account_labels),
                "partitions": len(partition_labels),
            },
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error auto-generating configuration: {str(e)}"
        )


@router.post("/config/reload")
async def reload_configuration():
    """Reload configuration from file.

    Useful after manual edits to the YAML file.

    Returns:
        Success message with loaded clusters
    """
    try:
        config = reload_cluster_config()
        clusters = config.get_all_clusters()

        return {
            "status": "success",
            "message": "Configuration reloaded successfully",
            "clusters": clusters,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reloading configuration: {str(e)}")


@router.put("/config")
async def update_configuration(config_data: Dict[str, Any]):
    """Update the entire cluster configuration.

    This endpoint allows you to update the complete YAML configuration.
    The configuration will be validated and written to the file.

    Args:
        config_data: Complete configuration object with clusters and settings

    Returns:
        Success message
    """
    try:
        # Validate that we have the required structure
        if "clusters" not in config_data:
            raise HTTPException(status_code=400, detail="Configuration must include 'clusters' key")

        # Get config path
        config_path = get_config_path()

        # Create backup of existing config
        if config_path.exists():
            backup_path = config_path.with_suffix(".yaml.backup")
            import shutil
            shutil.copy2(config_path, backup_path)

        # Write new configuration
        with open(config_path, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        # Reload configuration to validate
        reload_cluster_config()

        return {
            "status": "success",
            "message": "Configuration updated successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        # If there was an error, try to restore from backup
        config_path = get_config_path()
        backup_path = config_path.with_suffix(".yaml.backup")
        if backup_path.exists():
            import shutil
            shutil.copy2(backup_path, config_path)
            reload_cluster_config()

        raise HTTPException(status_code=500, detail=f"Error updating configuration: {str(e)}")


@router.put("/config/{cluster_name}")
async def update_cluster_configuration(cluster_name: str, cluster_data: Dict[str, Any]):
    """Update configuration for a specific cluster.

    This endpoint allows you to update the configuration for a single cluster.
    More convenient than updating the entire configuration file.

    Args:
        cluster_name: Name of the cluster (e.g., "DAIC")
        cluster_data: Cluster configuration object

    Returns:
        Success message
    """
    try:
        # Get config path
        config_path = get_config_path()

        # Load current configuration
        if config_path.exists():
            with open(config_path, "r") as f:
                config_data = yaml.safe_load(f) or {}
        else:
            config_data = {"clusters": {}, "settings": {}}

        # Ensure clusters key exists
        if "clusters" not in config_data:
            config_data["clusters"] = {}

        # Create backup
        backup_path = config_path.with_suffix(".yaml.backup")
        if config_path.exists():
            import shutil
            shutil.copy2(config_path, backup_path)

        # Update the specific cluster
        config_data["clusters"][cluster_name] = cluster_data

        # Write updated configuration
        with open(config_path, "w") as f:
            yaml.dump(config_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

        # Reload configuration to validate
        reload_cluster_config()

        return {
            "status": "success",
            "message": f"Configuration updated successfully for cluster {cluster_name}",
        }
    except Exception as e:
        # If there was an error, try to restore from backup
        config_path = get_config_path()
        backup_path = config_path.with_suffix(".yaml.backup")
        if backup_path.exists():
            import shutil
            shutil.copy2(backup_path, config_path)
            reload_cluster_config()

        raise HTTPException(status_code=500, detail=f"Error updating cluster configuration: {str(e)}")
