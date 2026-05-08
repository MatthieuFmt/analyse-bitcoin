import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score

# Supposons que 'df' est ta table avec : Date, Open, High, Low, Close, Volume
# df['Date'] doit être au format datetime et triée

def engineering_variables(df):
    # 1. Rendements (Target : ce qu'on veut prédire)
    df['Target_Return'] = df['Close'].shift(-1) / df['Close'] - 1  # Rendement du lendemain
    
    # 2. Indicateurs de Tendance (Moyennes Mobiles)
    df['SMA_7'] = df['Close'].rolling(window=7).mean()
    df['SMA_30'] = df['Close'].rolling(window=30).mean()
    
    # 3. Volatilité (Log Returns et Range)
    df['Log_Ret'] = np.log(df['Close'] / df['Close'].shift(1))
    df['Daily_Range'] = (df['High'] - df['Low']) / df['Close']
    
    # 4. Momentum (RSI simplifié)
    change = df['Close'].diff()
    gain = (change.where(change > 0, 0)).rolling(window=14).mean()
    loss = (-change.where(change < 0, 0)).rolling(window=14).mean()
    df['RSI'] = 100 - (100 / (1 + gain/loss))
    
    # 5. Volume Shock
    df['Vol_Change'] = df['Volume'].pct_change()
    
    return df.dropna()

df_ready = engineering_variables(df)
