"""API endpoints for agent data uploads."""

import logging
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from ..core.agent_auth import verify_agent_api_key
from ..core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_data(
    cluster_name: Annotated[str, Form(description="Cluster name (e.g., DAIC)")],
    file: Annotated[UploadFile, File(description="Parquet file with SLURM data")],
    api_key: str = Depends(verify_agent_api_key),
) -> dict:
    """Upload SLURM data from agent.

    This endpoint allows agents to upload collected SLURM data via API instead of
    requiring shared filesystem access.

    Args:
        cluster_name: Name of the cluster (used for directory organization)
        file: Parquet file containing SLURM job data
        api_key: Verified API key from header

    Returns:
        Success message with file location

    Example:
        ```bash
        curl -X POST "http://localhost:8100/api/agent/upload" \\
          -H "X-API-Key: your-api-key-here" \\
          -F "cluster_name=DAIC" \\
          -F "file=@2024-W45.parquet"
        ```
    """
    settings = get_settings()

    # Validate file extension
    if not file.filename or not file.filename.endswith(".parquet"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a .parquet file",
        )

    # Validate cluster name (basic sanitation)
    if not cluster_name or not cluster_name.replace("_", "").replace("-", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid cluster name. Use alphanumeric characters, hyphens, or underscores only.",
        )

    # Create directory structure: DATA_PATH/cluster_name/weekly-data/
    cluster_dir = Path(settings.data_path) / cluster_name / "weekly-data"
    cluster_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = cluster_dir / file.filename
    try:
        contents = await file.read()
        with open(file_path, "wb") as f:
            f.write(contents)

        logger.info(
            f"Agent uploaded data: cluster={cluster_name}, "
            f"file={file.filename}, size={len(contents)} bytes"
        )

        return {
            "status": "success",
            "message": f"File uploaded successfully: {file.filename}",
            "cluster": cluster_name,
            "file": file.filename,
            "size": len(contents),
            "path": str(file_path.relative_to(settings.data_path)),
        }

    except Exception as e:
        logger.error(f"Failed to save uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}",
        ) from e


@router.get("/health")
async def health_check(api_key: str = Depends(verify_agent_api_key)) -> dict:
    """Health check endpoint for agents.

    Verifies that the agent can authenticate and the API is operational.

    Args:
        api_key: Verified API key from header

    Returns:
        Health status
    """
    settings = get_settings()
    data_path = Path(settings.data_path)

    return {
        "status": "healthy",
        "data_path": str(data_path),
        "data_path_exists": data_path.exists(),
        "data_path_writable": data_path.exists() and os.access(data_path, os.W_OK),
    }


# Import for health check
import os
