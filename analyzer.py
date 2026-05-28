import pandas as pd
import numpy as np

def analyze_squeeze_and_rsi(df, window=20, rsi_period=14):
    if df is None or len(df) < max(window, rsi_period):
        return None
        
    analyzed_df = df.copy()
    
    analyzed_df['sma'] = analyzed_df['close'].rolling(window=window).mean()
    analyzed_df['std_dev'] = analyzed_df['close'].rolling(window=window).std()
    analyzed_df['upper_band'] = analyzed_df['sma'] + (analyzed_df['std_dev'] * 2)
    analyzed_df['lower_band'] = analyzed_df['sma'] - (analyzed_df['std_dev'] * 2)
    analyzed_df['bandwidth'] = ((analyzed_df['upper_band'] - analyzed_df['lower_band']) / analyzed_df['sma']) * 100
    
    delta = analyzed_df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=rsi_period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=rsi_period).mean()
    rs = gain / loss
    analyzed_df['rsi'] = 100 - (100 / (1 + rs))
    
    analyzed_df = analyzed_df.dropna().reset_index(drop=True)
    
    return analyzed_df