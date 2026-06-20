"""Technical indicator calculations"""
import numpy as np
import pandas as pd

def sma(arr, n):
    s = pd.Series(arr)
    return s.rolling(n).mean().tolist()

def ema(arr, n):
    s = pd.Series(arr)
    return s.ewm(span=n, adjust=False).mean().tolist()

def calc_boll(cls, n=20, m=2):
    s = pd.Series(cls)
    mid = s.rolling(n).mean()
    std = s.rolling(n).std()
    return {
        'upper': (mid + m * std).tolist(),
        'mid': mid.tolist(),
        'lower': (mid - m * std).tolist()
    }

def calc_macd(cls):
    s = pd.Series(cls)
    e12 = s.ewm(span=12, adjust=False).mean()
    e26 = s.ewm(span=26, adjust=False).mean()
    dif = e12 - e26
    dea = dif.ewm(span=9, adjust=False).mean()
    bar = 2 * (dif - dea)
    return {'dif': dif.tolist(), 'dea': dea.tolist(), 'bar': bar.tolist()}

def calc_rsi(cls, n=14):
    s = pd.Series(cls)
    delta = s.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.ewm(alpha=1/n, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/n, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50).tolist()

def calc_kdj(hi, lo, cls, n=9):
    h, l, c = pd.Series(hi), pd.Series(lo), pd.Series(cls)
    hh = h.rolling(n).max()
    ll = l.rolling(n).min()
    rsv = (c - ll) / (hh - ll).replace(0, np.nan) * 100
    rsv = rsv.fillna(50)
    K, D = [50.0], [50.0]
    for i, r in enumerate(rsv):
        if i == 0:
            continue
        k = (2/3) * K[-1] + (1/3) * r
        d = (2/3) * D[-1] + (1/3) * k
        K.append(k)
        D.append(d)
    J = [3*k - 2*d for k, d in zip(K, D)]
    return {'K': K, 'D': D, 'J': J}

def calc_obv(cls, vol):
    obv = [0]
    for i in range(1, len(cls)):
        if cls[i] > cls[i-1]:
            obv.append(obv[-1] + vol[i])
        elif cls[i] < cls[i-1]:
            obv.append(obv[-1] - vol[i])
        else:
            obv.append(obv[-1])
    return obv

def calc_all(ohlcv):
    cls = [d['c'] for d in ohlcv]
    hi = [d['h'] for d in ohlcv]
    lo = [d['l'] for d in ohlcv]
    vol = [d['v'] for d in ohlcv]
    return {
        'ma5': sma(cls, 5), 'ma10': sma(cls, 10), 'ma20': sma(cls, 20),
        'ma60': sma(cls, 60), 'ma200': sma(cls, 200),
        'boll': calc_boll(cls),
        'macd': calc_macd(cls),
        'rsi': calc_rsi(cls),
        'kdj': calc_kdj(hi, lo, cls),
        'obv': calc_obv(cls, vol)
    }
