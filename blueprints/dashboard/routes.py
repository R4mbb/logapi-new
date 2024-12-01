from flask import Blueprint
from dash import Dash, dcc, html, Input, Output, State
from dash.exceptions import PreventUpdate
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
    dash_create = Dash(__name__, server=app, url_base_pathname='/dashboard/create_dash/')

    dash_create.layout = html.Div([
        html.H1("Create a New Dashboard", style={
            'textAlign': 'center',
            'color': '#f0f0f0',
            'marginBottom': '20px',
            'backgroundColor': '#1c1c1c',
            'padding': '10px',
            'borderRadius': '5px'
        }),

        html.Div([
            html.Label("Log Type (Required)", style={'fontWeight': 'bold', 'color': '#f0f0f0'}),
            dcc.Dropdown(
                id='log-type-dropdown',
                options=[
                    {'label': 'Apache2 Logs', 'value': 'apache2_logs'},
                    {'label': 'Nginx Logs', 'value': 'nginx_logs'}
                ],
                placeholder="Select Log Type",
                style={'marginBottom': '15px', 'backgroundColor': '#2c2c2c', 'color': '#f0f0f0'}
            ),
            html.Label("X-Axis (Required)", style={'fontWeight': 'bold', 'color': '#f0f0f0'}),
            dcc.Dropdown(id='x-axis-dropdown', placeholder='Select X-axis',
                         style={'marginBottom': '15px', 'backgroundColor': '#2c2c2c', 'color': '#f0f0f0'}),
            html.Label("Y-Axis (Required)", style={'fontWeight': 'bold', 'color': '#f0f0f0'}),
            dcc.Dropdown(id='y-axis-dropdown', placeholder='Select Y-axis',
                         style={'marginBottom': '15px', 'backgroundColor': '#2c2c2c', 'color': '#f0f0f0'}),
            html.Label("Color (Optional)", style={'fontWeight': 'bold', 'color': '#f0f0f0'}),
            dcc.Dropdown(id='color-dropdown', placeholder='Select Color',
                         style={'marginBottom': '15px', 'backgroundColor': '#2c2c2c', 'color': '#f0f0f0'}),
            html.Label("Graph Title (Required)", style={'fontWeight': 'bold', 'color': '#f0f0f0'}),
            dcc.Input(id='graph-title', type='text', placeholder='Enter Graph Title',
                      style={'marginBottom': '15px', 'backgroundColor': '#2c2c2c', 'color': '#f0f0f0'}),
            html.Label("Graph Type (Required)", style={'fontWeight': 'bold', 'color': '#f0f0f0'}),
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
                style={'marginBottom': '15px', 'backgroundColor': '#2c2c2c', 'color': '#f0f0f0'}
            ),
        ], style={'maxWidth': '600px', 'margin': 'auto', 'padding': '20px', 'backgroundColor': '#1c1c1c', 'borderRadius': '5px'}),

        html.Div([
            html.Button("Preview", id="preview-btn", n_clicks=0, style={
                'marginRight': '10px', 'padding': '10px 20px', 'backgroundColor': '#007bff', 'color': '#fff'
            }),
            html.Button("Confirm", id="confirm-btn", n_clicks=0, style={
                'marginRight': '10px', 'padding': '10px 20px', 'backgroundColor': '#28a745', 'color': '#fff'
            }),
            html.Button("Reset", id="reset-btn", n_clicks=0, style={
                'padding': '10px 20px', 'backgroundColor': '#dc3545', 'color': '#fff'
            }),
        ], style={'textAlign': 'center', 'marginTop': '20px'}),

        html.Div(id='preview-container', style={'marginTop': '30px', 'textAlign': 'center', 'color': '#f0f0f0'})
    ], style={'backgroundColor': '#121212', 'padding': '0', 'margin': '0', 'minHeight': '100vh', 'width': '100vw'})

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
            return html.Div("Please select Log Type, X-axis, and Y-axis.", style={'color': 'red'})

        df = get_live_logs(log_type, x_axis, y_axis, color)
        if df.empty:
            return html.Div("No data available for the selected criteria.", style={'color': 'red'})

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

            return dcc.Graph(figure=fig)
        except Exception as e:
            logging.error(f"Failed to generate graph: {e}")
            return html.Div(f"Error generating graph: {str(e)}", style={'color': 'red'})

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
            return html.Div("Graph title is required.", style={'color': 'red'})

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

        return html.Div("Graph confirmed and saved to dashboard.", style={'color': 'green'})

    return dash_create


def init_dashboard_view_dash(app):
    dash_view = Dash(__name__, server=app, url_base_pathname='/dashboard/')

    dash_view.layout = html.Div([
        html.Div([
            html.H1("Dashboard View", style={
                'textAlign': 'center',
                'color': '#f0f0f0',
                'backgroundColor': '#1c1c1c',
                'padding': '10px',
                'borderRadius': '5px'
            }),
            html.A("Create Dashboard", href="/dashboard/create_dash/", className="btn btn-primary", 
                   style={'display': 'block', 'margin': '20px auto', 'textAlign': 'center',
                          'backgroundColor': '#007bff', 'color': '#fff', 'padding': '10px 20px', 'borderRadius': '5px'})
        ]),

        html.Div(id='graphs-container', style={'marginTop': '50px', 'padding': '20px'}),
        dcc.Interval(id='refresh-interval', interval=10000, n_intervals=0)
    ], style={'backgroundColor': '#121212', 'padding': '0', 'margin': '0', 'minHeight': '100vh', 'width': '100vw'})

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
                live_graphs.append(html.Div([
                    html.H5(f"Graph: {graph_meta['title']}"),
                    html.Div("No data available for this graph.", style={'color': 'red', 'textAlign': 'center'}),
                ]))
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

            live_graphs.append(html.Div([
                html.H5(f"Graph: {graph_meta['title']}"),
                dcc.Graph(figure=fig),
            ]))

        return live_graphs

    return dash_view

