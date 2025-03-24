# /src/slurm_usage_history/app/main.py

import argparse

from .app import create_dash_app


def parse_arguments():
    """
    Parse command line arguments.
    """
    parser = argparse.ArgumentParser(description="Run a Plotly Dash app.")
    parser.add_argument(
        "--data-path",
        default="data",
        type=str,
        help="Path to the directory containing Parquet data files.",
    )
    parser.add_argument(
        "--port", type=int, default=8050, help="Port to run the server on."
    )
    parser.add_argument(
        "--debug", action="store_true", help="Run the server in development mode."
    )
    return parser.parse_args()


def main():
    """
    Main function to run the Dash app.
    """
    # Parse command line arguments
    args = parse_arguments()

    # Create Dash app
    app = create_dash_app(args)

    # Run the server
    app.run(debug=args.debug, port=args.port)


if __name__ == "__main__":
    main()
