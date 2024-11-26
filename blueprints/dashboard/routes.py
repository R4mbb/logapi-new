from flask import Blueprint, render_template, request, jsonify
from db import query_logs

import pandas as pd
import plotly.express as px
import os, json

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

STORAGE_FILE = 'stored_graphs.json'

def load_graphs():
    """Load graphs from JSON file."""
    if os.path.exists(STORAGE_FILE):
        with open(STORAGE_FILE, 'r') as f:
            return json.load(f)
    return []

def save_graphs():
    """Save graphs to JSON file."""
    with open(STORAGE_FILE, 'w') as f:
        json.dump(stored_graphs, f)

@dashboard_bp.route('/')
def dashboard():
    """Render dashboard with stored graphs."""
    #print("Stored Graphs:", stored_graphs)  # 디버깅용 출력
    return render_template('dashboard.html', graphs=stored_graphs)

@dashboard_bp.route('/columns', methods=['GET'])
def get_columns():
    """Fetch column names from the logs table."""
    query = "PRAGMA table_info(logs)"
    rows = query_logs(query)
    columns = [row[1] for row in rows]  # Extract column names
    return jsonify(columns)

@dashboard_bp.route('/create_graph', methods=['GET'])
def create_graph_page():
    """Render the graph creation page."""
    return render_template('create_graph.html')

@dashboard_bp.route('/create_graph', methods=['POST'])
def create_graph():
    """Generate a graph based on user-selected options."""
    data = request.json
    print("Request Data:", data)

    x_axis = data.get('x')
    y_axis = data.get('y')
    color = data.get('color')
    title = data.get('title')

    if not x_axis or not y_axis:
        return jsonify({"error": "X-axis and Y-axis must be selected."}), 400

    # 데이터베이스 쿼리
    query = f"SELECT {x_axis}, {y_axis}, {color} FROM logs" if color else f"SELECT {x_axis}, {y_axis} FROM logs"
    rows = query_logs(query)
    if not rows:
        print("Query Result Rows: Empty")
        return jsonify({"error": "No data available for the selected criteria."}), 404

    # 데이터프레임 생성
    columns = [x_axis, y_axis, color] if color else [x_axis, y_axis]
    try:
        df = pd.DataFrame(rows, columns=columns)
    except ValueError as e:
        print(f"DataFrame Error: {str(e)}")
        return jsonify({"error": f"Error processing data: {str(e)}"}), 400

    if df.empty:
        print("DataFrame is empty.")
        return jsonify({"error": "No data available for the selected criteria."}), 404

    # Plotly 그래프 생성
    try:
        fig = px.bar(
            df,
            x=x_axis, y=y_axis, color=color if color in df.columns else None,
            labels={x_axis: x_axis.capitalize(), y_axis: y_axis.capitalize()},
            title=title or "Custom Graph",
            template='plotly_white'
        )
        fig.update_layout(margin=dict(l=20, r=20, t=40, b=20))
        graph_html = fig.to_html(full_html=False)
        return jsonify({"graph": graph_html, "data": data})  # 데이터 반환
    except Exception as e:
        print(f"Plotly Error: {str(e)}")
        return jsonify({"error": f"Error generating graph: {str(e)}"}), 500



# 저장된 그래프 목록
stored_graphs = load_graphs()

@dashboard_bp.route('/save_graph', methods=['POST'])
def save_graph():
    """Save the generated graph to the dashboard."""
    data = request.json
    graph_html = data.get("graph_html")
    title = data.get("title")

    if not graph_html or not title:
        return jsonify({"error": "Invalid graph data."}), 400

    # 그래프 저장
    stored_graphs.append({"graph_html": graph_html, "title": title})
    save_graphs()  # 파일에 저장
    return jsonify({"message": "Graph saved successfully."}), 200

@dashboard_bp.route('/delete_graph', methods=['POST'])
def delete_graph():
    """Delete a graph from the dashboard."""
    data = request.json
    title = data.get("title")

    if not title:
        return jsonify({"error": "Graph title is required."}), 400

    # 삭제할 그래프 찾기
    global stored_graphs
    stored_graphs = [graph for graph in stored_graphs if graph["title"] != title]

    save_graphs()  # 파일에 저장
    return jsonify({"message": "Graph deleted successfully."}), 200

@dashboard_bp.route('/update_order', methods=['POST'])
def update_order():
    """Update the order of graphs in the dashboard."""
    data = request.json
    order = data.get("order")

    if not order or not isinstance(order, list):
        return jsonify({"error": "Invalid order data."}), 400

    # 새로운 순서에 따라 stored_graphs 정렬
    global stored_graphs
    new_graphs = []
    for title in order:
        for graph in stored_graphs:
            if graph["title"] == title:
                new_graphs.append(graph)
                break

    stored_graphs = new_graphs
    save_graphs()  # 파일에 저장
    return jsonify({"message": "Graph order updated successfully."}), 200

