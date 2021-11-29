import numpy as np
import pandas as pd
import yfinance as yf 

def get_hist(ticker, period):
    stock = yf.Ticker(ticker)

    hist = stock.history(period=period)
    if not len(hist):
        return None 

    return hist

def base(ticker, period):
    df = get_hist(ticker, period)

    if df is None:
        return None 

    return df.index, df['Close'].values, df['Open'].values

def first(idx, close, open, smooth):
    if not type(close) is np.ndarray:
        close = np.array(close)
        open = np.array(open) 
        idx = np.array(idx, dtype='datetime64')

    offset = max(1, int(smooth*5))
    deriv = (close[offset:] - open[:-offset]) / open[:-offset]

    return [idx[offset:], deriv]

def second(idx, deriv, smooth):
    if not type(deriv) is np.ndarray:
        deriv = np.array(deriv)

    offset = max(1, int(smooth*5))

    return [idx[offset:], (deriv[offset:] - deriv[:-offset]) ]

def find_zeros(idx, series, time_cutoff=None, max_arrows=25):
    # Dash likes to convert these to strings when going from 
    # client to server... sigh
    idx = pd.to_datetime(idx).array
    
    if not type(series) is np.ndarray:
        series = np.array(series)

    if time_cutoff:
        print(type(time_cutoff))
        print(idx)

        idx = idx[idx >= time_cutoff]
        series = series[-idx.shape[0]:]

    gt = series>0
    zero_days = np.logical_xor(gt[1:], gt[:-1])
    idx = idx[1:][zero_days]

    # Check any arrows need printing
    if idx.shape[0] == 0:
        return []

    # Normalize between 0 and 1
    magnitudes = series[1:][zero_days] - series[:-1][zero_days]
    magnitudes = magnitudes - magnitudes.min() / (magnitudes.max() - magnitudes.min())
    magnitudes -= 0.5
    magnitudes *= 2

    # Get indices of top 100 magnitudes
    to_display = -min(max_arrows, magnitudes.shape[0])
    max_mags = np.argpartition(
        abs(magnitudes), to_display
    )[to_display:]

    annotations = []
    for i in max_mags:
        mag = magnitudes[i]
        annotations.append(
            dict(
                arrowcolor='green' if mag > 0 else 'red',
                x=idx[i],
                y=mag,
                xref="x", yref="y2",
                text="",
                showarrow=True,
                axref = "x", ayref='y2',
                ax=idx[i],
                ay=0,
                arrowhead = 3,
                arrowwidth=1.5
            )
        )

    return annotations

def get_all(ticker, period='max', smooth=4):
    ret = base(ticker, period)
    if ret is None:
        return None

    idx, o, c = ret 
    d_idx, deriv = first(idx, c, o, smooth)
    dd_idx, dderiv = second(d_idx, deriv, smooth)

    return [
        [idx, c, o],
        [d_idx, deriv],
        [dd_idx, dderiv]
    ]

def smoothing(x, N):
    if N == 0:
        return x 

    cumsum = np.cumsum(np.insert(x, 0, 0)) 
    return (cumsum[N:] - cumsum[:-N]) / float(N)

def dummy():
    return np.array([i for i in range(10)], dtype=float), np.random.rand((10))*10

if __name__ == '__main__':
    get_all('qqq')