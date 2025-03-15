# /src/slurmo/app/wsgi.py

import os

from dotenv import load_dotenv

from slurm_usage_history.app.app import create_dash_app

# Load environment variables from a .env file if present
load_dotenv()


def create_app():
    """
    Create and configure the Dash app for deployment.
    """
    # Retrieve data path from environment variables or set a default path
    data_path = os.getenv("SLURM_USAGE_HISTORY_DATA_PATH", "slurm-usage-history")

    # Create a simple args object to pass to create_dash_app
    class Args:
        pass

    args = Args()
    args.data_path = data_path

    # Create the Dash app
    dash_app = create_dash_app(args)

    # Return the underlying Flask server
    return dash_app.server


# This is the application object used by WSGI servers
app = create_app()
