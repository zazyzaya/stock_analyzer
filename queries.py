import numpy as np
import pandas as pd
import yfinance as yf 

def get_hist(ticker, period):
    stock = yf.Ticker(ticker)

    hist = stock.history(period=period)
    if not len(hist):
        return None 

    return hist 

def base(ticker, period='1y', smooth=0):
    df = get_hist(ticker, period)['Close']
    return df.index, df.values

def first(ticker, base=None, period='1y', smooth=4):
    hist = get_hist(ticker, period)
    if hist is None:
        return hist 

    offset = max(1, int(smooth*5))
    open, close = hist['Open'].values, hist['Close'].values
    deriv = (close[offset:] - open[:-offset]) / open[:-offset]

    return hist.index[offset:], deriv

def second(ticker, der=None, period='1y', smooth=4):
    if der is None:
        index, der = first(ticker, period=period, smooth=smooth)
    else:
        index, der = der.index, der.values

    # TODO only plot zeros of 2nd der
    offset = max(1, int(smooth*5))
    return index[1:], der[offset:] - der[:-offset]
    

def smoothing(x, N):
    if N == 0:
        return x 

    cumsum = np.cumsum(np.insert(x, 0, 0)) 
    return (cumsum[N:] - cumsum[:-N]) / float(N)

def dummy():
    return np.array([i for i in range(10)], dtype=float), np.random.rand((10))*10