import pandas as pd
import torch 
import yfinance as yf 

def get_hist(ticker, period):
    stock = yf.Ticker(ticker)

    hist = stock.history(period=period)
    if not len(hist):
        return None 

    return hist 

def base(ticker, period='max'):
    return get_hist()['Close']

def first(ticker, period='max', delta=1):
    hist = get_hist(ticker, period)
    if hist is None:
        return hist 

    if delta == 1:
        return hist['Close'] - hist['Open'] 

    # Assume delta is in days
    #TODO 

def dummy():
    return torch.tensor([i for i in range(10)]).float().numpy(), (torch.rand((10))*10).numpy()