import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from ..core.config import get_settings
from ..models.data_models import FilterRequest, HealthResponse, MetadataResponse

# Add parent directory to path to import the original datastore
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

try:
    from slurm_usage_history.app.datastore import PandasDataStore
except ImportError:
    PandasDataStore = None

router = APIRouter()
settings = get_settings()

# Global datastore instance
_datastore: Optional[PandasDataStore] = None


def get_datastore() -> PandasDataStore:
    """Get or initialize the datastore singleton."""
    global _datastore
    if _datastore is None:
        if PandasDataStore is None:
            raise HTTPException(status_code=500, detail="DataStore not available")
        _datastore = PandasDataStore(directory=settings.data_path)
        _datastore.load_data()
        _datastore.start_auto_refresh(interval=settings.auto_refresh_interval)
    return _datastore


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    try:
        datastore = get_datastore()
        hostnames = datastore.get_hostnames()
        return HealthResponse(
            status="healthy",
            timestamp=datetime.now(),
            data_loaded=len(hostnames) > 0,
            hostnames=hostnames,
        )
    except Exception:
        return HealthResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            data_loaded=False,
            hostnames=[],
        )


@router.get("/metadata", response_model=MetadataResponse)
async def get_metadata() -> MetadataResponse:
    """Get metadata for all clusters including available filters."""
    try:
        datastore = get_datastore()
        hostnames = datastore.get_hostnames()

        partitions = {}
        accounts = {}
        users = {}
        qos = {}
        states = {}
        date_ranges = {}

        for hostname in hostnames:
            partitions[hostname] = datastore.get_partitions(hostname)
            accounts[hostname] = datastore.get_accounts(hostname)
            users[hostname] = datastore.get_users(hostname)
            qos[hostname] = datastore.get_qos(hostname)
            states[hostname] = datastore.get_states(hostname)

            min_date, max_date = datastore.get_min_max_dates(hostname)
            date_ranges[hostname] = {"min_date": min_date or "", "max_date": max_date or ""}

        return MetadataResponse(
            hostnames=hostnames,
            partitions=partitions,
            accounts=accounts,
            users=users,
            qos=qos,
            states=states,
            date_ranges=date_ranges,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metadata: {str(e)}")


@router.post("/filter")
async def filter_data(request: FilterRequest) -> dict:
    """Filter data based on provided criteria and return aggregated results."""
    try:
        datastore = get_datastore()

        # Apply filters
        df = datastore.filter(
            hostname=request.hostname,
            start_date=request.start_date,
            end_date=request.end_date,
            partitions=request.partitions,
            accounts=request.accounts,
            users=request.users,
            qos=request.qos,
            states=request.states,
            complete_periods_only=request.complete_periods_only,
            period_type=request.period_type,
        )

        if df.empty:
            return {
                "total_jobs": 0,
                "total_cpu_hours": 0.0,
                "total_gpu_hours": 0.0,
                "total_users": 0,
                "data": [],
            }

        # Convert to records for JSON serialization
        records = df.to_dict(orient="records")

        # Calculate summary statistics
        summary = {
            "total_jobs": len(df),
            "total_cpu_hours": float(df["CPUHours"].sum()) if "CPUHours" in df.columns else 0.0,
            "total_gpu_hours": float(df["GPUHours"].sum()) if "GPUHours" in df.columns else 0.0,
            "total_users": df["User"].nunique() if "User" in df.columns else 0,
            "data": records,
        }

        return summary

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error filtering data: {str(e)}")


@router.get("/stats/{hostname}")
async def get_cluster_stats(
    hostname: str,
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
) -> dict:
    """Get statistics for a specific cluster."""
    try:
        datastore = get_datastore()

        if hostname not in datastore.get_hostnames():
            raise HTTPException(status_code=404, detail=f"Cluster {hostname} not found")

        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
        )

        if df.empty:
            return {
                "hostname": hostname,
                "total_jobs": 0,
                "total_cpu_hours": 0.0,
                "total_gpu_hours": 0.0,
                "total_users": 0,
                "partitions": [],
            }

        stats = {
            "hostname": hostname,
            "total_jobs": len(df),
            "total_cpu_hours": float(df["CPUHours"].sum()) if "CPUHours" in df.columns else 0.0,
            "total_gpu_hours": float(df["GPUHours"].sum()) if "GPUHours" in df.columns else 0.0,
            "total_users": df["User"].nunique() if "User" in df.columns else 0,
            "partitions": df["Partition"].unique().tolist() if "Partition" in df.columns else [],
        }

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching stats: {str(e)}")
