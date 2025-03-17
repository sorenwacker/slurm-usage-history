# /src/slurmo/app/app.py

import os
import dash
import dash_bootstrap_components as dbc
from dotenv import load_dotenv

from .callbacks import add_callbacks
from .DataStore import PandasDataStore as DataStore
from .layout import layout

from dash import DiskcacheManager
import diskcache

def create_dash_app(args, server=True, url_base_pathname="/"):
    """
    Create a Dash app that visualizes data from the specified Parquet files.
    """

    load_dotenv()

    # Initialize the Dash app
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,         
            '/assets/custom-styles.css'
    ],
        assets_folder='src/slurm_usage_history/assets',
        server=server,
        url_base_pathname=url_base_pathname,
    )

    cache = diskcache.Cache("./cache")
    background_callback_manager = DiskcacheManager(cache)

    # Create DataStore instance
    datastore = DataStore(directory=args.data_path)
    datastore.load_data()
    datastore.start_auto_refresh(interval=60)

    # Layout of the app
    app.layout = layout
    add_callbacks(app, datastore, cache, background_callback_manager)
    app.title = "Slurm Usage History Dashboard"
    
    server = app.server
    server.secret_key = os.getenv('FLASK_SECRET_KEY')

    return app
