import pandas as pd
import numpy as np
import re
from urllib.parse import quote

def rules_met(account='FTP - 151063'):
    TRADES_SHEET_ID = "1HJ9h7UEtUQCXNA58UkZyPsHogJWBAcB1lNWt9nOPMR4"
    RISK_MGMT_SHEET_ID = '1VLHmzyJuQqAh6W-Zngkyg2sbbUahHV0spNkifSNtGHE'
    DAILY_LOSS_COUNT_LIMIT = 3

    # Specify the tab name (optional, defaults to the first sheet)
    TRADES_SHEET_NAME = 'TradesCopy'

    # Get trades
    sql_query = f'SELECT A, I, O, Q, R WHERE C="{account}"'
    encoded_query = quote(sql_query)
    url = f"https://docs.google.com/spreadsheets/d/{TRADES_SHEET_ID}/gviz/tq?tqx=out:csv&sheet={TRADES_SHEET_NAME}&tq={encoded_query}"
    num_cols = ['PnL', 'Balance at Open']


    # Load into DataFrame read directly from the url
    df = pd.read_csv(url)
    df[num_cols] = df[num_cols].fillna('0')
    for c in num_cols:
        df[c] = df[c].apply(lambda x: float(re.sub(r"\(", "-", re.sub(r"[,\)]", "", str(x))))) # Replace '(' with '-' and remove ')', ',' from the numbers to cast them to float
    df['Open Time'] = pd.to_datetime(df['Open Time'])
    df['Close Time'] = pd.to_datetime(df['Close Time'])
    df['Close Date'] = pd.to_datetime(df['Close Date'], format="%m/%d/%y")

    # Add win/lose indicator
    df['Win'] = np.where(df.PnL>=0, 1, 0)
    df['Loss'] = 1 - df['Win']

    df.sort_values(by='Open Time', inplace=True)
    df['Loss Amount'] = df['Loss']*df['PnL']
    df['Cumulative Loss'] = df.groupby('Close Date')['Loss'].cumsum()
    df['Cumulative PnL'] = df.groupby('Close Date')['PnL'].cumsum()
    df['Trade Count'] = df.groupby('Close Date')['Close Time'].rank( method='first')
 
    df['Breached Loss Count Rule'] = np.where((df['Trade Count']>DAILY_LOSS_COUNT_LIMIT) & (df['Cumulative Loss']>=DAILY_LOSS_COUNT_LIMIT), 1, 0)
    df.sort_values(by='Open Time', inplace=True)

    trades = df.copy()
    
    # Get risk management req
    sql_query = "SELECT E, H"
    encoded_query = quote(sql_query)
    url = f"https://docs.google.com/spreadsheets/d/{RISK_MGMT_SHEET_ID}/gviz/tq?tqx=out:csv&tq={encoded_query}"
    df = pd.read_csv(url)

    # Cast numerical columns
    num_cols = ['Risk per Trade ($)',
                'Total Profit Req to Move to the Next Level']

    for c in num_cols:
        df[c] = df[c].apply(lambda x: float(re.sub(r"\$", "", re.sub(r"\(", "-", re.sub(r"[,\)]", "", str(x)))))) # Replace '(' with '-' and remove ')', ',', '$' from the numbers to cast them to float


    # Add range column for each risk level
    df['range'] = df['Total Profit Req to Move to the Next Level'].shift(1)
    df['range'] = df['range'].fillna(0)
    # Create the Interval column
    df['range'] = pd.IntervalIndex.from_arrays(
        df['range']+100000, 
        df['Total Profit Req to Move to the Next Level']+100000, 
        closed='left'
    )    

    df.drop(columns=['Total Profit Req to Move to the Next Level'], inplace=True)

    risk_req = df.copy()
    
    
    # Group by Close Date to get daily info
    trades.sort_values(by='Open Time', inplace=True)
    trades_daily = trades.groupby('Close Date').agg({'PnL': ['count', 'sum'],
                                                     'Win': 'sum',
                                                     'Loss': 'sum',
                                                     'Loss Amount': 'sum',
                                                     'Balance at Open': ['first'],
                                                     'Breached Loss Count Rule': max,
                                                    })
    trades_daily.columns = ['Trade Count',
                            'PnL',
                            'Win Count',
                            'Loss Count',
                            'Loss Amount',
                            'Beginning Balance',
                            'Loss Count Rule Breached'
                           ]
    trades_daily['Ending Balance'] = trades_daily['Beginning Balance']+trades_daily['PnL']
    trades_daily.reset_index(inplace=True)

    # Add a row for today if not already exists
    today = pd.Timestamp.today().normalize()
    if not (trades_daily['Close Date'] == today).any():
        print('Todays date not exist')
        new_row = {
            'Close Date': today,
            'Trade Count': 0,
            'PnL': 0.0,
            'Win Count': 0,
            'Loss Count': 0,
            'Loss Amount': 0.0,
            'Beginning Balance': trades_daily['Ending Balance'].iloc[-1],
            'Loss Count Rule Breached': 0,
            'Ending Balance': trades_daily['Ending Balance'].iloc[-1],
            'Daily Loss Limit Breached': 0,
            'Excess Loss Limit': 0.0,
        }

        # Add the row to the end of the DataFrame
        trades_daily.loc[len(trades_daily)] = new_row
        
        
    # Create an IntervalIndex from the interval column
    interval_idx = pd.IntervalIndex(risk_req['range'])

    # Find the position of the matching interval for each number (-1 if no match)
    trades_daily['interval_idx'] = interval_idx.get_indexer(trades_daily['Beginning Balance'])

    # Filter out non-matches and merge based on the matched positions
    trades_daily = (
        trades_daily
        .merge(risk_req[['Risk per Trade ($)', 'range']].reset_index(), left_on='interval_idx', right_on='index')
        .drop(columns=['index', 'interval_idx'])
    )
    
    trades_daily['Daily Loss Limit Breached'] = np.where(trades_daily['Loss Amount']<= -1*DAILY_LOSS_COUNT_LIMIT*trades_daily['Risk per Trade ($)'], 1, 0)
    trades_daily['Excess Loss Limit'] = np.where(trades_daily['Daily Loss Limit Breached'], DAILY_LOSS_COUNT_LIMIT*trades_daily['Risk per Trade ($)']+trades_daily['Loss Amount'], 0)
    
    out = trades_daily.iloc[:, [0,1,4,5,2,9, 7,11,12]].sort_values('Close Date', ascending=False).head(30)
    return(out.to_html(border=0, justify='left',  table_id='rulesDataTable', classes='table table-striped table-hover', index=False))
