import getpass
import logging
from datetime import date

import dash
import pandas as pd
import plotly.express as px
from dash import Input, Output
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

CATEGORY_ORDERS = {
    "User": None,
    "Account": None,
    "Partition": None,
    "State": None,
    "QOS": None,
}


def list_to_options(list_of_strings):
    return [{"label": x, "value": x} for x in list_of_strings]


def add_callbacks(app, datastore):
    def get_category_order(df, category):
        global CATEGORY_ORDERS
        if CATEGORY_ORDERS[category] is None and category in df.columns:
            CATEGORY_ORDERS[category] = df[category].value_counts().index.tolist()
        return CATEGORY_ORDERS[category] or []

    def ensure_consistent_categories(df, category_name, value_column=None):
        if CATEGORY_ORDERS[category_name] is None or category_name not in df.columns:
            return df
        all_category_values = CATEGORY_ORDERS[category_name]
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
        Output("plot_active_users", "figure"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
        Input("partitions_dropdown", "value"),
        Input("accounts_dropdown", "value"),
        Input("account-formatter-store", "data"),
        Input("complete_periods_switch", "value"),
    )
    def plot_active_users(hostname, start_date, end_date, partitions, accounts, formatter_data, complete_periods):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            partitions=partitions,
            accounts=accounts,
            format_accounts=True,
            complete_periods_only=complete_periods,
        )
        time_col = get_time_column(start_date, end_date)

        color_by = "Account"

        active_users = df.groupby([time_col, color_by])["User"].nunique().reset_index(name="num_active_users")

        category_order = get_category_order(df, color_by)

        fig = px.area(
            active_users,
            x=time_col,
            y="num_active_users",
            color="Account",
            title="Number of Active Users",
            labels={"num_active_users": "Number of Active Users"},
            color_discrete_sequence=COLORS["Account"],
            category_orders={color_by: category_order},
        )
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
        Input("account-formatter-store", "data"),  # Add this input
    )
    def plot_number_of_jobs(hostname, start_date, end_date, states, partitions, users, accounts, color_by, formatter_data):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            format_accounts=True,  # Enable account formatting
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
            category_order = get_category_order(df, color_by)
            df_counts = df[[color_by, time_col]].groupby([color_by, time_col]).size().to_frame("Counts").reset_index()
            fig = px.bar(
                df_counts,
                x=time_col,
                y="Counts",
                color=color_by,
                title="Job submissions",
                color_discrete_sequence=COLORS[color_by],
                category_orders={color_by: category_order},
            )
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
        Input("account-formatter-store", "data"),  # Add this input
    )
    def plot_fraction_accounts(hostname, start_date, end_date, states, partitions, users, accounts, formatter_data):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            format_accounts=True,  # Enable account formatting
        )
        account_order = get_category_order(df, "Account")
        counts = df.Account.value_counts().to_frame("Counts").reset_index()
        fig = px.pie(
            counts,
            values="Counts",
            names="Account",
            title="Job submissions by account",
            color_discrete_sequence=COLORS["Account"],
            category_orders={"Account": account_order},
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
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
    )
    def plot_fraction_qos(hostname, start_date, end_date, states, partitions, users, accounts):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
        )
        qos_order = get_category_order(df, "QOS")
        counts = df.QOS.value_counts().to_frame("Counts").reset_index()
        fig = px.pie(
            counts,
            values="Counts",
            names="QOS",
            title="Job submissions by quality of service (QoS)",
            color_discrete_sequence=COLORS["QOS"],
            category_orders={"QOS": qos_order},
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
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
    )
    def plot_fractions_states(hostname, start_date, end_date, states, partitions, users, accounts):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
        )
        state_order = get_category_order(df, "State")
        counts = df.State.value_counts().to_frame("Counts").reset_index()
        fig = px.pie(
            counts,
            values="Counts",
            names="State",
            title="Job state",
            color_discrete_sequence=COLORS["State"],
            category_orders={"State": state_order},
        )
        fig.update_traces(textposition="inside", textinfo="percent+label")
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
    )
    def plot_cpus_per_job(hostname, start_date, end_date, states, partitions, users, accounts):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
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
    )
    def plot_gpus_per_job(hostname, start_date, end_date, states, partitions, users, accounts):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
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
    )
    def plot_nodes_per_job(hostname, start_date, end_date, states, partitions, users, accounts):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
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
        Input("account-formatter-store", "data"),
    )
    def plot_waiting_times(hostname, start_date, end_date, observable, color_by, states, partitions, users, accounts, formatter_data):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            format_accounts=True,  # Enable account formatting
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
            category_order = get_category_order(df, color_by)
            stats = df[[color_by, time_col, "WaitingTime [h]"]].groupby([color_by, time_col]).describe().droplevel(0, axis=1).reset_index()
            fig = px.scatter(
                stats,
                x=time_col,
                y=observable,
                title=f"{name} waiting time in hours",
                color=color_by,
                log_y=False,
                color_discrete_sequence=COLORS[color_by],
                category_orders={color_by: category_order},
            )
        
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
        Input("account-formatter-store", "data"),
    )
    def plot_waiting_times_hist(hostname, start_date, end_date, color_by, states, partitions, users, accounts, formatter_data):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            format_accounts=True,  # Enable account formatting
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
            category_order = get_category_order(df, color_by)
            fig = px.histogram(
                df,
                x="Time Group",
                color=color_by,
                title="Waiting Times",
                color_discrete_sequence=COLORS[color_by],
                histnorm="percent",
                text_auto=True,
                category_orders={color_by: category_order},
            )
        
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
        Input("account-formatter-store", "data"),
    )
    def plot_job_duration(hostname, start_date, end_date, observable, color_by, states, partitions, users, accounts, formatter_data):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            format_accounts=True,  # Enable account formatting
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
            category_order = get_category_order(df, color_by)
            stats = df[[color_by, time_col, "Elapsed [h]"]].groupby([color_by, time_col]).describe().droplevel(0, axis=1).reset_index()
            fig = px.scatter(
                stats,
                x=time_col,
                y=observable,
                title=f"{name} job duration in hours",
                color=color_by,
                log_y=False,
                color_discrete_sequence=COLORS[color_by],
                category_orders={color_by: category_order},
            )
        
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
        Input("account-formatter-store", "data"),
    )
    def plot_job_duration_hist(hostname, start_date, end_date, color_by, states, partitions, users, accounts, formatter_data):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            format_accounts=True,  # Enable account formatting
        )
        
        # Define the same job duration thresholds used in job_duration_stacked (in hours)
        thresholds = [0, 1, 4, 12, 24, 72, 168, float('inf')]
        
        # Define threshold labels - same as in job_duration_stacked
        threshold_labels = [
            "< 1h", 
            "1h - 4h", 
            "4h - 12h", 
            "12h - 24h", 
            "1d - 3d", 
            "3d - 7d",
            "> 7d"
        ]
        
        # Create a new column for job duration category
        df['Duration Category'] = pd.cut(
            df['Elapsed [h]'], 
            bins=thresholds,
            labels=threshold_labels,
            right=False
        )
        
        # Sort the categories in the same order as the labels
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
            category_order = get_category_order(df, color_by)
            fig = px.histogram(
                df,
                x="Duration Category",
                color=color_by,
                title="Job Duration",
                color_discrete_sequence=COLORS[color_by],
                histnorm="percent",
                text_auto=True,
                category_orders={
                    "Duration Category": ordered_categories,
                    color_by: category_order
                }
            )
        
        fig.update_traces(
            hovertemplate="<br>Percent = %{y:.2f}<extra>%{x}</extra>",
            texttemplate="%{y:.1f}%",
        )
        
        # To ensure consistent ordering
        fig.update_xaxes(categoryorder="array", categoryarray=ordered_categories)
        
        # Update the y-axis label
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
        Input("account-formatter-store", "data"),
    )
    def plot_cpu_hours(hostname, start_date, end_date, states, partitions, users, accounts, color_by, formatter_data):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            complete_periods_only=False,
            format_accounts=True,  # Enable account formatting
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
        category_order = get_category_order(df, color_by)
        color_distributions = df.groupby([time_col, color_by])[["CPU-hours"]].sum().reset_index()
        return px.bar(
            color_distributions,
            x=time_col,
            y="CPU-hours",
            color=color_by,
            title="CPU-hours used",
            category_orders={color_by: category_order},
            color_discrete_sequence=COLORS[color_by],
        )

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
        Input("account-formatter-store", "data"),  # Add this input
    )
    def plot_gpu_hours(hostname, start_date, end_date, states, partitions, users, accounts, color_by, formatter_data):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            complete_periods_only=False,
            format_accounts=True,  # Enable account formatting
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
        category_order = get_category_order(df, color_by)
        color_distributions = df.groupby([time_col, color_by])[["GPU-hours"]].sum().reset_index()
        return px.bar(
            color_distributions,
            x=time_col,
            y="GPU-hours",
            color=color_by,
            title="GPU-hours used",
            category_orders={color_by: category_order},
            color_discrete_sequence=COLORS[color_by],
        )

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
        Input("account-formatter-store", "data"),  # This input triggers on formatter changes
    )
    def plot_fraction_accounts_cpu_usage(hostname, start_date, end_date, states, partitions, users, accounts, color_by, formatter_data):
        # Important: Reset the category orders when formatter changes to force refresh
        global CATEGORY_ORDERS
        if formatter_data and 'segments' in formatter_data:
            # Reset the cached category orders to force recalculation with new format
            CATEGORY_ORDERS = {
                "User": None,
                "Account": None,
                "Partition": None,
                "State": None,
                "QOS": None,
            }
        
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            format_accounts=True,  # Enable account formatting
        )
        
        category = color_by if color_by else "Account"
        # Recalculate category order with newly formatted data
        category_order = get_category_order(df, category)
        
        # Group by category and sum CPU hours
        usage_by_category = df.groupby(category)["CPU-hours"].sum().reset_index()
        usage_by_category = ensure_consistent_categories(usage_by_category, category, "CPU-hours")
        
        fig = px.pie(
            usage_by_category, 
            values="CPU-hours", 
            names=category, 
            color_discrete_sequence=COLORS[category], 
            category_orders={category: category_order}, 
            title=f"CPU-hours used by {category.lower()}"
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
        Input("account-formatter-store", "data"),  # This input triggers on formatter changes
    )
    def plot_fraction_accounts_gpu_usage(hostname, start_date, end_date, states, partitions, users, accounts, color_by, formatter_data):
        # Important: Reset the category orders when formatter changes to force refresh
        global CATEGORY_ORDERS
        if formatter_data and 'segments' in formatter_data:
            # Reset the cached category orders to force recalculation with new format
            CATEGORY_ORDERS = {
                "User": None,
                "Account": None,
                "Partition": None,
                "State": None,
                "QOS": None,
            }
        
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            format_accounts=True,  # Enable account formatting
        )
        
        category = color_by if color_by else "Account"
        # Recalculate category order with newly formatted data
        category_order = get_category_order(df, category)
        
        # Group by category and sum GPU hours
        usage_by_category = df.groupby(category)["GPU-hours"].sum().reset_index()
        usage_by_category = ensure_consistent_categories(usage_by_category, category, "GPU-hours")
        
        fig = px.pie(
            usage_by_category, 
            values="GPU-hours", 
            names=category, 
            color_discrete_sequence=COLORS[category], 
            category_orders={category: category_order}, 
            title=f"GPU-hours used by {category.lower()}"
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
        Input("account-formatter-store", "data"),
    )
    def plot_nodes_usage(hostname, start_date, end_date, states, partitions, users, accounts, color_by, hide_unused, normalize, sort_by_usage, formatter_data):
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            complete_periods_only=False,
            format_accounts=True,
        )
        cols = ["NodeList", "GPU-hours", "CPU-hours"]
        groupby_cols = ["NodeList"]
        if color_by:
            category_order = get_category_order(df, color_by)
            cols.append(color_by)
            groupby_cols.append(color_by)
        
        # Explode the NodeList and compute usage per node
        node_usage = df[cols].explode("NodeList").dropna().groupby(groupby_cols).sum().reset_index()
        
        cpu_node_usage = node_usage.copy()
        gpu_node_usage = node_usage.copy()
        
        # Filter out unused nodes if requested
        if hide_unused and not node_usage.empty:
            cpu_node_usage = cpu_node_usage[cpu_node_usage["CPU-hours"] > 0]
            gpu_node_usage = gpu_node_usage[gpu_node_usage["GPU-hours"] > 0]
        
        # Calculate total usage per node (summing across all color categories)
        if color_by:
            cpu_total_per_node = cpu_node_usage.groupby("NodeList")["CPU-hours"].sum().reset_index()
            gpu_total_per_node = gpu_node_usage.groupby("NodeList")["GPU-hours"].sum().reset_index()
        
        # Sort nodes by total usage or alphabetically
        if sort_by_usage:
            if color_by:
                # When color factor is selected, sort by total usage across all categories
                cpu_sorted_nodes = cpu_total_per_node.sort_values("CPU-hours", ascending=False)["NodeList"].unique() if not cpu_node_usage.empty else []
                gpu_sorted_nodes = gpu_total_per_node.sort_values("GPU-hours", ascending=False)["NodeList"].unique() if not gpu_node_usage.empty else []
            else:
                # Standard sorting by usage when no color factor is selected
                cpu_sorted_nodes = cpu_node_usage.sort_values("CPU-hours", ascending=False)["NodeList"].unique() if not cpu_node_usage.empty else []
                gpu_sorted_nodes = gpu_node_usage.sort_values("GPU-hours", ascending=False)["NodeList"].unique() if not gpu_node_usage.empty else []
        else:
            # Alphabetical sorting
            cpu_nodes = cpu_node_usage["NodeList"].unique() if not cpu_node_usage.empty else []
            gpu_nodes = gpu_node_usage["NodeList"].unique() if not gpu_node_usage.empty else []
            cpu_sorted_nodes = sorted(cpu_nodes, key=natural_sort_key)
            gpu_sorted_nodes = sorted(gpu_nodes, key=natural_sort_key)
        
        # Normalize by node resources if requested
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
        
        # Create figures
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
                color_discrete_sequence=COLORS[color_by],
                category_orders={color_by: category_order},
            )
        
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
                color_discrete_sequence=COLORS[color_by],
                category_orders={color_by: category_order},
            )
        
        # Set correct sorting order for x-axis
        fig_nodes_usage_cpu.update_xaxes(categoryorder="array", categoryarray=cpu_sorted_nodes)
        fig_nodes_usage_gpu.update_xaxes(categoryorder="array", categoryarray=gpu_sorted_nodes)
        
        # Add hover info if normalized
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
        Output("account-formatter-store", "data"),
        Input("account-format-segments", "value"),
        Input("interval", "n_intervals"),  # Trigger on initial load too
    )
    def update_account_formatter_settings(segments_to_keep, _):
        """Update the account formatter settings when user changes radio buttons."""
        if segments_to_keep is not None:
            # Update the global formatter setting
            from .account_formatter import formatter

            formatter.max_segments = segments_to_keep

            # Clear the datastore filter cache to ensure all charts update
            datastore._filter_data.cache_clear()

        return {"segments": segments_to_keep or 3}  # Default to 3 if None

    @app.callback(
        Output("qos_selection_dropdown", "options"),
        Input("hostname_dropdown", "value"),
        Input("data_range_picker", "start_date"),
        Input("data_range_picker", "end_date"),
    )
    def update_qos_options(hostname, start_date, end_date):
        """Update the QOS selection dropdown options."""
        if not hostname:
            return [{"label": "All QOS", "value": "all"}]
        
        # Get available QOS options
        qos_options = datastore.get_qos(hostname)
        
        # Create dropdown options
        options = [{"label": "All QOS", "value": "all"}]
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
    )
    def plot_job_duration_stacked(hostname, start_date, end_date, states, partitions, users, accounts, selected_qos):
        """
        Create a stacked bar plot showing job duration distribution by predefined thresholds.
        """
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            format_accounts=False,
        )
        
        if df.empty:
            return px.bar(title="No data available for selected filters")
        
        # Filter by selected QOS if specified
        if selected_qos and selected_qos != "all":
            df = df[df['QOS'] == selected_qos]
            qos_title = f" for QOS: {selected_qos}"
        else:
            qos_title = ""
        
        # Group by time period
        time_col = get_time_column(start_date, end_date)
        
        # Define job duration thresholds (in hours)
        thresholds = [0, 1, 4, 12, 24, 72, 168, float('inf')]
        
        # Define threshold labels
        threshold_labels = [
            "< 1h", 
            "1h - 4h", 
            "4h - 12h", 
            "12h - 24h", 
            "1d - 3d", 
            "3d - 7d",
            "> 7d"
        ]
        
        # Color scheme - using a sequential colormap from light to dark green
        colors = [
            "rgb(237, 248, 233)",  # very light green
            "rgb(199, 233, 192)",  # light green
            "rgb(161, 217, 155)",  # medium-light green
            "rgb(116, 196, 118)",  # medium green
            "rgb(65, 171, 93)",    # medium-dark green
            "rgb(35, 139, 69)",    # dark green
            "rgb(0, 90, 50)"       # very dark green
        ]
        
        # Initialize results dataframe
        results = []
        
        # Calculate job counts for each time period and duration threshold
        for period in sorted(df[time_col].unique()):
            period_df = df[df[time_col] == period]
            total_jobs = len(period_df)
            
            for i in range(len(thresholds) - 1):
                lower = thresholds[i]
                upper = thresholds[i + 1]
                label = threshold_labels[i]
                
                # Count jobs in this duration range
                count = ((period_df['Elapsed [h]'] >= lower) & 
                        (period_df['Elapsed [h]'] < upper)).sum()
                
                # Calculate percentage
                percentage = (count / total_jobs * 100) if total_jobs > 0 else 0
                
                results.append({
                    time_col: period,
                    'Job Duration': label,
                    'Count': count,
                    'Percentage': percentage,
                    'Total Jobs': total_jobs
                })
        
        # Convert to dataframe
        results_df = pd.DataFrame(results)
        
        # Create the stacked bar chart
        fig = px.bar(
            results_df,
            x=time_col,
            y="Percentage",
            color="Job Duration",
            title=f"Job Duration Distribution by Period{qos_title}",
            labels={
                "Percentage": "Percentage of Jobs (%)",
                time_col: "Time Period"
            },
            color_discrete_map={threshold_labels[i]: colors[i] for i in range(len(threshold_labels))},
            category_orders={"Job Duration": threshold_labels},
            hover_data=["Count", "Total Jobs"],
        )
        
        # Improve layout
        fig.update_layout(
            legend_title_text="Job Duration",
            barmode="stack",
            yaxis=dict(
                title="Percentage of Jobs (%)",
                range=[0, 100]
            ),
            xaxis=dict(
                title=time_col,
                tickangle=45 if len(results_df[time_col].unique()) > 12 else 0
            ),
            margin=dict(t=50, l=50, r=20, b=100),  # More space at bottom for labels
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        
        # Add hover template
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
    )
    def plot_waiting_times_stacked(hostname, start_date, end_date, states, partitions, users, accounts, selected_qos):
        """
        Create a stacked bar plot showing waiting time distribution by predefined thresholds.
        """
        df = datastore.filter(
            hostname=hostname,
            start_date=start_date,
            end_date=end_date,
            states=states,
            partitions=partitions,
            users=users,
            accounts=accounts,
            format_accounts=False,
        )
        
        if df.empty:
            return px.bar(title="No data available for selected filters")
        
        # Filter by selected QOS if specified
        if selected_qos and selected_qos != "all":
            df = df[df['QOS'] == selected_qos]
            qos_title = f" for QOS: {selected_qos}"
        else:
            qos_title = ""
        
        # Group by time period
        time_col = get_time_column(start_date, end_date)
        
        # Define waiting time thresholds (in hours)
        thresholds = [0, 0.5, 1, 4, 12, 24, float('inf')]
        
        # Define threshold labels
        threshold_labels = [
            "< 30min", 
            "30min - 1h", 
            "1h - 4h", 
            "4h - 12h", 
            "12h - 24h", 
            "> 24h"
        ]
        
        colors = [
            "rgb(255, 245, 240)",  # very light red
            "rgb(254, 224, 210)",  # light red
            "rgb(252, 187, 161)",  # medium-light red
            "rgb(252, 146, 114)",  # medium red
            "rgb(239, 59, 44)",    # medium-dark red
            "rgb(153, 0, 13)"      # dark red
        ]
        
        # Initialize results dataframe
        results = []
        
        # Calculate job counts for each time period and waiting time threshold
        for period in sorted(df[time_col].unique()):
            period_df = df[df[time_col] == period]
            total_jobs = len(period_df)
            
            for i in range(len(thresholds) - 1):
                lower = thresholds[i]
                upper = thresholds[i + 1]
                label = threshold_labels[i]
                
                # Count jobs in this waiting time range
                count = ((period_df['WaitingTime [h]'] >= lower) & 
                        (period_df['WaitingTime [h]'] < upper)).sum()
                
                # Calculate percentage
                percentage = (count / total_jobs * 100) if total_jobs > 0 else 0
                
                results.append({
                    time_col: period,
                    'Waiting Time': label,
                    'Count': count,
                    'Percentage': percentage,
                    'Total Jobs': total_jobs
                })
        
        # Convert to dataframe
        results_df = pd.DataFrame(results)
        
        # Create the stacked bar chart
        fig = px.bar(
            results_df,
            x=time_col,
            y="Percentage",
            color="Waiting Time",
            title=f"Waiting Time Distribution by Period{qos_title}",
            labels={
                "Percentage": "Percentage of Jobs (%)",
                time_col: "Time Period"
            },
            color_discrete_map={threshold_labels[i]: colors[i] for i in range(len(threshold_labels))},
            category_orders={"Waiting Time": threshold_labels},
            hover_data=["Count", "Total Jobs"],
        )
        
        # Improve layout
        fig.update_layout(
            legend_title_text="Waiting Time",
            barmode="stack",
            yaxis=dict(
                title="Percentage of Jobs (%)",
                range=[0, 100]
            ),
            xaxis=dict(
                title=time_col,
                tickangle=45 if len(results_df[time_col].unique()) > 12 else 0
            ),
            margin=dict(t=50, l=50, r=20, b=100),  # More space at bottom for labels
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="center",
                x=0.5
            )
        )
        
        # Add hover template
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
        """
        Show the account formatting options only when Account is selected as the color factor.
        """
        if color_by == "Account":
            return {"display": "block"}
        return {"display": "none"}
