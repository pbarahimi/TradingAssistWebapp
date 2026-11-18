#!/usr/bin/env python
# coding: utf-8
import plotly.graph_objects as go
import pandas as pd
import re
from plotly.subplots import make_subplots
from urllib.parse import quote

def generate_weekly_pnl(full_html:bool=True)-> str:
    # 1. Pull and prepare data
    SHEET_ID = "1HJ9h7UEtUQCXNA58UkZyPsHogJWBAcB1lNWt9nOPMR4"

    # Specify the tab name (optional, defaults to the first sheet)
    SHEET_NAME = "TradesCopy"
    sql_query = "SELECT C, O, R WHERE P=1" # Query to only pull 'Account', 'Pnl', 'Close Time' columns for open trades
    encoded_query = quote(sql_query)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}&tq={encoded_query}"
    num_cols = ['PnL']
    
    
    # Load into DataFrame read directly from the url
    df = pd.read_csv(url)
    df[num_cols] = df[num_cols].fillna('0')
    for c in num_cols:
        df[c] = df[c].apply(lambda x: float(re.sub(r"\(", "-", re.sub(r"[,\)]", "", str(x))))) # Replace '(' with '-' and remove ')', ',' from the numbers to cast them to float
    
    # Filter on active trades
    active_accounts = ['Tradestation - Futures',
                       'Tradestation - Equity',
                       'Paper Trading #1',
                       'FTP - 151063']
    df = df[df['Account'].isin(active_accounts)].copy()
    df['WK'] = pd.to_datetime(df['Close Date'], format="%m/%d/%y").dt.strftime('%Y W%V')
    df = df.groupby(['Account', 'WK'], as_index=0).agg({'PnL':['count', 'sum']})
    
    df.columns = ['Account','Week','Trade Count', 'PnL']
    df['Balance'] = df.groupby('Account')['PnL'].cumsum()
    df.sort_values(['Account', 'Week'], inplace=True)

    # 2. Initialize the Plotly figure
    fig = go.Figure()

    # Get unique accounts
    unique_accounts = df['Account'].unique()

    # 3. Add traces for each account: Bar for PnL, Line for Balance
    for i, account in enumerate(unique_accounts):
        df_acc = df[df['Account'] == account]

        # Determine color for each bar: green if >= 0, red if < 0
        bar_colors = ['#26a69a' if val >= 0 else '#ef5350' for val in df_acc['PnL']]

        # Add PnL Bar Trace
        fig.add_trace(
            go.Bar(
                x=df_acc['Week'],
                y=df_acc['PnL'],
                name=f"{account} (PnL)",
                marker_color=bar_colors,
                opacity=0.7,
                visible=(i == 0),
            )
        )

        # Add Balance Line Trace (tied to secondary y-axis)
        fig.add_trace(
            go.Scatter(
                x=df_acc['Week'],
                y=df_acc['Balance'],
                name=f"{account} (Balance)",
                mode='lines+markers',
                yaxis='y2',
                line=dict(color='#49fcfe', width=2),  # Contrasting orange line
                visible=(i == 0),
            )
        )

    # 4. Create the dropdown buttons
    buttons = []
    for i, account in enumerate(unique_accounts):
        visibility_list = [False] * (2 * len(unique_accounts))
        visibility_list[2 * i] = True       # Bar trace
        visibility_list[2 * i + 1] = True   # Line trace

        buttons.append(
            dict(
                label=str(account),
                method='update',
                args=[
                    {'visible': visibility_list},
                    {'title': f'PnL & Balance - {account}'},
                ],
            )
        )

    # 5. Add the dropdown menu and secondary y-axis configuration to layout
    fig.update_layout(
        updatemenus=[
            dict(
                active=0,
                buttons=buttons,
                x=1.15,
                y=1.15,
                xanchor="right",
                yanchor="top",
                showactive=True,
                font=dict(color="#111111"),          
                bgcolor="#a7a5a5",                   
                bordercolor="#b2adad",               
                borderwidth=1,
            )
        ],
        xaxis=dict(tickangle=-45),
        title=f'PnL & Balance - {unique_accounts[0]}',
        xaxis_title='Date',
        yaxis_title='PnL',
        yaxis2=dict(
            title='Balance',
            overlaying='y',
            side='right',
            showgrid=False,  # Prevents overlapping grid lines
            rangemode='tozero',  # Forces the Y-axis range to start from 0
        ),
        template='plotly_dark',
        plot_bgcolor="#212529",
        paper_bgcolor="#212529",
        barmode='relative',
    )
    
    return fig.to_html(full_html=full_html)