import plotly.graph_objects as go
import pandas as pd

def generate_pnl_chart():
    df = pd.DataFrame({
        "Account": ["Paper Trading #1", "Paper Trading #2", "Tradestation - Equity"],
        "PnL": [336.06, 662, -163.08]
    })

    fig = go.Figure(
        go.Bar(
            x=df["Account"],
            y=df["PnL"],
            marker_color=["#4CAF50", "#2196F3", "#F44336"]
        )
    )

    fig.update_layout(
        title="PnL by Account",
        template="plotly_dark",
        height=400
    )

    return fig.to_html(full_html=False, include_plotlyjs="cdn")
