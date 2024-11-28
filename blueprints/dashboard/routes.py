from flask import Blueprint, request, jsonify
from dash import Dash, dcc, html, Input, Output, State
from dash.dependencies import ALL
import pandas as pd
import plotly.express as px
import plotly.io as pio
import os
import json

from db import query_logs

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Constants
GRAPH_STORAGE_FILE = "stored_graphs.json"

# Helper functions to save and load graphs
def save_graphs_to_file(graphs):
    try:
        with open(GRAPH_STORAGE_FILE, "w") as f:
            json.dump(graphs, f)
    except Exception as e:
        print(f"Error saving graphs to file: {e}")

def load_graphs_from_file():
    if os.path.exists(GRAPH_STORAGE_FILE):
        try:
            with open(GRAPH_STORAGE_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading graphs from file: {e}")
    return []

# Initialize the global variable
stored_graphs = load_graphs_from_file()

def init_dashboard_dash(app):
    dash_create = Dash(__name__, server=app, url_base_pathname='/dashboard/create_dash/')

    # Dash Layout
    dash_create.layout = html.Div([
        html.H1("Create a New Dashboard", style={'textAlign': 'center'}),

        # Navigation button to go back to dashboard view
        html.Div([
            html.A("Go to Dashboard", href="/dashboard/", className="btn btn-secondary"),
        ], style={'textAlign': 'center', 'marginBottom': '20px'}),

        # Dropdowns for graph creation
        html.Label("Log Type"),
        dcc.Dropdown(
            id='log-type-dropdown',
            options=[
                {'label': 'Apache2 Logs', 'value': 'apache2_logs'},
                {'label': 'Nginx Logs', 'value': 'nginx_logs'}
            ],
            placeholder="Select Log Type"
        ),
        html.Label("X-Axis"),
        dcc.Dropdown(id='x-axis-dropdown', placeholder='Select X-axis'),
        html.Label("Y-Axis"),
        dcc.Dropdown(id='y-axis-dropdown', placeholder='Select Y-axis'),
        html.Label("Color (Optional)"),
        dcc.Dropdown(id='color-dropdown', placeholder='Select Color'),
        html.Label("Graph Title"),
        dcc.Input(id='graph-title', type='text', placeholder='Enter Graph Title'),
        html.Label("Graph Type"),
        dcc.Dropdown(
            id='graph-type-dropdown',
            options=[
                {'label': 'Bar Chart', 'value': 'bar'},
                {'label': 'Line Chart', 'value': 'line'},
                {'label': 'Scatter Plot', 'value': 'scatter'},
                {'label': 'Histogram', 'value': 'histogram'},
                {'label': 'Heatmap', 'value': 'heatmap'},
            ],
            placeholder="Select Graph Type"
        ),

        # Buttons
        html.Div([
            html.Button("Preview", id="preview-btn", n_clicks=0),
            html.Button("Confirm", id="confirm-btn", n_clicks=0, style={'marginLeft': '10px'}),
            html.Button("Reset", id="reset-btn", n_clicks=0, style={'marginLeft': '10px', 'backgroundColor': 'red', 'color': 'white'}),
        ], style={'marginTop': '20px'}),

        # Preview container
        html.Div(id='preview-container', style={'marginTop': '20px'})
    ])

    @dash_create.callback(
        [Output('x-axis-dropdown', 'options', allow_duplicate=True),
         Output('y-axis-dropdown', 'options', allow_duplicate=True),
         Output('color-dropdown', 'options', allow_duplicate=True)],
        [Input('log-type-dropdown', 'value')],
        prevent_initial_call=True
    )
    def update_dropdowns(log_type):
        if not log_type:
            return [], [], []

        query = f"PRAGMA table_info({log_type})"
        rows = query_logs(query)
        if not rows:
            return [], [], []

        columns = [{'label': col[1], 'value': col[1]} for col in rows]
        return columns, columns, columns

    @dash_create.callback(
        Output('preview-container', 'children', allow_duplicate=True),
        [Input('preview-btn', 'n_clicks')],
        [
            State('log-type-dropdown', 'value'),
            State('x-axis-dropdown', 'value'),
            State('y-axis-dropdown', 'value'),
            State('color-dropdown', 'value'),
            State('graph-title', 'value'),
            State('graph-type-dropdown', 'value')
        ],
        prevent_initial_call=True
    )
    def preview_graph(n_clicks, log_type, x_axis, y_axis, color, title, graph_type):
        if not log_type or not x_axis or not y_axis:
            return html.Div("Please select Log Type, X-axis, and Y-axis.", style={'color': 'red'})

        query = f"SELECT {x_axis}, {y_axis}, {color} FROM {log_type}" if color else f"SELECT {x_axis}, {y_axis} FROM {log_type}"
        rows = query_logs(query)
        if not rows:
            return html.Div("No data available for the selected criteria.", style={'color': 'red'})

        df = pd.DataFrame(rows, columns=[x_axis, y_axis, color] if color else [x_axis, y_axis])

        # Choose graph type
        fig = px.bar(df, x=x_axis, y=y_axis, color=color, title=title or "Bar Chart") if graph_type == 'bar' else px.line(df, x=x_axis, y=y_axis, color=color, title=title or "Line Chart")
        return dcc.Graph(figure=fig)

    @dash_create.callback(
        Output('preview-container', 'children', allow_duplicate=True),
        [Input('confirm-btn', 'n_clicks')],
        [State('preview-container', 'children'), State('graph-title', 'value')],
        prevent_initial_call=True
    )
    def confirm_graph(n_clicks, preview_content, title):
        if not title:
            return html.Div("Graph title is required.", style={'color': 'red'})

        global stored_graphs
        stored_graphs.append({"graph_html": preview_content, "title": title})
        save_graphs_to_file(stored_graphs)

        return html.Div("Graph confirmed and saved.", style={'color': 'green'})

    return dash_create


def init_dashboard_view_dash(app):
    dash_view = Dash(__name__, server=app, url_base_pathname='/dashboard/')

    # Dash Layout
    dash_view.layout = html.Div([
        html.H1("Dashboard View", style={'textAlign': 'center'}),

        # Navigation button to create dashboard
        html.Div([
            html.A("Create New Dashboard", href="/dashboard/create_dash/", className="btn btn-primary"),
        ], style={'textAlign': 'center', 'marginBottom': '20px'}),

        html.Div(id='graphs-container'),
        html.Button("Refresh Graphs", id='refresh-btn', n_clicks=0, style={'marginTop': '20px'}),
    ])

    @dash_view.callback(
        Output('graphs-container', 'children'),
        [Input('refresh-btn', 'n_clicks')],
    )
    def render_graphs(n_clicks):
        """Render graphs dynamically from stored JSON."""
        try:
            graphs = load_graphs_from_file()
            if not graphs:
                return html.Div("No graphs available.", style={'color': 'red'})

            # Ensure proper JSON format for Plotly Graphs
            graph_components = []
            for graph in graphs:
                try:
                    graph_title = graph.get('title', 'Untitled Graph')
                    graph_html = graph.get('graph_html', None)

                    # Check if graph_html is valid JSON
                    if graph_html:
                        figure = pio.from_json(graph_html)
                        graph_components.append(
                            html.Div([
                                html.H5(graph_title),
                                dcc.Graph(figure=figure),
                                html.Button(
                                    "Delete",
                                    id={'type': 'delete-btn', 'index': len(graph_components)},
                                    style={'marginTop': '10px', 'color': 'red'}
                                )
                            ], style={'marginBottom': '20px'})
                        )
                except Exception as e:
                    print(f"Error converting graph for title {graph.get('title')}: {e}")
                    continue

            return graph_components
        except Exception as e:
            print(f"Error rendering graphs: {e}")
            return html.Div("Error loading graphs.", style={'color': 'red'})


    return dash_view

