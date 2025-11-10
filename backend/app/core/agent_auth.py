"""API key authentication for agent data uploads."""

from fastapi import Header, HTTPException, status

from ..db.clusters import get_cluster_db


async def verify_agent_api_key(x_api_key: str = Header(..., description="Agent API key")) -> str:
    """Verify agent API key from request header and return cluster name.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        The cluster name associated with the API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    cluster_db = get_cluster_db()
    cluster_name = cluster_db.verify_api_key(x_api_key)

    if not cluster_name:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return cluster_name
