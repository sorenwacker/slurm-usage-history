from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException

from ..core.auth import verify_api_key
from ..core.config import get_settings
from ..db.clusters import get_cluster_db
from ..models.data_models import DataIngestionRequest, DataIngestionResponse

router = APIRouter()
settings = get_settings()


@router.post("/ingest", response_model=DataIngestionResponse)
async def ingest_data(
    request: DataIngestionRequest,
    cluster_name: str = Depends(verify_api_key),
) -> DataIngestionResponse:
    """Ingest job data for a specific cluster.

    This endpoint accepts job records and stores them as parquet files.
    Requires API key authentication via X-API-Key header.

    Args:
        request: Data ingestion request containing hostname and job records
        api_key: Verified API key from header

    Returns:
        DataIngestionResponse with ingestion status
    """
    try:
        # Create directory structure for hostname
        data_dir = Path(settings.data_path) / request.hostname / "weekly-data"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Convert jobs to DataFrame
        jobs_data = [job.model_dump() for job in request.jobs]
        df = pd.DataFrame(jobs_data)

        # Convert datetime columns
        datetime_cols = ["Submit", "Start", "End"]
        for col in datetime_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])

        # Add derived columns for efficient querying
        if "Submit" in df.columns:
            df["SubmitDay"] = df["Submit"].dt.normalize()
            df["SubmitYearMonth"] = df["Submit"].dt.to_period("M").astype(str)
            df["SubmitYearWeek"] = (
                df["Submit"].dt.to_period("W").apply(lambda r: r.start_time).dt.strftime("%Y-%m-%d")
            )
            df["SubmitYear"] = df["Submit"].dt.year

        if "Start" in df.columns:
            df["StartDay"] = df["Start"].dt.normalize()

        # Calculate waiting time if both Submit and Start exist
        if "Submit" in df.columns and "Start" in df.columns:
            df["WaitingTime"] = (df["Start"] - df["Submit"]).dt.total_seconds() / 3600.0  # hours

        # Generate filename based on current timestamp
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jobs_{timestamp}.parquet"
        filepath = data_dir / filename

        # Save as parquet
        df.to_parquet(filepath, index=False, engine="pyarrow")

        # Update submission stats
        db = get_cluster_db()
        db.update_submission_stats(request.hostname, len(request.jobs))

        return DataIngestionResponse(
            success=True,
            message=f"Successfully ingested {len(request.jobs)} jobs for {request.hostname}",
            jobs_processed=len(request.jobs),
            hostname=request.hostname,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error ingesting data: {str(e)}",
        )
