#!/usr/bin/env python
# coding: utf-8

def generate_equity_curve(full_html:bool=True)-> str:
    import pandas as pd
    import plotly.graph_objects as go
    import re

    from plotly.subplots import make_subplots
    from urllib.parse import quote
    
    SHEET_ID = "1HJ9h7UEtUQCXNA58UkZyPsHogJWBAcB1lNWt9nOPMR4"

    # Specify the tab name (optional, defaults to the first sheet)
    SHEET_NAME = "TradesCopy"
    sql_query = "SELECT * WHERE P=1" # Query to only pull open trades
    encoded_query = quote(sql_query)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}&tq={encoded_query}"
    num_cols = ['Open Price', 'Close Price', 'Commission','Risk ($)', 'Balance at Open', 'PnL']

    # Load into DataFrame read directly from the url
    df = pd.read_csv(url)
    df[num_cols] = df[num_cols].fillna('0')
    for c in num_cols:
        df[c] = df[c].apply(lambda x: float(re.sub(r"\(", "-", re.sub(r"[,\)]", "", str(x))))) # Replace '(' with '-' and remove ')', ',' from the numbers to cast them to float
    df['Close Time'] = pd.to_datetime(df['Close Time'])
    df.sort_values('Close Time', inplace=True)

    cols2keep = ['Account', 'PnL', 'Close Time']
    trades = df[cols2keep].copy()
    trades.head()


    # Specify the tab name (optional, defaults to the first sheet)
    SHEET_NAME = "Accounts"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

    # Load into DataFrame read directly from the url
    df = pd.read_csv(url)
    num_cols = ['Initial Balance', 'PnL', 'Current Balance']
    df[num_cols] = df[num_cols].fillna('0')
    for c in num_cols:
        df[c] = df[c].apply(lambda x: float(re.sub(r"\(", "-", re.sub(r"[,\)]", "", str(x))))) # Replace '(' with '-' and remove ')', ',' from the numbers to cast them to float
        
    # Only show paper trading accounts
    df = df[df['Account Name'].str.contains('Paper Trading')]
    
    accounts = df.copy()
    accounts.head()
    
    # Merge trades with accounts
    df = pd.merge(trades, accounts[['Account Name', 'Initial Balance']], left_on='Account', right_on='Account Name')
    df['Balance'] = df.groupby(['Account Name'])['PnL'].cumsum() + df['Initial Balance']
    df.head()

    # # Generate the plot
    # Setup figure with secondary y-axis
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    accounts = df["Account"].unique()

    # Track trace indices to build visibility toggles correctly
    # Each account has 2 traces: (1) Balance Line, (2) PnL Bars
    traces_per_account = 2

    for i, account in enumerate(accounts):
        acc_df = df[df["Account"] == account].copy()

        # Prep data with starting baseline for line chart
        initial_bal = acc_df["Initial Balance"].iloc[0]
        line_x = list(range(0, len(acc_df) + 1))
        line_y = [initial_bal] + acc_df["Balance"].tolist()

        bar_x = list(range(1, len(acc_df) + 1))
        bar_y = acc_df["PnL"].tolist()

        # Trace 1: Balance Line (Primary Y-Axis)
        fig.add_trace(
            go.Scatter(
                x=line_x,
                y=line_y,
                mode="lines+markers",
                name=f"Acc {account} Balance",
                visible=(i == 0),
                line=dict(color="#49fcfe"),
                hovertemplate="Trade: %{x}<br>Balance: $%{y:,.2f}<extra></extra>"
            ),
            secondary_y=False
        )

        # Trace 2: PnL Bars (Secondary Y-Axis)
        # Color coding green for positive PnL and red for negative PnL
        colors = ['#26a69a' if pnl >= 0 else '#ef5350' for pnl in bar_y]

        fig.add_trace(
            go.Bar(
                x=bar_x,
                y=bar_y,
                name=f"Acc {account} PnL",
                marker_color=colors,
                opacity=0.4,
                visible=(i == 0),
                hovertemplate="Trade:  %{x}<br>P&L:   $%{y:,.2f}<extra></extra>"
            ),
            secondary_y=True
        )

    # Create dropdown buttons
    buttons = []
    total_traces = len(accounts) * traces_per_account

    for i, account in enumerate(accounts):
        # Set visibility for pair of traces belonging to current account
        visibility = [False] * total_traces
        visibility[i * traces_per_account] = True      # Line Trace
        visibility[i * traces_per_account + 1] = True  # Bar Trace

        button = dict(
            label=f"{account}",
            method="update",
            args=[
                {"visible": visibility},
                {"title": f"Equity Curve - {account}"}
            ]
        )
        buttons.append(button)

    # Update layout with custom dark text states for dropdown
    fig.update_layout(
        title=f"Equity Curve - {accounts[0]}",
        xaxis_title="Trade Number",
        template="plotly_dark",
        plot_bgcolor="#212529",
        paper_bgcolor="#212529",
        updatemenus=[
            dict(
                active=0,
                buttons=buttons,
                x=1.15,
                y=1.15,
                xanchor="right",
                yanchor="top",
                showactive=True,
                # --- DROPDOWN HOVER & SELECTED TEXT COLOR FIXES ---
                font=dict(color="#111111"),          # Sets dropdown item & hover text color to dark
                bgcolor="#a7a5a5",                   # Sets dropdown menu background to light gray for high contrast
                bordercolor="#b2adad",               # Border color
                borderwidth=1,
            )
        ],
        barmode="relative"
    )

    # Set Y-Axes titles
    fig.update_yaxes(title_text="Balance ($)", secondary_y=False)
    fig.update_yaxes(title_text="Trade PnL ($)", secondary_y=True, showgrid=False)
    
    return fig.to_html(full_html=full_html)