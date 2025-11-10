#!/usr/bin/env python3
"""
SLURM Usage History Exporter - Standalone cluster agent
Extracts SLURM job data and submits it to the dashboard API
"""

import argparse
import json
import logging
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('slurm-usage-history-exporter')


class SlurmDataExtractor:
    """Extracts job data from SLURM using sacct command"""

    SACCT_FORMAT = (
        "JobID,User,QOS,Account,Partition,Submit,Start,End,State,"
        "Elapsed,AveDiskRead,AveDiskWrite,AveCPU,MaxRSS,AllocCPUS,"
        "TotalCPU,NodeList,AllocTRES,Cluster"
    )

    def __init__(self, cluster_name: Optional[str] = None):
        self.cluster_name = cluster_name or self._get_cluster_name()
        logger.info(f"Initialized extractor for cluster: {self.cluster_name}")

    def _get_cluster_name(self) -> str:
        """Auto-detect cluster name from SLURM or hostname"""
        try:
            result = subprocess.run(
                ['scontrol', 'show', 'config'],
                capture_output=True,
                text=True,
                timeout=10
            )
            for line in result.stdout.split('\n'):
                if line.startswith('ClusterName'):
                    return line.split('=')[1].strip()
        except Exception as e:
            logger.warning(f"Could not detect cluster name from SLURM: {e}")

        # Fallback to hostname
        import socket
        return socket.gethostname().split('.')[0]

    def extract_jobs(
        self,
        start_date: str,
        end_date: str,
        all_users: bool = True
    ) -> pd.DataFrame:
        """
        Extract jobs from SLURM using sacct

        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            all_users: If True, fetch data for all users (requires admin)

        Returns:
            DataFrame with job records
        """
        logger.info(f"Extracting jobs from {start_date} to {end_date}")

        cmd = [
            'sacct',
            f'--format={self.SACCT_FORMAT}',
            '--parsable2',
            f'--starttime={start_date}',
            f'--endtime={end_date}'
        ]

        if all_users:
            cmd.append('--allusers')

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
                check=True
            )

            if not result.stdout.strip():
                logger.warning("No data returned from sacct")
                return pd.DataFrame()

            # Parse the pipe-separated output
            lines = result.stdout.strip().split('\n')
            headers = lines[0].split('|')
            data = [line.split('|') for line in lines[1:]]

            df = pd.DataFrame(data, columns=headers)
            logger.info(f"Extracted {len(df)} raw job records")

            # Filter out unwanted states
            df = df[~df['State'].isin(['RUNNING', 'Unknown', 'PENDING'])]
            logger.info(f"Filtered to {len(df)} completed job records")

            return df

        except subprocess.TimeoutExpired:
            logger.error("sacct command timed out")
            raise
        except subprocess.CalledProcessError as e:
            logger.error(f"sacct command failed: {e.stderr}")
            raise
        except Exception as e:
            logger.error(f"Error extracting jobs: {e}")
            raise

    def format_jobs(self, df: pd.DataFrame) -> List[Dict]:
        """
        Format raw SLURM data into dashboard API format

        Args:
            df: Raw DataFrame from sacct

        Returns:
            List of job dictionaries ready for API submission
        """
        if df.empty:
            return []

        logger.info("Formatting job data")

        # Parse AllocTRES to extract CPU, GPU, memory info
        def parse_alloc_tres(tres_str):
            """Parse AllocTRES string like 'cpu=4,mem=16G,gres/gpu=2'"""
            result = {'cpu': 0, 'gpu': 0, 'mem': 0}
            if pd.isna(tres_str) or not tres_str:
                return result

            for item in tres_str.split(','):
                if '=' in item:
                    key, val = item.split('=', 1)
                    key = key.strip().lower()

                    if 'cpu' in key:
                        result['cpu'] = int(val)
                    elif 'gpu' in key:
                        result['gpu'] = int(val)
                    elif 'mem' in key:
                        # Convert memory to MB
                        val_str = val.upper()
                        if 'G' in val_str:
                            result['mem'] = int(float(val_str.replace('G', '')) * 1024)
                        elif 'M' in val_str:
                            result['mem'] = int(float(val_str.replace('M', '')))

            return result

        # Parse elapsed time to hours
        def elapsed_to_hours(elapsed_str):
            """Convert SLURM elapsed time format to hours"""
            if pd.isna(elapsed_str) or not elapsed_str:
                return 0.0

            try:
                # Format can be: days-HH:MM:SS, HH:MM:SS, MM:SS
                total_seconds = 0

                if '-' in elapsed_str:
                    days, time_part = elapsed_str.split('-')
                    total_seconds += int(days) * 86400
                else:
                    time_part = elapsed_str

                parts = time_part.split(':')
                if len(parts) == 3:
                    hours, mins, secs = parts
                    total_seconds += int(hours) * 3600 + int(mins) * 60 + float(secs)
                elif len(parts) == 2:
                    mins, secs = parts
                    total_seconds += int(mins) * 60 + float(secs)

                return total_seconds / 3600.0
            except Exception as e:
                logger.warning(f"Could not parse elapsed time '{elapsed_str}': {e}")
                return 0.0

        # Apply formatting
        df['AllocTRESParsed'] = df['AllocTRES'].apply(parse_alloc_tres)
        df['AllocCPUS'] = df['AllocTRESParsed'].apply(lambda x: x['cpu'] if x['cpu'] > 0 else 0)
        df['AllocGPUS'] = df['AllocTRESParsed'].apply(lambda x: x['gpu'])
        df['ElapsedHours'] = df['Elapsed'].apply(elapsed_to_hours)

        # Calculate resource-hours
        df['CPUHours'] = df['ElapsedHours'] * df['AllocCPUS']
        df['GPUHours'] = df['ElapsedHours'] * df['AllocGPUS']

        # Count nodes
        def count_nodes(nodelist):
            if pd.isna(nodelist) or not nodelist:
                return 0
            # Simple count - could be improved for range notation
            return len([n for n in nodelist.split(',') if n.strip()])

        df['AllocNodes'] = df['NodeList'].apply(count_nodes)

        # Convert to list of dicts
        jobs = []
        for _, row in df.iterrows():
            job = {
                'JobID': str(row['JobID']),
                'User': str(row['User']),
                'Account': str(row['Account']) if pd.notna(row['Account']) else 'unknown',
                'Partition': str(row['Partition']) if pd.notna(row['Partition']) else 'unknown',
                'State': str(row['State']),
                'QOS': str(row['QOS']) if pd.notna(row['QOS']) else None,
                'Submit': str(row['Submit']),
                'Start': str(row['Start']) if pd.notna(row['Start']) else None,
                'End': str(row['End']) if pd.notna(row['End']) else None,
                'CPUHours': float(row['CPUHours']),
                'GPUHours': float(row['GPUHours']),
                'AllocCPUS': int(row['AllocCPUS']),
                'AllocGPUS': int(row['AllocGPUS']),
                'AllocNodes': int(row['AllocNodes']),
                'NodeList': str(row['NodeList']) if pd.notna(row['NodeList']) else None,
            }
            jobs.append(job)

        logger.info(f"Formatted {len(jobs)} jobs for submission")
        return jobs


class DashboardClient:
    """Client for submitting data to the dashboard API"""

    def __init__(self, api_url: str, api_key: str, timeout: int = 30):
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.timeout = timeout

        # Configure session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        logger.info(f"Initialized dashboard client for {api_url}")

    def submit_jobs(self, hostname: str, jobs: List[Dict]) -> Dict:
        """
        Submit job data to the dashboard API

        Args:
            hostname: Cluster hostname
            jobs: List of job dictionaries

        Returns:
            API response dictionary
        """
        if not jobs:
            logger.warning("No jobs to submit")
            return {'success': False, 'message': 'No jobs to submit'}

        endpoint = f"{self.api_url}/api/data/ingest"
        headers = {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        payload = {
            'hostname': hostname,
            'jobs': jobs
        }

        logger.info(f"Submitting {len(jobs)} jobs to {endpoint}")

        try:
            response = self.session.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()

            result = response.json()
            logger.info(f"Successfully submitted: {result.get('message', 'OK')}")
            return result

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            logger.error(f"Response: {e.response.text}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error: {e}")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Request timed out: {e}")
            raise
        except Exception as e:
            logger.error(f"Error submitting jobs: {e}")
            raise

    def check_health(self) -> Dict:
        """Check dashboard health status"""
        endpoint = f"{self.api_url}/api/dashboard/health"
        try:
            response = self.session.get(endpoint, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise


def load_config(config_path: Path) -> Dict:
    """Load configuration from JSON file"""
    logger.info(f"Loading configuration from {config_path}")

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        config = json.load(f)

    # Validate required fields
    required = ['api_url', 'api_key']
    for field in required:
        if field not in config:
            raise ValueError(f"Missing required configuration field: {field}")

    return config


def main():
    parser = argparse.ArgumentParser(
        description='Extract SLURM job data and submit to dashboard'
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('/etc/slurm-usage-history-exporter/config.json'),
        help='Path to configuration file (default: /etc/slurm-usage-history-exporter/config.json)'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        help='Start date in YYYY-MM-DD format (default: 7 days ago)'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        help='End date in YYYY-MM-DD format (default: today)'
    )
    parser.add_argument(
        '--cluster-name',
        type=str,
        help='Override cluster name (auto-detected if not provided)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Extract and format data but do not submit to API'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Calculate date range
    end_date = args.end_date or datetime.now().strftime('%Y-%m-%d')
    start_date = args.start_date or (
        datetime.now() - timedelta(days=7)
    ).strftime('%Y-%m-%d')

    logger.info(f"Processing date range: {start_date} to {end_date}")

    try:
        # Load configuration
        config = load_config(args.config)

        # Initialize extractor
        extractor = SlurmDataExtractor(cluster_name=args.cluster_name)

        # Extract jobs
        df = extractor.extract_jobs(start_date, end_date)

        if df.empty:
            logger.warning("No jobs found in specified date range")
            return 0

        # Format jobs
        jobs = extractor.format_jobs(df)

        if args.dry_run:
            logger.info("DRY RUN: Would submit the following:")
            logger.info(f"  Cluster: {extractor.cluster_name}")
            logger.info(f"  Jobs: {len(jobs)}")
            logger.info(f"  Total CPU-hours: {sum(j['CPUHours'] for j in jobs):.2f}")
            logger.info(f"  Total GPU-hours: {sum(j['GPUHours'] for j in jobs):.2f}")

            # Show sample of first job
            if jobs:
                logger.info(f"  Sample job: {json.dumps(jobs[0], indent=2)}")

            return 0

        # Submit to dashboard
        client = DashboardClient(
            api_url=config['api_url'],
            api_key=config['api_key'],
            timeout=config.get('timeout', 30)
        )

        # Check health first
        health = client.check_health()
        logger.info(f"Dashboard health: {health.get('status', 'unknown')}")

        # Submit jobs
        result = client.submit_jobs(extractor.cluster_name, jobs)

        logger.info(f"Submission complete: {result}")
        return 0

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())
