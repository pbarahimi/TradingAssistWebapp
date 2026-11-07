#!/usr/bin/env python
# coding: utf-8
import plotly.graph_objects as go
import pandas as pd
import re
from plotly.subplots import make_subplots
from urllib.parse import quote

def generate_daily_pnl(full_html:bool=True)-> str:
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
    df = df.groupby(['Account', 'Close Date'], as_index=0).agg({'PnL':['count', 'sum']})
    df.columns = ['Account','Date','Trade Count', 'PnL']

    # 2. Initialize the Plotly figure
    fig = go.Figure()

    # Get unique accounts
    unique_accounts = df['Account'].unique()

    # 3. Add a bar trace for each account with conditional coloring
    for i, account in enumerate(unique_accounts):
      df_acc = df[df['Account'] == account]

      # Determine color for each bar: green if >= 0, red if < 0
      bar_colors = ['green' if val >= 0 else '#ea3b3c' for val in df_acc['PnL']]

      fig.add_trace(
          go.Bar(
              x=df_acc['Date'],
              y=df_acc['PnL'],
              name=str(account),
              marker_color=bar_colors,
              opacity=0.7,
              # Make only the first account visible by default
              visible=(i == 0),
          )
      )

    # 4. Create the dropdown buttons
    buttons = []
    for i, account in enumerate(unique_accounts):
      # Create a boolean list where only the selected trace is True, others are False
      visibility_list = [False] * len(unique_accounts)
      visibility_list[i] = True

      buttons.append(
          dict(
              label=str(account),
              method='update',
              args=[
                  {'visible': visibility_list},
                  {'title': f'PnL Bar Chart - {account}'},
              ],
          )
      )

    # 5. Add the dropdown menu to the layout
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
                # --- DROPDOWN HOVER & SELECTED TEXT COLOR FIXES ---
                font=dict(color="#111111"),          # Sets dropdown item & hover text color to dark
                bgcolor="#a7a5a5",                   # Sets dropdown menu background to light gray for high contrast
                bordercolor="#b2adad",               # Border color
                borderwidth=1,
            )
        ],
        xaxis=dict(tickangle=-45),
        title=f'Daily PnL Bar - {unique_accounts[0]}',
        xaxis_title='Date',
        yaxis_title='PnL',
        template='plotly_dark',
        plot_bgcolor="#212529",
        paper_bgcolor="#212529",
        barmode='relative',
    )
    
    return fig.to_html(full_html=full_html)