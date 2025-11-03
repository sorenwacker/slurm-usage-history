"""Simple JSON-based database for cluster management."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from ..core.admin_auth import generate_api_key


class ClusterDB:
    """Simple JSON-based database for storing cluster information."""

    def __init__(self, db_path: str = "data/clusters.json"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Create database file if it doesn't exist."""
        if not self.db_path.exists():
            self._write_db({"clusters": {}, "stats": {}})

    def _read_db(self) -> dict:
        """Read database from file."""
        try:
            with open(self.db_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"clusters": {}, "stats": {}}

    def _write_db(self, data: dict):
        """Write database to file."""
        with open(self.db_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def create_cluster(
        self,
        name: str,
        description: Optional[str] = None,
        contact_email: Optional[str] = None,
        location: Optional[str] = None,
    ) -> dict:
        """Create a new cluster and generate API key."""
        db = self._read_db()

        # Check if cluster name already exists
        for cluster in db["clusters"].values():
            if cluster["name"] == name:
                raise ValueError(f"Cluster with name '{name}' already exists")

        cluster_id = str(uuid4())
        api_key = generate_api_key()
        now = datetime.utcnow()

        cluster = {
            "id": cluster_id,
            "name": name,
            "description": description,
            "contact_email": contact_email,
            "location": location,
            "api_key": api_key,
            "api_key_created": now.isoformat(),
            "active": True,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        db["clusters"][cluster_id] = cluster

        # Initialize stats
        db["stats"][cluster_id] = {
            "last_submission": None,
            "total_jobs_submitted": 0,
        }

        self._write_db(db)
        return cluster

    def get_cluster(self, cluster_id: str) -> Optional[dict]:
        """Get cluster by ID."""
        db = self._read_db()
        cluster = db["clusters"].get(cluster_id)

        if cluster:
            # Merge with stats
            stats = db["stats"].get(cluster_id, {})
            cluster["last_submission"] = stats.get("last_submission")
            cluster["total_jobs_submitted"] = stats.get("total_jobs_submitted", 0)

        return cluster

    def get_cluster_by_name(self, name: str) -> Optional[dict]:
        """Get cluster by name."""
        db = self._read_db()
        for cluster in db["clusters"].values():
            if cluster["name"] == name:
                cluster_id = cluster["id"]
                stats = db["stats"].get(cluster_id, {})
                cluster["last_submission"] = stats.get("last_submission")
                cluster["total_jobs_submitted"] = stats.get("total_jobs_submitted", 0)
                return cluster
        return None

    def get_all_clusters(self) -> List[dict]:
        """Get all clusters."""
        db = self._read_db()
        clusters = []

        for cluster_id, cluster in db["clusters"].items():
            stats = db["stats"].get(cluster_id, {})
            cluster["last_submission"] = stats.get("last_submission")
            cluster["total_jobs_submitted"] = stats.get("total_jobs_submitted", 0)
            clusters.append(cluster)

        return sorted(clusters, key=lambda x: x["created_at"], reverse=True)

    def update_cluster(
        self,
        cluster_id: str,
        description: Optional[str] = None,
        contact_email: Optional[str] = None,
        location: Optional[str] = None,
        active: Optional[bool] = None,
    ) -> Optional[dict]:
        """Update cluster information."""
        db = self._read_db()

        if cluster_id not in db["clusters"]:
            return None

        cluster = db["clusters"][cluster_id]

        if description is not None:
            cluster["description"] = description
        if contact_email is not None:
            cluster["contact_email"] = contact_email
        if location is not None:
            cluster["location"] = location
        if active is not None:
            cluster["active"] = active

        cluster["updated_at"] = datetime.utcnow().isoformat()

        self._write_db(db)
        return self.get_cluster(cluster_id)

    def delete_cluster(self, cluster_id: str) -> bool:
        """Delete a cluster."""
        db = self._read_db()

        if cluster_id not in db["clusters"]:
            return False

        del db["clusters"][cluster_id]
        if cluster_id in db["stats"]:
            del db["stats"][cluster_id]

        self._write_db(db)
        return True

    def rotate_api_key(self, cluster_id: str) -> Optional[str]:
        """Generate a new API key for a cluster."""
        db = self._read_db()

        if cluster_id not in db["clusters"]:
            return None

        new_api_key = generate_api_key()
        db["clusters"][cluster_id]["api_key"] = new_api_key
        db["clusters"][cluster_id]["api_key_created"] = datetime.utcnow().isoformat()
        db["clusters"][cluster_id]["updated_at"] = datetime.utcnow().isoformat()

        self._write_db(db)
        return new_api_key

    def verify_api_key(self, api_key: str) -> Optional[str]:
        """Verify API key and return cluster name if valid."""
        db = self._read_db()

        for cluster in db["clusters"].values():
            if cluster["api_key"] == api_key and cluster["active"]:
                return cluster["name"]

        return None

    def get_all_active_api_keys(self) -> List[str]:
        """Get all active API keys."""
        db = self._read_db()
        return [
            cluster["api_key"]
            for cluster in db["clusters"].values()
            if cluster["active"]
        ]

    def update_submission_stats(self, cluster_name: str, job_count: int):
        """Update submission statistics for a cluster."""
        db = self._read_db()

        # Find cluster by name
        cluster_id = None
        for cid, cluster in db["clusters"].items():
            if cluster["name"] == cluster_name:
                cluster_id = cid
                break

        if not cluster_id:
            return

        if cluster_id not in db["stats"]:
            db["stats"][cluster_id] = {
                "last_submission": None,
                "total_jobs_submitted": 0,
            }

        db["stats"][cluster_id]["last_submission"] = datetime.utcnow().isoformat()
        db["stats"][cluster_id]["total_jobs_submitted"] += job_count

        self._write_db(db)


# Singleton instance
_cluster_db = None


def get_cluster_db() -> ClusterDB:
    """Get singleton instance of cluster database."""
    global _cluster_db
    if _cluster_db is None:
        _cluster_db = ClusterDB()
    return _cluster_db
