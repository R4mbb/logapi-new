from flask import Blueprint, render_template
import pandas as pd
from db import query_logs
import plotly.express as px

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@dashboard_bp.route('/')
def dashboard():
    query = "SELECT * FROM logs"
    rows = query_logs(query)
    df = pd.DataFrame(rows, columns=["id", "timestamp", "level", "message", "source"])

    if df.empty:
        return render_template('dashboard.html', plot="<h3 class='text-center'>No data available to display</h3>")

    # Parse timestamp using Apache log format
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%d/%b/%Y:%H:%M:%S', errors='coerce')
    df = df.dropna(subset=['timestamp'])
    df['date'] = df['timestamp'].dt.date

    # Log level frequency
    level_freq = df['level'].value_counts()

    # Log level distribution by date
    date_level_freq = df.groupby(['date', 'level']).size().reset_index(name='count')

    # Generate log level frequency bar chart
    fig_level = px.bar(
        x=level_freq.index, y=level_freq.values,
        labels={'x': 'Log Level', 'y': 'Count'},
        title='Log Level Frequency',
        color=level_freq.index,
        template='plotly_white'
    )

    # Generate log level distribution heatmap
    fig_distribution = px.density_heatmap(
        date_level_freq, x='date', y='level', z='count',
        labels={'date': 'Date', 'level': 'Log Level', 'count': 'Count'},
        title='Log Level Distribution by Date',
        template='plotly_white',
        color_continuous_scale='Viridis'
    )

    plot_level = fig_level.to_html(full_html=False)
    plot_distribution = fig_distribution.to_html(full_html=False)

    return render_template(
        'dashboard.html', 
        plot=plot_level + "<br><br>" + plot_distribution
    )

