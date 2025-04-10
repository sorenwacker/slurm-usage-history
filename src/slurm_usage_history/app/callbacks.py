import os
import time
import getpass
import logging
from datetime import date

import dash
import pandas as pd
import plotly.express as px
from dash import Input, Output, State, dcc
from dateutil.relativedelta import relativedelta

from ..app.node_config import NodeConfiguration
from ..tools import categorize_time_series, get_time_column, natural_sort_key

node_config = NodeConfiguration()
logger = logging.getLogger(__name__)

COLORS = {
    None: None,
    "User": px.colors.qualitative.Dark24,
    "Account": px.colors.qualitative.Alphabet,
    "Partition": px.colors.qualitative.Prism,
    "State": px.colors.qualitative.Set1,
    "QOS": px.colors.qualitative.Set2,
}

def initialize_session_data(session_id=None):
    return {
        'category_orders': {
            "User": None,
            "Account": None,
            "Partition": None,
            "State": None,
            "QOS": None,
        },
        'color_mappings': {
            "User": {},
            "Account": {},
            "Partition": {},
            "State": {},
            "QOS": {},
        }
    }

def init_app(app):
    server = app.server
    server.secret_key = os.getenv('FLASK_SECRET_KEY')

def ensure_consistent_categories_and_colors(df, category_name, color_sequence, session_data):
    if category_name not in df.columns or session_data is None:
        return [], {}

    if 'color_mappings' not in session_data:
        session_data['color_mappings'] = {}
    if category_name not in session_data['color_mappings']:
        session_data['color_mappings'][category_name] = {}

    color_mappings = session_data['color_mappings'][category_name]

    current_values = df[category_name].unique().tolist()

    for value in current_values:
        if value not in color_mappings:
            color_idx = len(color_mappings) % len(color_sequence)
            color_mappings[value] = color_sequence[color_idx]

    color_map = {value: color_mappings[value] for value in current_values}

    value_counts = df[category_name].value_counts()
    category_order = value_counts.index.tolist()

    if 'category_orders' not in session_data:
        session_data['category_orders'] = {}
    session_data['category_orders'][category_name] = category_order

    return category_order, color_map

def ensure_consistent_categories(df, category_name, value_column=None, session_data=None):
    if session_data is None or 'category_orders' not in session_data or category_name not in session_data['category_orders'] or session_data['category_orders'][category_name] is None or category_name not in df.columns:
        return df

    all_category_values = session_data['category_orders'][category_name]
    existing_categories = set(df[category_name].unique())
    missing_categories = set(all_category_values) - existing_categories

    if missing_categories:
        placeholder_rows = []
        for cat_value in missing_categories:
            new_row = {category_name: cat_value}
            if value_column and value_column in df.columns:
                new_row[value_column] = 0
            for col in df.columns:
                if col != category_name and col not in new_row:
                    if df[col].dtype == "object":
                        new_row[col] = ""
                    else:
                        new_row[col] = 0
            placeholder_rows.append(new_row)
        if placeholder_rows:
            placeholder_df = pd.DataFrame(placeholder_rows)
            return pd.concat([df, placeholder_df], ignore_index=True)
    return df

def list_to_options(list_of_strings):
    return [{"label": x, "value": x} for x in list_of_strings]

def add_callbacks(app, datastore, cache, background_callback_manager):
    
    @app.callback(
        Output("account-formatter-store", "data"),
        Input("account-format-segments", "value"),
        prevent_initial_call=True
    )
    def update_account_format(segments_to_keep):
        if segments_to_keep is not None:
            return {"updated_at": time.time(), "segments": segments_to_keep}
        return dash.no_update
    
    @app.callback(
        Output("session-store", "data"),
        Input("interval", "n_intervals"),
        Input("account-formatter-store", "data"),
        State("session-store", "data")
    )
    def update_session_data(n_intervals, account_format, current_data):
        if current_data is None:
            current_data = initialize_session_data()
        
        # If account format has changed, reset the category data
        if account_format is not None:
            current_data['category_orders'] = {
                "User": None,
                "Account": None,
                "Partition": None,
                "State": None,
                "QOS": None,
            }
            current_data['color_mappings'] = {
                "User": {},
                "Account": {},
                "Partition": {},
                "State": {},
                "QOS": {},
            }
            
            # Only update the formatter if we have segments information
            if "segments" in account_format:
                current_data['formatter'] = {"segments": account_format.get("segments", 3)}

        return current_data

    @app.callback(
        Output("accounts_dropdown", "options"),
        Input("hostname_dropdown", "value"),
    )
    def update_accounts_dropdown(hostname):
        if not hostname:
            return []
        accounts = datastore.get_accounts(hostname)
        return [{"label": a, "value": a} for a in accounts]

    @app.callback(
        Output("color_by_dropdown", "options"),
        Output("color_by_dropdown", "value"),
        Input("admin-mode-switch", "value"),
        Input("color_by_dropdown", "value"),
    )
    def update_color_by_dropdown(admin_mode, current_value):
        standard_options = [
            {"label": "Account", "value": "Account"},
            {"label": "Partition", "value": "Partition"},
            {"label": "State", "value": "State"},
            {"label": "QOS", "value": "QOS"},
        ]
        admin_options = [*standard_options, {"label": "User", "value": "User"}]
        options = admin_options if admin_mode else standard_options
        valid_values = [opt["value"] for opt in options]
        if current_value in valid_values:
            return options, current_value
        return options, None

    @app.callback(
        Output("hostname_dropdown", "options"),
        Output("hostname_dropdown", "value"),
        Input("interval", "n_intervals"),
        Input("hostname_dropdown", "value"),
    )
    def update_hostnames(_, current_hostname):
        hostnames = list_to_options(datastore.get_hostnames())
        if not hostnames:
            return hostnames, None
        hostname_values = [h["value"] for h in hostnames]
        if current_hostname in hostname_values:
            return hostnames, current_hostname
        return hostnames, hostnames[0]["value"]

    @app.callback(
        Output("data_range_picker", "start_date"),
        Output("data_range_picker", "end_date"),
        Output("data_range_picker", "min_date_allowed"),
        Output("data_range_picker", "max_date_allowed"),
        Input("hostname_dropdown", "value"),
    )
    def update_date_range(hostname):
        min_date, max_date = datastore.get_min_max_dates(hostname)
        today_date = date.today()
        today_iso_format = today_date.isoformat()
        a_while_ago = today_date - relativedelta(days=45)
        a_while_ago_iso_date = a_while_ago.isoformat()
        return a_while_ago_iso_date, today_iso_format, min_date, max_date

    @app.callback(
        Output("partitions_dropdown", "options"),
        Input("hostname_dropdown", "value"),
    )
    def update_partitions_dropdown(hostname):
        if not hostname:
            return []
        partitions = datastore.get_partitions(hostname)
        return [{"label": p, "value": p} for p in partitions]

    @app.callback(
        Output("users_dropdown", "options"),
        Input("hostname_dropdown", "value"),
        Input("admin-mode-switch", "value"),
    )
    def update_users_dropdown(hostname, admin_mode):
        if not hostname or not admin_mode:
            return []
        users = datastore.get_users(hostname)
        return [{"label": u, "value": u} for u in users]

    @app.callback(Output("users-filter-container", "style"), Input("admin-mode-switch", "value"))
    def toggle_users_filter(admin_mode):
        if admin_mode:
            return {"display": "block"}
        return {"display": "none"}

    @app.callback(Output("admin-toggle-container", "style"), Input("interval", "n_intervals"))
    def show_admin_toggle(n_intervals):
        admin_users = [
            "tabeel",
            "aeaahmed",
            "sdrwacker",
        ]
        try:
            current_user = getpass.getuser()
            print("Current user:", current_user)
            if current_user in admin_users:
                return {"display": "block"}
            return {"display": "none"}
        except:
            return {"display": "none"}

    @app.callback(Output("admin-mode-switch", "label"), Input("admin-mode-switch", "value"))
    def update_admin_label(admin_mode):
        if admin_mode:
            return "Admin Mode Active"
        return "Admin Mode"

    @app.callback(Output("admin-warning", "is_open"), Input("admin-mode-switch", "value"), Input("close-admin-warning", "n_clicks"), prevent_initial_call=True)
    def toggle_admin_warning(admin_mode, n_clicks):
        ctx = dash.callback_context
        if not ctx.triggered:
            return False
        trigger_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if trigger_id == "admin-mode-switch":
            return admin_mode
        if trigger_id == "close-admin-warning":
            return False
        return False


    @app.callback(
        Output("total-active-users", "children"),
        Output("total-jobs", "children"),
        Output("total-cpu-hours", "children"),
        Output("total-gpu-hours", "children"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        background=False,
        manager=background_callback_manager,
    )
    def update_summary_stats(hostname, start_date, end_date, states, partitions, users, accounts, qos):
        if not hostname:
            return "N/A", "N/A", "N/A", "N/A"

        # Get filtered data
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=True,
        )

        if df.empty:
            return "0", "0", "0", "0"

        # Calculate total unique active users
        total_users = df["User"].nunique()

        # Calculate total jobs
        total_jobs = len(df)

        # Calculate total CPU and GPU hours
        total_cpu_hours = df["CPU-hours"].sum()
        total_gpu_hours = df["GPU-hours"].sum()

        # Format numbers for display
        formatted_users = f"{total_users:,}"
        formatted_jobs = f"{total_jobs:,}"
        formatted_cpu = f"{total_cpu_hours:,.0f} h"
        formatted_gpu = f"{total_gpu_hours:,.0f} h"

        return formatted_users, formatted_jobs, formatted_cpu, formatted_gpu


    @app.callback(
        Output("plot_active_users", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("accounts_dropdown", "value"),
        Input("complete_periods_switch", "value"),
        Input("session-store", "data"),
        Input("account-formatter-store", "data"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_active_users(hostname, start_date, end_date, accounts, complete_periods, session_data, account_format):
        if session_data is None:
            session_data = initialize_session_data()

        account_segments = account_format.get("segments") if account_format else None

        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            accounts=accounts,
            format_accounts=True,
            account_segments=account_segments,
            complete_periods_only=complete_periods,
        )
        time_col = get_time_column(start_date, end_date)

        color_by = "Account"

        category_order, color_map = ensure_consistent_categories_and_colors(
            df, color_by, COLORS[color_by], session_data
        )

        active_users = df.groupby([time_col, color_by])["User"].nunique().reset_index(name="num_active_users")

        fig = px.area(
            active_users,
            x=time_col,
            y="num_active_users",
            color=color_by,
            title="Number of active users",
            labels={"num_active_users": "Number of active users"},
            category_orders={color_by: category_order},
        )

        for _i, trace in enumerate(fig.data):
            if hasattr(trace, 'fillcolor') and hasattr(trace, 'name'):
                color = color_map.get(trace.name, trace.fillcolor)
                trace.fillcolor = color
                if hasattr(trace, 'line') and hasattr(trace.line, 'color'):
                    trace.line.color = color

        return fig

    @app.callback(
        Output("plot_number_of_jobs", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("color_by_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        Input("account-formatter-store", "data"), 
        background=False,
        manager=background_callback_manager,
    )
    def plot_number_of_jobs(hostname, start_date, end_date, states, partitions, users, accounts, color_by, qos, session_data, account_format):
        
        account_segments = account_format.get("segments") if account_format else None

        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=True,
            account_segments=account_segments,
        )
        time_col = get_time_column(start_date, end_date)
        sorted_time_values = sorted(df[time_col].unique())
        if not color_by:
            df_counts = df[time_col].value_counts().to_frame("Counts").reset_index()
            df_counts = df_counts.sort_values(time_col)
            fig = px.bar(
                df_counts,
                x=time_col,
                y="Counts",
                title="Job submissions",
            )
        else:
            category_order, color_map = ensure_consistent_categories_and_colors(
                df, color_by, COLORS[color_by], session_data
            )

            df_counts = df[[color_by, time_col]].groupby([color_by, time_col]).size().to_frame("Counts").reset_index()
            fig = px.bar(
                df_counts,
                x=time_col,
                y="Counts",
                color=color_by,
                title="Number of job submissions",
                category_orders={color_by: category_order},
            )

            for _i, trace in enumerate(fig.data):
                if hasattr(trace, 'marker') and hasattr(trace, 'name'):
                    trace.marker.color = color_map.get(trace.name, trace.marker.color)

        fig.update_xaxes(categoryorder="array", categoryarray=sorted_time_values)
        return fig

    @app.callback(
        Output("plot_fractions_accounts", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("color_by_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        Input("account-formatter-store", "data"), 
        background=False,
        manager=background_callback_manager,
    )
    def plot_fraction_accounts(hostname, start_date, end_date, states, partitions, users, accounts, color_by, qos, session_data, account_format):

        account_segments = account_format.get("segments") if account_format else None

        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=True,
            account_segments=account_segments,
        )

        if color_by == 'User':
            pass
        else:
            color_by = 'Account'

        category_order, color_map = ensure_consistent_categories_and_colors(
            df, color_by, COLORS[color_by], session_data
        )

        counts = df[color_by].value_counts().to_frame("Counts").reset_index()
        fig = px.pie(
            counts,
            values="Counts",
            names=color_by,
            title=f"Job submissions by {color_by.lower()}",
            category_orders={color_by: category_order},
        )

        fig.update_traces(
            marker={"colors": [color_map.get(cat, "#CCCCCC") for cat in counts[color_by]]},
            textposition="inside",
            textinfo="percent+label"
        )

        return fig

    @app.callback(
        Output("plot_fraction_qos", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_fraction_qos(hostname, start_date, end_date, states, partitions, users, accounts, qos, session_data):

        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=False,
        )

        category_order, color_map = ensure_consistent_categories_and_colors(
            df, "QOS", COLORS["QOS"], session_data
        )

        counts = df.QOS.value_counts().to_frame("Counts").reset_index()
        fig = px.pie(
            counts,
            values="Counts",
            names="QOS",
            title="Job submissions by quality of service (QoS)",
            category_orders={"QOS": category_order},
        )

        fig.update_traces(
            marker={"colors": [color_map.get(cat, "#CCCCCC") for cat in counts["QOS"]]},
            textposition="inside",
            textinfo="percent+label"
        )

        return fig

    @app.callback(
        Output("plot_fractions_states", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_fractions_states(hostname, start_date, end_date, states, partitions, users, accounts, qos, session_data):

        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=False,
        )

        category_order, color_map = ensure_consistent_categories_and_colors(
            df, "State", COLORS["State"], session_data
        )

        counts = df.State.value_counts().to_frame("Counts").reset_index()
        fig = px.pie(
            counts,
            values="Counts",
            names="State",
            title="Job state",
            category_orders={"State": category_order},
        )

        fig.update_traces(
            marker={"colors": [color_map.get(cat, "#CCCCCC") for cat in counts["State"]]},
            textposition="inside",
            textinfo="percent+label"
        )

        return fig

    @app.callback(
        Output("plot_cpus_per_job", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_cpus_per_job(hostname, start_date, end_date, states, partitions, users, accounts, qos):
        
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=False,
        )
        cpus_per_job = df.CPUs.value_counts().sort_index().to_frame("Count").reset_index()
        cpus_per_job["CPUs"] = cpus_per_job["CPUs"].astype(str)
        cpu_order = cpus_per_job["CPUs"].tolist()
        return px.bar(
            cpus_per_job,
            x="CPUs",
            y="Count",
            title="Number of CPUs per job",
            log_y=False,
            text_auto=True,
            category_orders={"CPUs": cpu_order},
        )

    @app.callback(
        Output("plot_gpus_per_job", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_gpus_per_job(hostname, start_date, end_date, states, partitions, users, accounts, qos):
        
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=False,
        )
        
        gpus_per_job = df.GPUs.value_counts().sort_index().to_frame("Count").reset_index()
        gpus_per_job["GPUs"] = gpus_per_job["GPUs"].astype(str)
        gpu_order = gpus_per_job["GPUs"].tolist()
        return px.bar(
            gpus_per_job,
            x="GPUs",
            y="Count",
            title="Number of GPUs per job",
            log_y=False,
            text_auto=True,
            category_orders={"GPUs": gpu_order},
        )

    @app.callback(
        Output("plot_nodes_per_job", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_nodes_per_job(hostname, start_date, end_date, states, partitions, users, accounts, qos):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=False,
        )
        nodes_per_job = df.Nodes.value_counts().sort_index().to_frame("Count").reset_index()
        nodes_per_job["Nodes"] = nodes_per_job["Nodes"].astype(str)
        node_order = nodes_per_job["Nodes"].tolist()
        return px.bar(
            nodes_per_job,
            x="Nodes",
            y="Count",
            title="Number of nodes per job",
            log_y=False,
            text_auto=True,
            category_orders={"Nodes": node_order},
        )

    @app.callback(
        Output("plot_waiting_times", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("waiting_times_observable_dropdown", "value"),
        Input("color_by_dropdown", "value"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        Input("account-formatter-store", "data"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_waiting_times(hostname, start_date, end_date, observable, color_by, states, partitions, users, accounts, qos, session_data, account_format):  

        account_segments = account_format.get("segments") if account_format else None
        
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=True,
            account_segments=account_segments,
        )

        time_col = get_time_column(start_date, end_date)

        observable_names = {
            "75%": "75 percentile",
            "50%": "Median",
            "25%": "25 percentile",
            "max": "Maximum",
            "mean": "Mean",
        }
        name = observable_names.get(observable, observable)

        if not color_by:
            stats = df.groupby(time_col)["WaitingTime [h]"].describe().reset_index()
            fig = px.scatter(
                stats,
                x=time_col,
                y=observable,
                title=f"{name} waiting time in hours",
                log_y=False,
            )
        else:
            category_order, color_map = ensure_consistent_categories_and_colors(
                df, color_by, COLORS[color_by], session_data
            )

            stats = df[[color_by, time_col, "WaitingTime [h]"]].groupby([color_by, time_col]).describe().droplevel(0, axis=1).reset_index()
            fig = px.scatter(
                stats,
                x=time_col,
                y=observable,
                title=f"{name} waiting time in hours",
                color=color_by,
                log_y=False,
                category_orders={color_by: category_order},
            )

            for _i, trace in enumerate(fig.data):
                if hasattr(trace, 'marker') and hasattr(trace, 'name'):
                    trace.marker.color = color_map.get(trace.name, trace.marker.color)

        fig.update_traces(marker={"size": 10})
        fig.update_layout(yaxis_title=name)
        return fig

    @app.callback(
        Output("plot_waiting_times_hist", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("color_by_dropdown", "value"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        Input("account-formatter-store", "data"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_waiting_times_dist(hostname, start_date, end_date, color_by, states, partitions, users, accounts, qos, session_data, account_format):
        
        account_segments = account_format.get("segments") if account_format else None

        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=True,
            account_segments=account_segments,
        )

        df["Time Group"] = categorize_time_series(df["WaitingTime [h]"])
        ordered_categories = df["Time Group"].cat.categories

        if not color_by:
            fig = px.histogram(
                df,
                x="Time Group",
                title="Waiting Times",
                histnorm="percent",
                text_auto=True,
            )
        else:
            category_order, color_map = ensure_consistent_categories_and_colors(
                df, color_by, COLORS[color_by], session_data
            )

            fig = px.histogram(
                df,
                x="Time Group",
                color=color_by,
                title="Waiting Times",
                histnorm="percent",
                text_auto=True,
                category_orders={color_by: category_order},
            )

            for _i, trace in enumerate(fig.data):
                if hasattr(trace, 'marker') and hasattr(trace, 'name'):
                    trace.marker.color = color_map.get(trace.name, trace.marker.color)

        fig.update_traces(
            hovertemplate="<br>Percent = %{y:.2f}<extra>%{x}</extra>",
            texttemplate="%{y:.1f}%",
        )
        fig.update_xaxes(categoryorder="array", categoryarray=ordered_categories)
        return fig

    @app.callback(
        Output("plot_job_duration", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("job_duration_observable_dropdown", "value"),
        Input("color_by_dropdown", "value"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        Input("account-formatter-store", "data"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_job_duration(hostname, start_date, end_date, observable, color_by, states, partitions, users, accounts, qos, session_data, account_format):

        account_segments = account_format.get("segments") if account_format else None
        
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=True,
            account_segments=account_segments,
        )

        time_col = get_time_column(start_date, end_date)
        observable_names = {
            "75%": "75 percentile",
            "50%": "Median",
            "25%": "25 percentile",
            "max": "Maximum",
            "mean": "Mean",
        }

        name = observable_names.get(observable, observable)

        if not color_by:
            stats = df.groupby(time_col)["Elapsed [h]"].describe().reset_index()
            fig = px.scatter(
                stats,
                x=time_col,
                y=observable,
                title=f"{name} job duration in hours",
                log_y=False,
            )
        else:
            category_order, color_map = ensure_consistent_categories_and_colors(
                df, color_by, COLORS[color_by], session_data
            )

            stats = df[[color_by, time_col, "Elapsed [h]"]].groupby([color_by, time_col]).describe().droplevel(0, axis=1).reset_index()
            fig = px.scatter(
                stats,
                x=time_col,
                y=observable,
                title=f"{name} job duration in hours",
                color=color_by,
                log_y=False,
                category_orders={color_by: category_order},
            )

            for _i, trace in enumerate(fig.data):
                if hasattr(trace, 'marker') and hasattr(trace, 'name'):
                    trace.marker.color = color_map.get(trace.name, trace.marker.color)

        fig.update_traces(marker={"size": 10})
        fig.update_layout(yaxis_title=name)
        return fig

    @app.callback(
        Output("plot_job_duration_hist", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("color_by_dropdown", "value"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        Input("account-formatter-store", "data"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_job_duration_dist(hostname, start_date, end_date, color_by, states, partitions, users, accounts, qos, session_data, account_format):
        
        account_segments = account_format.get("segments") if account_format else None

        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=True,
            account_segments=account_segments,
        )

        thresholds = [0, 1, 4, 12, 24, 72, 168, float('inf')]

        threshold_labels = [
            "< 1h",
            "1h - 4h",
            "4h - 12h",
            "12h - 24h",
            "1d - 3d",
            "3d - 7d",
            "> 7d"
        ]

        df['Duration Category'] = pd.cut(
            df['Elapsed [h]'],
            bins=thresholds,
            labels=threshold_labels,
            right=False
        )

        ordered_categories = threshold_labels

        if not color_by:
            fig = px.histogram(
                df,
                x="Duration Category",
                title="Job Duration",
                histnorm="percent",
                text_auto=True,
                category_orders={"Duration Category": ordered_categories}
            )
        else:
            category_order, color_map = ensure_consistent_categories_and_colors(
                df, color_by, COLORS[color_by], session_data
            )

            fig = px.histogram(
                df,
                x="Duration Category",
                color=color_by,
                title="Job Duration",
                histnorm="percent",
                text_auto=True,
                category_orders={
                    "Duration Category": ordered_categories,
                    color_by: category_order
                }
            )

            for _i, trace in enumerate(fig.data):
                if hasattr(trace, 'marker') and hasattr(trace, 'name'):
                    trace.marker.color = color_map.get(trace.name, trace.marker.color)

        fig.update_traces(
            hovertemplate="<br>Percent = %{y:.2f}<extra>%{x}</extra>",
            texttemplate="%{y:.1f}%",
        )

        fig.update_xaxes(categoryorder="array", categoryarray=ordered_categories)
        fig.update_yaxes(title_text="Percentage of Jobs (%)")

        return fig

    @app.callback(
        Output("plot_cpu_hours", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("color_by_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        Input("account-formatter-store", "data"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_cpu_hours(hostname, start_date, end_date, states, partitions, users, accounts, color_by, qos, session_data, account_format):

        account_segments = account_format.get("segments") if account_format else None

        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            complete_periods_only=False,
            qos=qos,
            format_accounts=True,
            account_segments=account_segments,
        )

        time_col = get_time_column(start_date, end_date).replace("Submit", "Start")

        if not color_by:
            total_usage = df.groupby(time_col)[["CPU-hours"]].sum().reset_index()
            return px.bar(
                total_usage,
                x=time_col,
                y="CPU-hours",
                title="CPU-hours used",
            )

        category_order, color_map = ensure_consistent_categories_and_colors(
            df, color_by, COLORS[color_by], session_data
        )

        color_distributions = df.groupby([time_col, color_by])[["CPU-hours"]].sum().reset_index()

        fig = px.bar(
            color_distributions,
            x=time_col,
            y="CPU-hours",
            color=color_by,
            title="CPU-hours used",
            category_orders={color_by: category_order},
        )

        for _i, trace in enumerate(fig.data):
            if hasattr(trace, 'marker') and hasattr(trace, 'name'):
                trace.marker.color = color_map.get(trace.name, trace.marker.color)

        return fig

    @app.callback(
        Output("plot_gpu_hours", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("color_by_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        Input("account-formatter-store", "data"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_gpu_hours(hostname, start_date, end_date, states, partitions, users, accounts, color_by, qos, session_data, account_format):

        account_segments = account_format.get("segments") if account_format else None
        
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            complete_periods_only=False,
            qos=qos,
            format_accounts=True,
            account_segments=account_segments
        )

        time_col = get_time_column(start_date, end_date).replace("Submit", "Start")

        if not color_by:
            total_usage = df.groupby(time_col)[["GPU-hours"]].sum().reset_index()
            return px.bar(
                total_usage,
                x=time_col,
                y="GPU-hours",
                title="GPU-hours used",
            )

        category_order, color_map = ensure_consistent_categories_and_colors(
            df, color_by, COLORS[color_by], session_data
        )

        color_distributions = df.groupby([time_col, color_by])[["GPU-hours"]].sum().reset_index()

        fig = px.bar(
            color_distributions,
            x=time_col,
            y="GPU-hours",
            color=color_by,
            title="GPU-hours used",
            category_orders={color_by: category_order},
        )

        for _i, trace in enumerate(fig.data):
            if hasattr(trace, 'marker') and hasattr(trace, 'name'):
                trace.marker.color = color_map.get(trace.name, trace.marker.color)

        return fig

    @app.callback(
        Output("plot_fraction_accounts_cpu_usage", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("color_by_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        Input("account-formatter-store", "data"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_fraction_cpu_usage(hostname, start_date, end_date, states, partitions, users, accounts, color_by, qos_selection, session_data, account_format):

        account_segments = account_format.get("segments") if account_format else None

        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos_selection,
            format_accounts=True,
            account_segments=account_segments,
        )

        category = color_by if color_by else "Account"

        category_order, color_map = ensure_consistent_categories_and_colors(
            df, category, COLORS[category], session_data
        )

        usage_by_category = df.groupby(category)["CPU-hours"].sum().reset_index()
        usage_by_category = ensure_consistent_categories(usage_by_category, category, "CPU-hours", session_data)

        [color_map.get(cat, "#CCCCCC") for cat in usage_by_category[category]]

        fig = px.pie(
            usage_by_category,
            values="CPU-hours",
            names=category,
            title=f"CPU-hours used by {category.lower()}",
            color=category,
            color_discrete_map=color_map,
            category_orders={category: category_order}
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")

        return fig

    @app.callback(
        Output("plot_fraction_accounts_gpu_usage", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("color_by_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        Input("account-formatter-store", "data"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_fraction_gpu_usage(hostname, start_date, end_date, states, partitions, users, accounts, color_by, qos, session_data, account_format):

        account_segments = account_format.get("segments") if account_format else None
        
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos,
            format_accounts=True,
            account_segments=account_segments,
        )

        category = color_by if color_by else "Account"

        category_order, color_map = ensure_consistent_categories_and_colors(
            df, category, COLORS[category], session_data
        )

        usage_by_category = df.groupby(category)["GPU-hours"].sum().reset_index()
        usage_by_category = ensure_consistent_categories(usage_by_category, category, "GPU-hours", session_data)

        fig = px.pie(
            usage_by_category,
            values="GPU-hours",
            names=category,
            title=f"GPU-hours used by {category.lower()}",
            color=category,
            color_discrete_map=color_map,
            category_orders={category: category_order}
        )

        fig.update_traces(textposition="inside", textinfo="percent+label")

        return fig

    @app.callback(
        Output("plot_nodes_usage_cpu", "figure"),
        Output("plot_nodes_usage_gpu", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("color_by_dropdown", "value"),
        Input("hide_unused_nodes_switch", "value"),
        Input("normalize_node_resources_switch", "value"),
        Input("sort_by_usage_switch", "value"),
        Input("qos_selection_dropdown", "value"),
        Input("session-store", "data"),
        Input("account-formatter-store", "data"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_nodes_usage(hostname, start_date, end_date, states, partitions, users, accounts, color_by, hide_unused, normalize, sort_by_usage, qos_selection, session_data, account_format):

        account_segments = account_format.get("segments") if account_format else None

        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            qos=qos_selection,
            complete_periods_only=False,
            format_accounts=True,
            account_segments=account_segments
        )

        cols = ["NodeList", "GPU-hours", "CPU-hours"]
        groupby_cols = ["NodeList"]

        if color_by:
            category_order, color_map = ensure_consistent_categories_and_colors(
                df, color_by, COLORS[color_by], session_data
            )
            cols.append(color_by)
            groupby_cols.append(color_by)

        node_usage = df[cols].explode("NodeList").dropna().groupby(groupby_cols).sum().reset_index()

        cpu_node_usage = node_usage.copy()
        gpu_node_usage = node_usage.copy()

        if hide_unused and not node_usage.empty:
            cpu_node_usage = cpu_node_usage[cpu_node_usage["CPU-hours"] > 0]
            gpu_node_usage = gpu_node_usage[gpu_node_usage["GPU-hours"] > 0]

        if color_by:
            cpu_total_per_node = cpu_node_usage.groupby("NodeList")["CPU-hours"].sum().reset_index()
            gpu_total_per_node = gpu_node_usage.groupby("NodeList")["GPU-hours"].sum().reset_index()

        if sort_by_usage:
            if color_by:
                cpu_sorted_nodes = cpu_total_per_node.sort_values("CPU-hours", ascending=False)["NodeList"].unique() if not cpu_node_usage.empty else []
                gpu_sorted_nodes = gpu_total_per_node.sort_values("GPU-hours", ascending=False)["NodeList"].unique() if not gpu_node_usage.empty else []
            else:
                cpu_sorted_nodes = cpu_node_usage.sort_values("CPU-hours", ascending=False)["NodeList"].unique() if not cpu_node_usage.empty else []
                gpu_sorted_nodes = gpu_node_usage.sort_values("GPU-hours", ascending=False)["NodeList"].unique() if not gpu_node_usage.empty else []
        else:
            cpu_nodes = cpu_node_usage["NodeList"].unique() if not cpu_node_usage.empty else []
            gpu_nodes = gpu_node_usage["NodeList"].unique() if not gpu_node_usage.empty else []
            cpu_sorted_nodes = sorted(cpu_nodes, key=natural_sort_key)
            gpu_sorted_nodes = sorted(gpu_nodes, key=natural_sort_key)

        if normalize:
            node_resources = node_config.get_all_node_resources(node_usage["NodeList"].unique())
            for node in node_resources:
                cpu_count = max(node_resources[node]["cpus"], 1)
                if node in cpu_node_usage["NodeList"].values:
                    mask = cpu_node_usage["NodeList"] == node
                    cpu_node_usage.loc[mask, "CPU-hours"] = cpu_node_usage.loc[mask, "CPU-hours"] / cpu_count
            for node in node_resources:
                gpu_count = max(node_resources[node]["gpus"], 1)
                if node in gpu_node_usage["NodeList"].values and node_resources[node]["gpus"] > 0:
                    mask = gpu_node_usage["NodeList"] == node
                    gpu_node_usage.loc[mask, "GPU-hours"] = gpu_node_usage.loc[mask, "GPU-hours"] / gpu_count

        subtitle = ""
        if normalize:
            subtitle = "<br><sub>Values are divided by the number of CPUs/GPUs in each node</sub>"

        if not color_by:
            fig_nodes_usage_cpu = px.bar(
                cpu_node_usage,
                x="NodeList",
                y="CPU-hours",
                height=400,
                title="Total CPU-hours per node" + (" (normalized)" if normalize else "") + subtitle,
            )
        else:
            fig_nodes_usage_cpu = px.bar(
                cpu_node_usage,
                x="NodeList",
                y="CPU-hours",
                height=400,
                title="Total CPU-hours per node" + (" (normalized)" if normalize else "") + subtitle,
                color=color_by,
                category_orders={color_by: category_order},
            )

            for _i, trace in enumerate(fig_nodes_usage_cpu.data):
                if hasattr(trace, 'marker') and hasattr(trace, 'name'):
                    trace.marker.color = color_map.get(trace.name, trace.marker.color)

        if not color_by:
            fig_nodes_usage_gpu = px.bar(
                gpu_node_usage,
                x="NodeList",
                y="GPU-hours",
                height=400,
                title="Total GPU-hours per node" + (" (normalized)" if normalize else "") + subtitle,
            )
        else:
            fig_nodes_usage_gpu = px.bar(
                gpu_node_usage,
                x="NodeList",
                y="GPU-hours",
                height=400,
                title="Total GPU-hours per node" + (" (normalized)" if normalize else "") + subtitle,
                color=color_by,
                category_orders={color_by: category_order},
            )

            for _i, trace in enumerate(fig_nodes_usage_gpu.data):
                if hasattr(trace, 'marker') and hasattr(trace, 'name'):
                    trace.marker.color = color_map.get(trace.name, trace.marker.color)

        fig_nodes_usage_cpu.update_xaxes(categoryorder="array", categoryarray=cpu_sorted_nodes)
        fig_nodes_usage_gpu.update_xaxes(categoryorder="array", categoryarray=gpu_sorted_nodes)

        if normalize:
            hover_template = "%{x}<br>%{y:.2f} hours"
            if color_by:
                hover_template += "<br>%{fullData.name}"
            hover_template += "<extra>Normalized by CPU count</extra>"
            fig_nodes_usage_cpu.update_traces(hovertemplate=hover_template)
            hover_template = "%{x}<br>%{y:.2f} hours"
            if color_by:
                hover_template += "<br>%{fullData.name}"
            hover_template += "<extra>Normalized by GPU count</extra>"
            fig_nodes_usage_gpu.update_traces(hovertemplate=hover_template)

        return fig_nodes_usage_cpu, fig_nodes_usage_gpu

    @app.callback(Output("pie-charts-row", "style"), Input("color_by_dropdown", "value"))
    def toggle_pie_charts_visibility(color_by):
        if color_by:
            return {"display": "block"}
        return {"display": "none"}

    @app.callback(
        Output("qos_selection_dropdown", "options"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
    )
    def update_qos_options(hostname, start_date, end_date):
        if not hostname:
            return []

        qos_options = datastore.get_qos(hostname)

        options = []
        options.extend([{"label": qos, "value": qos} for qos in sorted(qos_options)])

        return options

    @app.callback(
        Output("plot_job_duration_stacked", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_job_duration_stacked(hostname, start_date, end_date, states, partitions, users, accounts, qos):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            qos=qos,
            users=users,
            accounts=accounts,
            format_accounts=False,
        )

        if df.empty:
            return px.bar(title="No data available for selected filters")

        time_col = get_time_column(start_date, end_date)

        thresholds = [0, 1, 4, 12, 24, 72, 168, float('inf')]

        threshold_labels = [
            "< 1h",
            "1h - 4h",
            "4h - 12h",
            "12h - 24h",
            "1d - 3d",
            "3d - 7d",
            "> 7d"
        ]

        colors = [
            "rgb(237, 248, 233)",
            "rgb(199, 233, 192)",
            "rgb(161, 217, 155)",
            "rgb(116, 196, 118)",
            "rgb(65, 171, 93)",
            "rgb(35, 139, 69)",
            "rgb(0, 90, 50)"
        ]

        results = []

        for period in sorted(df[time_col].unique()):
            period_df = df[df[time_col] == period]
            total_jobs = len(period_df)

            for i in range(len(thresholds) - 1):
                lower = thresholds[i]
                upper = thresholds[i + 1]
                label = threshold_labels[i]

                count = ((period_df['Elapsed [h]'] >= lower) &
                        (period_df['Elapsed [h]'] < upper)).sum()

                percentage = (count / total_jobs * 100) if total_jobs > 0 else 0

                results.append({
                    time_col: period,
                    'Job Duration': label,
                    'Count': count,
                    'Percentage': percentage,
                    'Total Jobs': total_jobs
                })

        results_df = pd.DataFrame(results)

        fig = px.bar(
            results_df,
            x=time_col,
            y="Percentage",
            color="Job Duration",
            title="Job Duration Distribution by Period",
            labels={
                "Percentage": "Percentage of Jobs (%)",
                time_col: "Time Period"
            },
            color_discrete_map={threshold_labels[i]: colors[i] for i in range(len(threshold_labels))},
            category_orders={"Job Duration": threshold_labels},
            hover_data=["Count", "Total Jobs"],
        )

        fig.update_layout(
            legend_title_text="Job Duration",
            barmode="stack",
            yaxis={
                "title": "Percentage of Jobs (%)",
                "range": [0, 100]
            },
            xaxis={
                "title": time_col,
                "tickangle": 45 if len(results_df[time_col].unique()) > 12 else 0
            },
            margin={"t": 50, "l": 50, "r": 20, "b": 100},
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5
            }
        )

        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>" +
                        "Job Duration: %{customdata[0]} jobs<br>" +
                        "Percentage: %{y:.1f}%<br>" +
                        "Total Jobs: %{customdata[1]}<extra>%{fullData.name}</extra>"
        )

        return fig

    @app.callback(
        Output("plot_waiting_times_stacked", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("states_dropdown", "value"),
        Input("partitions_dropdown", "value"),
        Input("users_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("qos_selection_dropdown", "value"),
        background=False,
        manager=background_callback_manager,
    )
    def plot_waiting_times_stacked(hostname, start_date, end_date, states, partitions, users, accounts, qos):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            qos=qos,
            accounts=accounts,
            format_accounts=False,
        )

        if df.empty:
            return px.bar(title="No data available for selected filters")

        time_col = get_time_column(start_date, end_date)

        thresholds = [0, 0.5, 1, 4, 12, 24, float('inf')]

        threshold_labels = [
            "< 30min",
            "30min - 1h",
            "1h - 4h",
            "4h - 12h",
            "12h - 24h",
            "> 24h"
        ]

        colors = [
            "rgb(255, 245, 240)",
            "rgb(254, 224, 210)",
            "rgb(252, 187, 161)",
            "rgb(252, 146, 114)",
            "rgb(239, 59, 44)",
            "rgb(153, 0, 13)"
        ]

        results = []

        for period in sorted(df[time_col].unique()):
            period_df = df[df[time_col] == period]
            total_jobs = len(period_df)

            for i in range(len(thresholds) - 1):
                lower = thresholds[i]
                upper = thresholds[i + 1]
                label = threshold_labels[i]

                count = ((period_df['WaitingTime [h]'] >= lower) &
                        (period_df['WaitingTime [h]'] < upper)).sum()

                percentage = (count / total_jobs * 100) if total_jobs > 0 else 0

                results.append({
                    time_col: period,
                    'Waiting Time': label,
                    'Count': count,
                    'Percentage': percentage,
                    'Total Jobs': total_jobs
                })

        results_df = pd.DataFrame(results)

        fig = px.bar(
            results_df,
            x=time_col,
            y="Percentage",
            color="Waiting Time",
            title="Waiting Time Distribution by Period",
            labels={
                "Percentage": "Percentage of Jobs (%)",
                time_col: "Time Period"
            },
            color_discrete_map={threshold_labels[i]: colors[i] for i in range(len(threshold_labels))},
            category_orders={"Waiting Time": threshold_labels},
            hover_data=["Count", "Total Jobs"],
        )

        fig.update_layout(
            legend_title_text="Waiting Time",
            barmode="stack",
            yaxis={
                "title": "Percentage of Jobs (%)",
                "range": [0, 100]
            },
            xaxis={
                "title": time_col,
                "tickangle": 45 if len(results_df[time_col].unique()) > 12 else 0
            },
            margin={"t": 50, "l": 50, "r": 20, "b": 100},
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "center",
                "x": 0.5
            }
        )

        fig.update_traces(
            hovertemplate="<b>%{x}</b><br>" +
                        "Waiting Time: %{customdata[0]} jobs<br>" +
                        "Percentage: %{y:.1f}%<br>" +
                        "Total Jobs: %{customdata[1]}<extra>%{fullData.name}</extra>"
        )

        return fig

    @app.callback(
        Output("account-format-container", "style"),
        Input("color_by_dropdown", "value"),
    )
    def toggle_account_format_visibility(color_by):
        # Just in case we want to hide the account format dropdown.
        if color_by == "Account":
            return {"display": "block"}
        return {"display": "block"}
