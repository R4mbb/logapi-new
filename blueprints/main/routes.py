import psutil
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Output, Input
import plotly.graph_objs as go

def init_main_page(app):
    main_dash = Dash(
        __name__,
        server=app,
        url_base_pathname='/',
        external_stylesheets=[dbc.themes.BOOTSTRAP]
    )

    main_dash.layout = dbc.Container([
        # Title
        dbc.Row([
            dbc.Col(html.H1("Server Monitoring Dashboard", className="text-center text-white bg-dark p-3 mb-4 rounded"))
        ]),

        # Navigation Buttons
        dbc.Row([
            dbc.Col(dcc.Link(dbc.Button("Dashboard", color="primary", className="w-100 mb-2"), href="/dashboard/", target="_blank"), md=3),
            dbc.Col(dcc.Link(dbc.Button("Upload Logs", color="info", className="w-100 mb-2"), href="/upload_logs/", target="_blank"), md=3),
            dbc.Col(dcc.Link(dbc.Button("Recent Logs", color="success", className="w-100 mb-2"), href="/recent_logs/", target="_blank"), md=3),
        ], className="justify-content-center mb-4"),

        # Summary Section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Resource Summary", className="text-center text-white")),
                    dbc.CardBody(html.Div(id='resource-summary', className="text-white"), className="p-3")
                ], className="bg-secondary text-white w-100")
            ], md=12, className="mb-3"),
        ]),

        # Performance Graphs (Horizontal Layout)
        dbc.Row([
            # CPU Usage
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("CPU Usage", className="text-center text-white")),
                    dbc.CardBody(
                        dcc.Graph(id='cpu-usage-graph', config={'displayModeBar': False}, style={"height": "100%", "width": "100%"}),
                        style={"overflow": "hidden"}
                    ),
                ], className="bg-secondary text-white w-100 h-100")
            ], md=4, xs=12, className="mb-3"),

            # Memory Usage
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Memory Usage", className="text-center text-white")),
                    dbc.CardBody(
                        dcc.Graph(id='memory-usage-graph', config={'displayModeBar': False}, style={"height": "100%", "width": "100%"}),
                        style={"overflow": "hidden"}
                    ),
                ], className="bg-secondary text-white w-100 h-100")
            ], md=4, xs=12, className="mb-3"),

            # Disk Usage
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Disk Usage", className="text-center text-white")),
                    dbc.CardBody(
                        dcc.Graph(id='disk-usage-graph', config={'displayModeBar': False}, style={"height": "100%", "width": "100%"}),
                        style={"overflow": "hidden"}
                    ),
                ], className="bg-secondary text-white w-100 h-100")
            ], md=4, xs=12, className="mb-3"),
        ], className="g-2"),

        # Interval for real-time updates
        dcc.Interval(id='update-interval', interval=5000, n_intervals=0)
    ], fluid=True, className="bg-dark vh-100 text-white")

    @main_dash.callback(
        Output('cpu-usage-graph', 'figure'),
        Output('memory-usage-graph', 'figure'),
        Output('disk-usage-graph', 'figure'),
        Output('resource-summary', 'children'),
        Input('update-interval', 'n_intervals')
    )
    def update_metrics(n_intervals):
        try:
            # Collect system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            # CPU Usage Graph
            cpu_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=cpu_percent,
                title={'text': "CPU Usage (%)"},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#007bff"}}
            ))

            # Memory Usage Graph
            memory_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=memory.percent,
                title={'text': "Memory Usage (%)"},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#28a745"}}
            ))

            # Disk Usage Graph
            disk_fig = go.Figure(go.Indicator(
                mode="gauge+number",
                value=disk.percent,
                title={'text': "Disk Usage (%)"},
                gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#dc3545"}}
            ))

            # Resource Summary
            summary = html.Ul([
                html.Li(f"CPU Usage: {cpu_percent}%", className="mb-2"),
                html.Li(f"Memory Usage: {memory.percent}% ({memory.used // (1024 ** 2)}MB / {memory.total // (1024 ** 2)}MB)", className="mb-2"),
                html.Li(f"Disk Usage: {disk.percent}% ({disk.used // (1024 ** 3)}GB / {disk.total // (1024 ** 3)}GB)", className="mb-2"),
            ])

            return cpu_fig, memory_fig, disk_fig, summary

        except Exception as e:
            print(f"Error during metrics update: {e}")
            return go.Figure(), go.Figure(), go.Figure(), html.Ul([html.Li("Failed to load metrics", className="text-danger")])

    return main_dash

