from flask import Blueprint
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import os, json
import logging
from db import query_logs, get_live_logs

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

GRAPH_STORAGE_FILE = "stored_graphs.json"
stored_graphs = []

def save_graphs_to_file():
    """Save the stored graphs to a JSON file."""
    with open(GRAPH_STORAGE_FILE, "w") as f:
        json.dump(stored_graphs, f)

def load_graphs_from_file():
    """Load stored graphs from a JSON file."""
    if os.path.exists(GRAPH_STORAGE_FILE):
        with open(GRAPH_STORAGE_FILE, "r") as f:
            return json.load(f)
    return []

stored_graphs = load_graphs_from_file()

def init_dashboard_dash(app):
    dash_create = Dash(
        __name__,
        server=app,
        url_base_pathname='/dashboard/create_dash/',
        external_stylesheets=[dbc.themes.BOOTSTRAP]
    )

    dash_create.layout = dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Create a New Dashboard", className="text-center text-white bg-dark p-3 mb-4 rounded"))
        ]),

        dbc.Row([
            dbc.Col([
                dbc.Label("Log Type (Required)", className="fw-bold text-white"),
                dcc.Dropdown(
                    id='log-type-dropdown',
                    options=[
                        {'label': 'Apache2 Logs', 'value': 'apache2_logs'},
                        {'label': 'Nginx Logs', 'value': 'nginx_logs'}
                    ],
                    placeholder="Select Log Type",
                    className="mb-3",
                    style={'color': '#000000'}  # 드롭다운 텍스트 색상 검정으로 변경
                ),
                dbc.Label("X-Axis (Required)", className="fw-bold text-white"),
                dcc.Dropdown(id='x-axis-dropdown', placeholder='Select X-axis', className="mb-3", style={'color': '#000000'}),
                dbc.Label("Y-Axis (Required)", className="fw-bold text-white"),
                dcc.Dropdown(id='y-axis-dropdown', placeholder='Select Y-axis', className="mb-3", style={'color': '#000000'}),
                dbc.Label("Color (Optional)", className="fw-bold text-white"),
                dcc.Dropdown(id='color-dropdown', placeholder='Select Color', className="mb-3", style={'color': '#000000'}),
                dbc.Label("Graph Title (Required)", className="fw-bold text-white"),
                dbc.Input(id='graph-title', type='text', placeholder='Enter Graph Title', className="mb-3"),
                dbc.Label("Graph Type (Required)", className="fw-bold text-white"),
                dcc.Dropdown(
                    id='graph-type-dropdown',
                    options=[
                        {'label': 'Bar Chart', 'value': 'bar'},
                        {'label': 'Line Chart', 'value': 'line'},
                        {'label': 'Scatter Plot', 'value': 'scatter'},
                        {'label': 'Histogram', 'value': 'histogram'},
                        {'label': 'Heatmap', 'value': 'heatmap'},
                        {'label': 'Count Plot', 'value': 'count'}
                    ],
                    placeholder="Select Graph Type",
                    className="mb-3",
                    style={'color': '#000000'}
                ),
            ], md=6, className="bg-dark text-white rounded p-4"),
        ], justify="center"),

        dbc.Row([
            dbc.Col([
                dbc.Button("Preview", id="preview-btn", n_clicks=0, color="primary", className="me-2"),
                dbc.Button("Confirm", id="confirm-btn", n_clicks=0, color="success", className="me-2"),
                dbc.Button("Reset", id="reset-btn", n_clicks=0, color="danger")
            ], className="text-center mt-4")
        ]),

        dbc.Row([
            dbc.Col(html.Div(id='preview-container', className="text-white mt-4"))
        ])
    ], fluid=True, className="bg-dark vh-100 text-white")


    # Callbacks
    @dash_create.callback(
        Output('x-axis-dropdown', 'options', allow_duplicate=True),
        Output('y-axis-dropdown', 'options', allow_duplicate=True),
        Output('color-dropdown', 'options', allow_duplicate=True),
        Input('log-type-dropdown', 'value'),
        prevent_initial_call=True
    )
    def update_dropdowns(log_type):
        if not log_type:
            return [], [], []

        rows = query_logs(f"PRAGMA table_info({log_type})")
        if not rows:
            return [], [], []

        columns = [{'label': col[1], 'value': col[1]} for col in rows]
        count_option = [{'label': 'Count', 'value': 'count'}]
        return columns + count_option, columns + count_option, columns

    @dash_create.callback(
        Output('preview-container', 'children', allow_duplicate=True),
        Input('preview-btn', 'n_clicks'),
        State('log-type-dropdown', 'value'),
        State('x-axis-dropdown', 'value'),
        State('y-axis-dropdown', 'value'),
        State('color-dropdown', 'value'),
        State('graph-title', 'value'),
        State('graph-type-dropdown', 'value'),
        prevent_initial_call=True
    )
    def preview_graph(n_clicks, log_type, x_axis, y_axis, color, title, graph_type):
        if not log_type or not x_axis or not y_axis:
            return dbc.Alert("Please select Log Type, X-axis, and Y-axis.", color="danger")

        df = get_live_logs(log_type, x_axis, y_axis, color)
        if df.empty:
            return dbc.Alert("No data available for the selected criteria.", color="warning")

        if color and color not in df.columns:
            color = None

        try:
            if graph_type == 'count':
                df = df.groupby(x_axis).size().reset_index(name='count')
                fig = px.bar(df, x=x_axis, y='count', color=color, title=title or "Count Plot")
            elif graph_type == 'bar':
                fig = px.bar(df, x=x_axis, y=y_axis, color=color, title=title or "Bar Chart")
            elif graph_type == 'line':
                fig = px.line(df, x=x_axis, y=y_axis, color=color, title=title or "Line Chart")
            elif graph_type == 'scatter':
                fig = px.scatter(df, x=x_axis, y=y_axis, color=color, title=title or "Scatter Plot")
            elif graph_type == 'histogram':
                fig = px.histogram(df, x=x_axis, y=y_axis, color=color, title=title or "Histogram")
            elif graph_type == 'heatmap':
                fig = px.density_heatmap(df, x=x_axis, y=y_axis, z=color, title=title or "Heatmap")

            return dcc.Graph(figure=fig, className="bg-light rounded")
        except Exception as e:
            logging.error(f"Failed to generate graph: {e}")
            return dbc.Alert(f"Error generating graph: {str(e)}", color="danger")

    @dash_create.callback(
        Output('preview-container', 'children', allow_duplicate=True),
        Input('confirm-btn', 'n_clicks'),
        State('log-type-dropdown', 'value'),
        State('x-axis-dropdown', 'value'),
        State('y-axis-dropdown', 'value'),
        State('color-dropdown', 'value'),
        State('graph-title', 'value'),
        State('graph-type-dropdown', 'value'),
        prevent_initial_call=True
    )
    def confirm_graph(n_clicks, log_type, x_axis, y_axis, color, title, graph_type):
        if not title:
            return dbc.Alert("Graph title is required.", color="danger")

        global stored_graphs
        graph_meta = {
            "log_type": log_type,
            "x_axis": x_axis,
            "y_axis": y_axis,
            "color": color,
            "title": title,
            "graph_type": graph_type
        }
        stored_graphs.append(graph_meta)
        save_graphs_to_file()

        return dbc.Alert("Graph confirmed and saved to dashboard.", color="success")

    return dash_create


def init_dashboard_view_dash(app):
    dash_view = Dash(
        __name__,
        server=app,
        url_base_pathname='/dashboard/',
        external_stylesheets=[dbc.themes.BOOTSTRAP]
    )

    dash_view.layout = dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Dashboard View", className="text-center text-white bg-dark p-3 mb-4 rounded"))
        ]),

        dbc.Row([
            dbc.Col(dbc.Button("Create Dashboard", href="/dashboard/create_dash/", color="primary", className="w-100 mb-3", target="_blank"))
        ]),

        dbc.Row([
            dbc.Col(html.Div(id='graphs-container'), className="p-3 bg-dark text-white rounded")
        ]),

        dcc.Interval(id='refresh-interval', interval=10000, n_intervals=0)
    ], fluid=True, className="bg-dark vh-100 text-white")

    @dash_view.callback(
        Output('graphs-container', 'children'),
        Input('refresh-interval', 'n_intervals')
    )
    def update_dashboard(n_intervals):
        live_graphs = []
        global stored_graphs
        stored_graphs = load_graphs_from_file()  # Reload the latest saved graphs

        for graph_meta in stored_graphs:
            df = get_live_logs(graph_meta['log_type'], graph_meta['x_axis'], graph_meta['y_axis'], graph_meta['color'])
            if df.empty:
                live_graphs.append(
                    dbc.Alert("No data available for this graph.", color="warning", className="text-center")
                )
                continue

            if graph_meta['graph_type'] == 'count':
                df = df.groupby(graph_meta['x_axis']).size().reset_index(name='count')
                fig = px.bar(df, x=graph_meta['x_axis'], y='count', title=graph_meta['title'])
            elif graph_meta['graph_type'] == 'bar':
                fig = px.bar(df, x=graph_meta['x_axis'], y=graph_meta['y_axis'], color=graph_meta['color'], title=graph_meta['title'])
            elif graph_meta['graph_type'] == 'line':
                fig = px.line(df, x=graph_meta['x_axis'], y=graph_meta['y_axis'], color=graph_meta['color'], title=graph_meta['title'])
            elif graph_meta['graph_type'] == 'scatter':
                fig = px.scatter(df, x=graph_meta['x_axis'], y=graph_meta['y_axis'], color=graph_meta['color'], title=graph_meta['title'])
            elif graph_meta['graph_type'] == 'histogram':
                fig = px.histogram(df, x=graph_meta['x_axis'], y=graph_meta['y_axis'], color=graph_meta['color'], title=graph_meta['title'])
            elif graph_meta['graph_type'] == 'heatmap':
                fig = px.density_heatmap(df, x=graph_meta['x_axis'], y=graph_meta['y_axis'], z=graph_meta['color'], title=graph_meta['title'])

            live_graphs.append(
                dbc.Card(
                    [
                        dbc.CardHeader(html.H5(graph_meta['title'], className="text-center text-white")),
                        dbc.CardBody(dcc.Graph(figure=fig, className="bg-light")),
                    ],
                    className="mb-3 bg-secondary text-white"
                )
            )

        if not live_graphs:
            return dbc.Alert("No graphs to display. Create one now!", color="warning", className="text-center mt-5")

        return live_graphs

    return dash_view
