"""Admin API endpoints for cluster and API key management."""

import logging
from datetime import timedelta
from pathlib import Path

import yaml
from fastapi import APIRouter, Depends, HTTPException, status

from ..core.admin_auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_admin,
    create_access_token,
    get_current_admin,
)
from ..core.config import get_settings
from ..db.clusters import get_cluster_db
from ..models.admin_models import (
    AdminRole,
    APIKeyRotateRequest,
    APIKeyRotateResponse,
    AdminLoginRequest,
    AdminLoginResponse,
    ClusterCreate,
    ClusterListResponse,
    ClusterResponse,
    ClusterUpdate,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def find_existing_data_directory(cluster_name: str) -> str | None:
    """Check if a data directory exists for this cluster (case-insensitive).

    Returns the actual directory name if found, None otherwise.
    """
    settings = get_settings()
    data_path = Path(settings.data_path)

    if not data_path.exists():
        return None

    # Check for exact match first
    exact_match = data_path / cluster_name
    if exact_match.exists() and exact_match.is_dir():
        return cluster_name

    # Check for case-insensitive match
    cluster_lower = cluster_name.lower()
    for item in data_path.iterdir():
        if item.is_dir() and item.name.lower() == cluster_lower:
            return item.name

    return None


def ensure_cluster_yaml_config(cluster_name: str, description: str | None = None,
                                contact_email: str | None = None, location: str | None = None) -> None:
    """Ensure cluster has configuration in clusters.yaml.

    Creates a default configuration if it doesn't exist.

    Args:
        cluster_name: Name of the cluster
        description: Optional description
        contact_email: Optional contact email
        location: Optional location
    """
    config_dir = Path(__file__).parent.parent.parent / "config"
    config_file = config_dir / "clusters.yaml"

    # Create config directory if it doesn't exist
    config_dir.mkdir(exist_ok=True)

    # Load existing config or create new
    if config_file.exists():
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f) or {}
    else:
        config = {"clusters": {}, "settings": {}}

    # Ensure structure exists
    if "clusters" not in config:
        config["clusters"] = {}
    if "settings" not in config:
        config["settings"] = {}

    # Check if cluster already exists
    if cluster_name in config["clusters"]:
        logger.info(f"Cluster {cluster_name} already exists in YAML config")
        return

    # Create default configuration
    config["clusters"][cluster_name] = {
        "display_name": cluster_name,
        "description": description or f"{cluster_name} Cluster",
        "metadata": {
            "location": location or "Unknown",
            "contact": contact_email or "admin@example.com"
        },
        "node_labels": {},
        "account_labels": {},
        "partition_labels": {}
    }

    # Ensure default settings exist
    if not config["settings"]:
        config["settings"] = {
            "default_node_type": "cpu",
            "case_sensitive": False,
            "auto_generate_labels": True
        }

    # Write back to file
    with open(config_file, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)

    logger.info(f"Created YAML configuration for cluster: {cluster_name}")


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(request: AdminLoginRequest):
    """Admin login endpoint.

    Authenticates admin user and returns JWT token.
    """
    username = authenticate_admin(request.username, request.password)

    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )

    # For password-based auth, default to superadmin role
    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        role=AdminRole.SUPERADMIN,
        email=None,
    )


@router.get("/clusters", response_model=ClusterListResponse)
async def list_clusters(admin: str = Depends(get_current_admin)):
    """List all clusters.

    Requires admin authentication.
    """
    db = get_cluster_db()
    clusters = db.get_all_clusters()

    cluster_responses = [
        ClusterResponse(
            id=c["id"],
            name=c["name"],
            description=c.get("description"),
            contact_email=c.get("contact_email"),
            location=c.get("location"),
            api_key=c["api_key"],
            api_key_created=c["api_key_created"],
            active=c["active"],
            created_at=c["created_at"],
            updated_at=c["updated_at"],
            last_submission=c.get("last_submission"),
            total_jobs_submitted=c.get("total_jobs_submitted", 0),
        )
        for c in clusters
    ]

    return ClusterListResponse(clusters=cluster_responses, total=len(cluster_responses))


@router.post("/clusters", response_model=ClusterResponse, status_code=status.HTTP_201_CREATED)
async def create_cluster(
    request: ClusterCreate,
    admin: str = Depends(get_current_admin),
):
    """Create a new cluster and generate API key.

    If a data directory already exists for this cluster (case-insensitive match),
    the cluster name will automatically match the existing directory's case.

    Requires admin authentication.
    """
    db = get_cluster_db()

    # Check for existing data directory and match its case
    existing_dir = find_existing_data_directory(request.name)
    cluster_name = existing_dir if existing_dir else request.name

    # Warn if case was changed
    if existing_dir and existing_dir != request.name:
        # Log the case correction
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Cluster name corrected from '{request.name}' to '{existing_dir}' "
            f"to match existing data directory"
        )

    try:
        cluster = db.create_cluster(
            name=cluster_name,
            description=request.description,
            contact_email=request.contact_email,
            location=request.location,
        )

        # Ensure YAML configuration is created for this cluster
        ensure_cluster_yaml_config(
            cluster_name=cluster_name,
            description=request.description,
            contact_email=request.contact_email,
            location=request.location,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return ClusterResponse(
        id=cluster["id"],
        name=cluster["name"],
        description=cluster.get("description"),
        contact_email=cluster.get("contact_email"),
        location=cluster.get("location"),
        api_key=cluster["api_key"],
        api_key_created=cluster["api_key_created"],
        active=cluster["active"],
        created_at=cluster["created_at"],
        updated_at=cluster["updated_at"],
        last_submission=None,
        total_jobs_submitted=0,
    )


@router.get("/clusters/{cluster_id}", response_model=ClusterResponse)
async def get_cluster(
    cluster_id: str,
    admin: str = Depends(get_current_admin),
):
    """Get cluster details by ID.

    Requires admin authentication.
    """
    db = get_cluster_db()
    cluster = db.get_cluster(cluster_id)

    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )

    return ClusterResponse(
        id=cluster["id"],
        name=cluster["name"],
        description=cluster.get("description"),
        contact_email=cluster.get("contact_email"),
        location=cluster.get("location"),
        api_key=cluster["api_key"],
        api_key_created=cluster["api_key_created"],
        active=cluster["active"],
        created_at=cluster["created_at"],
        updated_at=cluster["updated_at"],
        last_submission=cluster.get("last_submission"),
        total_jobs_submitted=cluster.get("total_jobs_submitted", 0),
    )


@router.patch("/clusters/{cluster_id}", response_model=ClusterResponse)
async def update_cluster(
    cluster_id: str,
    request: ClusterUpdate,
    admin: str = Depends(get_current_admin),
):
    """Update cluster information.

    Requires admin authentication.
    """
    db = get_cluster_db()

    cluster = db.update_cluster(
        cluster_id=cluster_id,
        description=request.description,
        contact_email=request.contact_email,
        location=request.location,
        active=request.active,
    )

    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )

    return ClusterResponse(
        id=cluster["id"],
        name=cluster["name"],
        description=cluster.get("description"),
        contact_email=cluster.get("contact_email"),
        location=cluster.get("location"),
        api_key=cluster["api_key"],
        api_key_created=cluster["api_key_created"],
        active=cluster["active"],
        created_at=cluster["created_at"],
        updated_at=cluster["updated_at"],
        last_submission=cluster.get("last_submission"),
        total_jobs_submitted=cluster.get("total_jobs_submitted", 0),
    )


@router.delete("/clusters/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cluster(
    cluster_id: str,
    admin: str = Depends(get_current_admin),
):
    """Delete a cluster.

    Requires admin authentication.
    """
    db = get_cluster_db()

    success = db.delete_cluster(cluster_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )

    return None


@router.post("/clusters/rotate-key", response_model=APIKeyRotateResponse)
async def rotate_api_key(
    request: APIKeyRotateRequest,
    admin: str = Depends(get_current_admin),
):
    """Rotate API key for a cluster.

    Generates a new API key and invalidates the old one.
    Requires admin authentication.
    """
    db = get_cluster_db()

    new_key = db.rotate_api_key(request.cluster_id)

    if not new_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cluster not found",
        )

    return APIKeyRotateResponse(
        cluster_id=request.cluster_id,
        new_api_key=new_key,
        message="API key rotated successfully. Update cluster configuration with new key.",
    )


@router.get("/admin-emails")
async def get_admin_emails(admin: str = Depends(get_current_admin)):
    """Get current admin and superadmin email lists.

    Requires admin authentication.
    """
    settings = get_settings()

    admin_emails = []
    superadmin_emails = []

    if settings.admin_emails:
        admin_emails = [email.strip() for email in settings.admin_emails.split(",") if email.strip()]

    if settings.superadmin_emails:
        superadmin_emails = [email.strip() for email in settings.superadmin_emails.split(",") if email.strip()]

    return {
        "admin_emails": admin_emails,
        "superadmin_emails": superadmin_emails,
    }


@router.post("/admin-emails")
async def update_admin_emails(
    admin_emails: list[str],
    superadmin_emails: list[str],
    admin: str = Depends(get_current_admin),
):
    """Update admin and superadmin email lists.

    Updates the .env file with new email lists.
    Requires admin authentication.
    """
    import os
    from pathlib import Path

    # Find .env file
    env_file = Path(".env")
    if not env_file.exists():
        # Try parent directory
        env_file = Path("../.env")
        if not env_file.exists():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=".env file not found",
            )

    # Read current .env content
    try:
        with open(env_file, 'r') as f:
            lines = f.readlines()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read .env file: {str(e)}",
        )

    # Update lines
    admin_emails_str = ",".join(admin_emails)
    superadmin_emails_str = ",".join(superadmin_emails)

    admin_emails_found = False
    superadmin_emails_found = False
    new_lines = []

    for line in lines:
        if line.startswith("ADMIN_EMAILS="):
            new_lines.append(f"ADMIN_EMAILS={admin_emails_str}\n")
            admin_emails_found = True
        elif line.startswith("SUPERADMIN_EMAILS="):
            new_lines.append(f"SUPERADMIN_EMAILS={superadmin_emails_str}\n")
            superadmin_emails_found = True
        else:
            new_lines.append(line)

    # Add if not found
    if not admin_emails_found:
        new_lines.append(f"ADMIN_EMAILS={admin_emails_str}\n")
    if not superadmin_emails_found:
        new_lines.append(f"SUPERADMIN_EMAILS={superadmin_emails_str}\n")

    # Write back
    try:
        with open(env_file, 'w') as f:
            f.writelines(new_lines)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write .env file: {str(e)}",
        )

    logger.info(f"Admin emails updated by {admin}: {len(admin_emails)} admins, {len(superadmin_emails)} superadmins")

    return {
        "status": "success",
        "message": "Admin emails updated successfully. Changes will take effect after backend restart.",
        "admin_emails": admin_emails,
        "superadmin_emails": superadmin_emails,
    }
