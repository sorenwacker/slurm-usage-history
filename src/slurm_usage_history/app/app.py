# /src/slurmo/app/app.py

import dash
import dash_bootstrap_components as dbc

from .callbacks import add_callbacks
from .DataStore import PandasDataStore as DataStore
from .layout import layout


def create_dash_app(args, server=True, url_base_pathname="/"):
    """
    Create a Dash app that visualizes data from the specified Parquet files.
    """

    # Initialize the Dash app
    app = dash.Dash(
        __name__,
        external_stylesheets=[
            dbc.themes.BOOTSTRAP,         
            '/assets/custom-styles.css'
    ],
        server=server,
        url_base_pathname=url_base_pathname,
    )

    # Create DataStore instance
    datastore = DataStore(directory=args.data_path)
    datastore.load_data()
    datastore.start_auto_refresh(interval=60)

    # Layout of the app
    app.layout = layout
    add_callbacks(app, datastore)
    app.title = "Slurm Usage History Dashboard"
    return app
