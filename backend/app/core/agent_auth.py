"""API key authentication for agent data uploads."""

from fastapi import Header, HTTPException, status

from .config import get_settings


async def verify_agent_api_key(x_api_key: str = Header(..., description="Agent API key")) -> str:
    """Verify agent API key from request header.

    Args:
        x_api_key: API key from X-API-Key header

    Returns:
        The verified API key

    Raises:
        HTTPException: If API key is invalid or missing
    """
    settings = get_settings()
    valid_keys = settings.get_api_keys()

    if not valid_keys:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent API not configured. Set AGENT_API_KEYS in environment.",
        )

    if x_api_key not in valid_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )

    return x_api_key
