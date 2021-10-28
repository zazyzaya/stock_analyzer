import numpy as np
import pandas as pd
import yfinance as yf 

def get_hist(ticker, period):
    stock = yf.Ticker(ticker)

    hist = stock.history(period=period)
    if not len(hist):
        return None 

    return hist 

def base(ticker, period='max', smooth=0):
    df = get_hist(ticker, period)['Close']
    return df.index, df.values

def first(ticker, period='max', smooth=4):
    hist = get_hist(ticker, period)
    if hist is None:
        return hist 

    offset = smooth*5
    open, close = hist['Open'].values, hist['Close'].values
    deriv = (close[offset:] - open[:-offset]) / open[:-offset]

    return hist.index[offset:], deriv

def smoothing(x, N):
    if N == 0:
        return x 

    cumsum = np.cumsum(np.insert(x, 0, 0)) 
    return (cumsum[N:] - cumsum[:-N]) / float(N)

def dummy():
    return np.array([i for i in range(10)], dtype=float), np.random.rand((10))*10