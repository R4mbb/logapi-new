from flask import Blueprint, request, jsonify
from dash import Dash, dcc, html, Input, Output, State
from dash.dependencies import ALL
import pandas as pd
import plotly.express as px
import plotly.io as pio
import json

from db import query_logs
from .blueprints.collector import start_log_collector  # 기존 Collector를 대시보드와 연결

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

# Initialize global variables
stored_graphs = []
GRAPH_STORAGE_FILE = "stored_graphs.json"

# Save and load graphs
def save_graphs_to_file():
    with open(GRAPH_STORAGE_FILE, "w") as f:
        json.dump(stored_graphs, f)

def load_graphs_from_file():
    if os.path.exists(GRAPH_STORAGE_FILE):
        with open(GRAPH_STORAGE_FILE, "r") as f:
            return json.load(f)
    return []

stored_graphs = load_graphs_from_file()


def init_dashboard_dash(app):
    dash_view = Dash(__name__, server=app, url_base_pathname='/dashboard/')

    # Dash Layout
    dash_view.layout = html.Div([
        html.H1("Dashboard", style={'textAlign': 'center'}),
        html.Div(id='graphs-container', style={'marginTop': '20px'}),
        html.Button("Refresh Graphs", id='refresh-btn', n_clicks=0),
        dcc.Interval(id='refresh-interval', interval=10 * 1000, n_intervals=0)  # 10초 주기
    ])

    # 실시간 데이터를 업데이트하는 콜백
    @dash_view.callback(
        Output('graphs-container', 'children'),
        [Input('refresh-btn', 'n_clicks'), Input('refresh-interval', 'n_intervals')],
    )
    def refresh_graphs(n_clicks, n_intervals):
        global stored_graphs
        stored_graphs = load_graphs_from_file()
        
        # 쿼리된 로그 데이터를 처리
        for graph in stored_graphs:
            try:
                figure = pio.from_json(graph['graph_html'])  # 기존 그래프 로드
                log_type = graph.get('log_type', 'apache2_logs')  # 그래프의 로그 타입
                x_axis = figure['data'][0]['x'][0]  # X축 필드
                y_axis = figure['data'][0]['y'][0]  # Y축 필드

                # 데이터베이스에서 새로운 데이터 가져오기
                query = f"SELECT {x_axis}, {y_axis} FROM {log_type} ORDER BY timestamp DESC LIMIT 100"
                new_data = query_logs(query)
                if new_data:
                    df = pd.DataFrame(new_data, columns=[x_axis, y_axis])
                    figure['data'][0]['x'] = df[x_axis].tolist()
                    figure['data'][0]['y'] = df[y_axis].tolist()

                    graph['graph_html'] = pio.to_json(figure)  # 그래프 업데이트
            except Exception as e:
                print(f"Error updating graph {graph.get('title')}: {e}")

        save_graphs_to_file()

        # 그래프 렌더링
        return [
            html.Div([
                html.H5(graph['title']),
                dcc.Graph(figure=pio.from_json(graph['graph_html'])),
                html.Button("Delete", id={'type': 'delete-btn', 'index': idx}, style={'marginTop': '10px', 'color': 'red'})
            ], style={'marginBottom': '20px'})
            for idx, graph in enumerate(stored_graphs)
        ]

    # Delete 버튼 콜백
    @dash_view.callback(
        Output('graphs-container', 'children'),
        [Input({'type': 'delete-btn', 'index': ALL}, 'n_clicks')],
        prevent_initial_call=True
    )
    def delete_graph(delete_clicks):
        global stored_graphs
        if not any(delete_clicks):
            raise PreventUpdate

        stored_graphs = [graph for idx, graph in enumerate(stored_graphs) if not delete_clicks[idx]]
        save_graphs_to_file()

        return [
            html.Div([
                html.H5(graph['title']),
                dcc.Graph(figure=pio.from_json(graph['graph_html'])),
                html.Button("Delete", id={'type': 'delete-btn', 'index': idx}, style={'marginTop': '10px', 'color': 'red'})
            ], style={'marginBottom': '20px'})
            for idx, graph in enumerate(stored_graphs)
        ]

    return dash_view


@dashboard_bp.route('/')
def start_dashboard():
    return "Dashboard is running. Visit /dashboard/ to view the dashboards."


@dashboard_bp.route('/start_collector', methods=['POST'])
def start_collector():
    """Start the log collector in a separate thread."""
    try:
        start_log_collector()  # Start the collector to monitor logs
        return jsonify({"message": "Collector started successfully."}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

