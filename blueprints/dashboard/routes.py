from flask import Blueprint, redirect, url_for, request, jsonify
from dash import Dash, dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
from db import query_logs

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# 저장된 그래프 리스트
stored_graphs = []

def init_dashboard_dash(app):
    dash_app = Dash(__name__, server=app, url_base_pathname='/dashboard/')

    # Dash Layout
    dash_app.layout = html.Div([
        html.H1("Create a New Dashboard", style={'textAlign': 'center'}),

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

        html.Button("Preview", id="preview-btn", n_clicks=0),
        html.Div(id='preview-container', style={'marginTop': '20px'})
    ])

    # 콜백: Log Type 선택에 따라 드롭다운 옵션 업데이트
    @dash_app.callback(
        [Output('x-axis-dropdown', 'options'),
         Output('y-axis-dropdown', 'options'),
         Output('color-dropdown', 'options')],
        [Input('log-type-dropdown', 'value')]
    )
    def update_dropdowns(log_type):
        if not log_type:
            return [], [], []

        try:
            # Log Type에 따라 컬럼 정보를 가져옴
            query = f"PRAGMA table_info({log_type})"
            rows = query_logs(query)
            if not rows:
                return [], [], []
            columns = [{'label': col[1], 'value': col[1]} for col in rows]
            return columns, columns, columns
        except Exception as e:
            print(f"Error fetching columns: {e}")
            return [], [], []

    # 콜백: Preview 버튼 클릭 시 그래프 생성
    @dash_app.callback(
        Output('preview-container', 'children'),
        [Input('preview-btn', 'n_clicks')],
        [State('log-type-dropdown', 'value'),
         State('x-axis-dropdown', 'value'),
         State('y-axis-dropdown', 'value'),
         State('color-dropdown', 'value'),
         State('graph-title', 'value')]
    )
    def preview_graph(n_clicks, log_type, x_axis, y_axis, color, title):
        if n_clicks == 0:
            return ""

        if not log_type or not x_axis or not y_axis:
            return html.Div("Please select Log Type, X-axis, and Y-axis.", style={'color': 'red'})

        # Query logs and generate graph
        query = f"SELECT {x_axis}, {y_axis}, {color} FROM {log_type}" if color else f"SELECT {x_axis}, {y_axis} FROM {log_type}"
        rows = query_logs(query)
        if not rows:
            return html.Div("No data available for the selected criteria.", style={'color': 'red'})

        df = pd.DataFrame(rows, columns=[x_axis, y_axis, color] if color else [x_axis, y_axis])
        fig = px.bar(
            df, x=x_axis, y=y_axis, color=color,
            labels={x_axis: x_axis.capitalize(), y_axis: y_axis.capitalize()},
            title=title or "Custom Graph",
            template='plotly_white'
        )
        return dcc.Graph(figure=fig)

    return dash_app


def init_create_dash(app):
    dash_create = Dash(__name__, server=app, url_base_pathname='/dashboard/create_dash/')

    # Layout for creating a dashboard
    dash_create.layout = html.Div([
        html.H1("Create a New Dashboard", style={'textAlign': 'center'}),

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

        html.Button("Preview", id="preview-btn", n_clicks=0),
        html.Button("Save Dashboard", id="save-btn", n_clicks=0, style={'marginLeft': '10px'}),

        html.Div(id='preview-container', style={'marginTop': '20px'})
    ])

    # Update dropdowns based on selected log type
    @dash_create.callback(
        [Output('x-axis-dropdown', 'options'),
         Output('y-axis-dropdown', 'options'),
         Output('color-dropdown', 'options')],
        [Input('log-type-dropdown', 'value')]
    )
    def update_dropdowns(log_type):
        if not log_type:
            return [], [], []

        try:
            query = f"PRAGMA table_info({log_type})"
            rows = query_logs(query)
            if not rows:
                return [], [], []
            columns = [{'label': col[1], 'value': col[1]} for col in rows]
            return columns, columns, columns
        except Exception as e:
            print(f"Error fetching columns: {e}")
            return [], [], []

    # Preview graph
    @dash_create.callback(
        Output('preview-container', 'children'),
        [Input('preview-btn', 'n_clicks')],
        [State('log-type-dropdown', 'value'),
         State('x-axis-dropdown', 'value'),
         State('y-axis-dropdown', 'value'),
         State('color-dropdown', 'value'),
         State('graph-title', 'value')]
    )
    def preview_graph(n_clicks, log_type, x_axis, y_axis, color, title):
        if n_clicks == 0:
            return ""

        if not log_type or not x_axis or not y_axis:
            return html.Div("Please select Log Type, X-axis, and Y-axis.", style={'color': 'red'})

        # Query data and generate graph
        query = f"SELECT {x_axis}, {y_axis}, {color} FROM {log_type}" if color else f"SELECT {x_axis}, {y_axis} FROM {log_type}"
        rows = query_logs(query)
        if not rows:
            return html.Div("No data available for the selected criteria.", style={'color': 'red'})

        df = pd.DataFrame(rows, columns=[x_axis, y_axis, color] if color else [x_axis, y_axis])
        fig = px.bar(
            df, x=x_axis, y=y_axis, color=color,
            labels={x_axis: x_axis.capitalize(), y_axis: y_axis.capitalize()},
            title=title or "Custom Graph",
            template='plotly_white'
        )
        return dcc.Graph(figure=fig)

    # Save graph
    @dash_create.callback(
        Output('preview-container', 'children'),
        [Input('save-btn', 'n_clicks')],
        [State('log-type-dropdown', 'value'),
         State('x-axis-dropdown', 'value'),
         State('y-axis-dropdown', 'value'),
         State('color-dropdown', 'value'),
         State('graph-title', 'value')]
    )
    def save_graph(n_clicks, log_type, x_axis, y_axis, color, title):
        if n_clicks == 0:
            return ""

        if not log_type or not x_axis or not y_axis:
            return html.Div("Please select Log Type, X-axis, and Y-axis.", style={'color': 'red'})

        # Save graph to stored_graphs
        query = f"SELECT {x_axis}, {y_axis}, {color} FROM {log_type}" if color else f"SELECT {x_axis}, {y_axis} FROM {log_type}"
        rows = query_logs(query)
        df = pd.DataFrame(rows, columns=[x_axis, y_axis, color] if color else [x_axis, y_axis])
        fig = px.bar(
            df, x=x_axis, y=y_axis, color=color,
            labels={x_axis: x_axis.capitalize(), y_axis: y_axis.capitalize()},
            title=title or "Custom Graph",
            template='plotly_white'
        )
        graph_html = fig.to_html(full_html=False)
        stored_graphs.append({"graph_html": graph_html, "title": title})
        return html.Div("Graph saved successfully.", style={'color': 'green'})

    return dash_create

