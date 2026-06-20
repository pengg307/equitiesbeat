"""Signal detection from indicators"""
from .indicators import calc_all

def safe_get(arr, i):
    if i < 0 or i >= len(arr): return None
    v = arr[i]
    if v is None: return None
    try:
        if isinstance(v, float) and (v != v):
            return None
    except: pass
    return v

SIGNAL_KEYS = [
    'ma_golden','ma_death','ma_bull_arr','ma_bear_arr','ma_above','ma_below',
    'boll_upper','boll_lower','boll_abmid','boll_blmid','boll_squeeze','boll_expand',
    'macd_golden','macd_death','macd_red_grow','macd_grn_grow','macd_above_zero','macd_below_zero',
    'rsi_oversold','rsi_overbought','rsi_strong','rsi_weak','rsi_cross50',
    'kdj_golden','kdj_death','kdj_oversold','kdj_overbought','kdj_kabove','kdj_kbelow',
    'obv_up','obv_dn','obv_bull_div','obv_bear_div'
]

def detect_signals(ohlcv):
    if not ohlcv or len(ohlcv) < 30:
        return {k: False for k in SIGNAL_KEYS}
    
    ind = calc_all(ohlcv)
    cls = [d['c'] for d in ohlcv]
    L = len(cls) - 1
    cur = cls[L]
    
    m5 = safe_get(ind['ma5'], L)
    m10 = safe_get(ind['ma10'], L)
    m20 = safe_get(ind['ma20'], L)
    m60 = safe_get(ind['ma60'], L)
    m5p = safe_get(ind['ma5'], L-1)
    m10p = safe_get(ind['ma10'], L-1)
    
    bu = safe_get(ind['boll']['upper'], L)
    bm = safe_get(ind['boll']['mid'], L)
    bl = safe_get(ind['boll']['lower'], L)
    buP = safe_get(ind['boll']['upper'], L-1)
    blP = safe_get(ind['boll']['lower'], L-1)
    bmP = safe_get(ind['boll']['mid'], L-1)
    
    dif = safe_get(ind['macd']['dif'], L)
    dea = safe_get(ind['macd']['dea'], L)
    bar = safe_get(ind['macd']['bar'], L)
    difP = safe_get(ind['macd']['dif'], L-1)
    deaP = safe_get(ind['macd']['dea'], L-1)
    barP = safe_get(ind['macd']['bar'], L-1)
    
    rsiV = safe_get(ind['rsi'], L)
    rsiP = safe_get(ind['rsi'], L-1)
    
    kv = safe_get(ind['kdj']['K'], L)
    dv = safe_get(ind['kdj']['D'], L)
    kvP = safe_get(ind['kdj']['K'], L-1)
    dvP = safe_get(ind['kdj']['D'], L-1)
    
    obv = ind['obv']
    obvL = obv[L]
    obvL5 = obv[max(0, L-5)]
    obvL10 = obv[max(0, L-10)]
    prL10 = cls[max(0, L-10)]
    
    def ok(*vals): return all(v is not None for v in vals)
    
    return {
        'ma_golden': ok(m5,m10,m5p,m10p) and m5p < m10p and m5 > m10,
        'ma_death':  ok(m5,m10,m5p,m10p) and m5p > m10p and m5 < m10,
        'ma_bull_arr': ok(m5,m10,m20,m60) and m5 > m10 > m20 > m60,
        'ma_bear_arr': ok(m5,m10,m20,m60) and m5 < m10 < m20 < m60,
        'ma_above': ok(m5,m10,m20) and cur > m5 and cur > m10 and cur > m20,
        'ma_below': ok(m5,m10,m20) and cur < m5 and cur < m10 and cur < m20,
        'boll_upper': ok(bu,bl) and bu != bl and (cur-bl)/(bu-bl) > 0.92,
        'boll_lower': ok(bu,bl) and bu != bl and (cur-bl)/(bu-bl) < 0.08,
        'boll_abmid': ok(bm) and cur > bm,
        'boll_blmid': ok(bm) and cur < bm,
        'boll_squeeze': ok(bu,bl,bm) and bm != 0 and (bu-bl)/bm < 0.045,
        'boll_expand': ok(bu,bl,bm,buP,blP,bmP) and bmP != 0 and bm != 0 and (buP-blP)/bmP < 0.045 and (bu-bl)/bm >= 0.045,
        'macd_golden': ok(dif,dea,difP,deaP) and difP < deaP and dif > dea,
        'macd_death':  ok(dif,dea,difP,deaP) and difP > deaP and dif < dea,
        'macd_red_grow': ok(bar,barP) and bar > 0 and bar > barP,
        'macd_grn_grow': ok(bar,barP) and bar < 0 and bar < barP,
        'macd_above_zero': ok(dif,dea) and dif > 0 and dea > 0,
        'macd_below_zero': ok(dif,dea) and dif < 0 and dea < 0,
        'rsi_oversold':   rsiV is not None and rsiV < 30,
        'rsi_overbought': rsiV is not None and rsiV > 70,
        'rsi_strong':     rsiV is not None and 50 <= rsiV <= 70,
        'rsi_weak':       rsiV is not None and 30 <= rsiV < 50,
        'rsi_cross50':    ok(rsiV,rsiP) and rsiP < 50 and rsiV >= 50,
        'kdj_golden':     ok(kv,dv,kvP,dvP) and kvP < dvP and kv > dv and kv < 30,
        'kdj_death':      ok(kv,dv,kvP,dvP) and kvP > dvP and kv < dv and kv > 70,
        'kdj_oversold':   ok(kv,dv) and kv < 20 and dv < 20,
        'kdj_overbought': ok(kv,dv) and kv > 80 and dv > 80,
        'kdj_kabove':     ok(kv,dv) and kv > dv,
        'kdj_kbelow':     ok(kv,dv) and kv < dv,
        'obv_up': obvL > obvL5,
        'obv_dn': obvL < obvL5,
        'obv_bull_div': cur < prL10 and obvL > obvL10,
        'obv_bear_div': cur > prL10 and obvL < obvL10,
        '_vals': {
            'm5': m5, 'm10': m10, 'm20': m20, 'm60': m60,
            'bu': bu, 'bm': bm, 'bl': bl,
            'dif': dif, 'dea': dea, 'bar': bar,
            'rsiV': rsiV, 'kv': kv, 'dv': dv
        }
    }
