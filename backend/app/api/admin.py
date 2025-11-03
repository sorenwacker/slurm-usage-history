"""Admin API endpoints for cluster and API key management."""

from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status

from ..core.admin_auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_admin,
    create_access_token,
    get_current_admin,
)
from ..db.clusters import get_cluster_db
from ..models.admin_models import (
    APIKeyRotateRequest,
    APIKeyRotateResponse,
    AdminLoginRequest,
    AdminLoginResponse,
    ClusterCreate,
    ClusterListResponse,
    ClusterResponse,
    ClusterUpdate,
)

router = APIRouter()


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

    return AdminLoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
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

    Requires admin authentication.
    """
    db = get_cluster_db()

    try:
        cluster = db.create_cluster(
            name=request.name,
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
