"""Data provider with caching and retry logic"""
import asyncio
import logging
import time
from cachetools import TTLCache
from concurrent.futures import ThreadPoolExecutor
import yfinance as yf
import numpy as np
from config import Config

log = logging.getLogger(__name__)

# IMPORTANT: Suppress noisy yfinance error logs
# We have our own fallback to simulation, so these errors are not critical
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('peewee').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.WARNING)

_executor = ThreadPoolExecutor(max_workers=5)  # reduced to avoid rate limits
_quote_cache = TTLCache(maxsize=2000, ttl=Config.QUOTE_CACHE_TTL)
_history_cache = TTLCache(maxsize=500, ttl=Config.HISTORY_CACHE_TTL)

# Track failed symbols to skip during refresh
_failed_symbols = set()


class DataProvider:
    
    @staticmethod
    def _try_fetch_quote(symbol, max_retries=2):
        """Sync fetch with retries"""
        for attempt in range(max_retries):
            try:
                t = yf.Ticker(symbol)
                # Try multiple periods to find one that works
                for period in ["5d", "1mo"]:
                    try:
                        hist = t.history(period=period, interval="1d", auto_adjust=False)
                        if hist is None or hist.empty or len(hist) == 0:
                            continue
                        last = hist.iloc[-1]
                        prev = hist.iloc[-2] if len(hist) > 1 else last
                        return {
                            'price': float(last['Close']),
                            'open': float(last['Open']),
                            'high': float(last['High']),
                            'low': float(last['Low']),
                            'volume': int(last['Volume']) if last['Volume'] > 0 else 1000,
                            'prevClose': float(prev['Close']),
                            'change': float(last['Close'] - prev['Close']),
                            'changePct': float((last['Close'] - prev['Close']) / prev['Close'] * 100),
                        }
                    except Exception:
                        continue
                return None
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                continue
        return None
    
    @staticmethod
    def _try_fetch_history(symbol, period="1y", interval="1d", max_retries=2):
        """Sync fetch with retries"""
        for attempt in range(max_retries):
            try:
                t = yf.Ticker(symbol)
                hist = t.history(period=period, interval=interval, auto_adjust=False)
                if hist is None or hist.empty or len(hist) == 0:
                    # Try shorter period as fallback
                    if period == "1y":
                        hist = t.history(period="6mo", interval=interval, auto_adjust=False)
                        if hist is None or hist.empty:
                            return []
                    else:
                        return []
                return [
                    {
                        'o': float(row['Open']),
                        'h': float(row['High']),
                        'l': float(row['Low']),
                        'c': float(row['Close']),
                        'v': int(row['Volume']) if row['Volume'] > 0 else 1000,
                        't': row.name.isoformat()
                    }
                    for _, row in hist.iterrows()
                ]
            except Exception:
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))
                continue
        return []
    
    @staticmethod
    async def fetch_yf_quote(symbol):
        cache_key = "q:" + symbol
        if cache_key in _quote_cache:
            return _quote_cache[cache_key]
        
        # Skip recently-failed symbols
        if symbol in _failed_symbols:
            return None
        
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(_executor, DataProvider._try_fetch_quote, symbol)
            if data:
                _quote_cache[cache_key] = data
                _failed_symbols.discard(symbol)  # remove from failed if it worked
            else:
                _failed_symbols.add(symbol)
            return data
        except Exception:
            _failed_symbols.add(symbol)
            return None
    
    @staticmethod
    async def fetch_yf_history(symbol, period="1y", interval="1d"):
        cache_key = "h:" + symbol + ":" + period + ":" + interval
        if cache_key in _history_cache:
            return _history_cache[cache_key]
        
        if symbol in _failed_symbols:
            return []
        
        loop = asyncio.get_event_loop()
        try:
            data = await loop.run_in_executor(
                _executor, DataProvider._try_fetch_history, symbol, period, interval
            )
            if data:
                _history_cache[cache_key] = data
            return data
        except Exception:
            return []
    
    @staticmethod
    async def fetch_yf_batch_quotes(symbols):
        """Batch fetch with concurrency limit to avoid rate limits"""
        # Process in chunks of 10
        results = {}
        chunk_size = 10
        for i in range(0, len(symbols), chunk_size):
            chunk = symbols[i:i + chunk_size]
            tasks = [DataProvider.fetch_yf_quote(s) for s in chunk]
            chunk_results = await asyncio.gather(*tasks, return_exceptions=True)
            for s, r in zip(chunk, chunk_results):
                if not isinstance(r, Exception) and r is not None:
                    results[s] = r
            # Small delay between chunks
            if i + chunk_size < len(symbols):
                await asyncio.sleep(0.2)
        return results
    
    @staticmethod
    def clear_failed_cache():
        """Reset failed symbols (call periodically to retry)"""
        _failed_symbols.clear()
    
    @staticmethod
    def get_stats():
        return {
            'quote_cache_size': len(_quote_cache),
            'history_cache_size': len(_history_cache),
            'failed_count': len(_failed_symbols),
            'failed_symbols': list(_failed_symbols)[:20],
        }
    
    @staticmethod
    def simulate_ohlcv(base, days=260, volatility=0.025):
        seed = int(abs(base) * 1000) % (2**31)
        rng = np.random.default_rng(seed)
        d = []
        p = base * (0.7 + rng.random() * 0.3)
        for i in range(days, -1, -1):
            chg = (rng.random() - 0.47) * volatility * 2
            o = round(p, 4)
            c = round(p * (1 + chg), 4)
            h = round(max(o, c) * (1 + rng.random() * volatility * 0.4), 4)
            l = round(min(o, c) * (1 - rng.random() * volatility * 0.4), 4)
            d.append({
                'o': o, 'h': h, 'l': l, 'c': c,
                'v': int(rng.integers(10000, 510000))
            })
            p = c
        return d
    
    @staticmethod
    def simulate_quote(base_symbol, vol=0.025):
        ohlcv = DataProvider.simulate_ohlcv(base_symbol['base'], 260, vol)
        last = ohlcv[-1]
        prev = ohlcv[-2]
        price = last['c']
        pc = prev['c']
        return {
            'price': price,
            'open': last['o'],
            'high': last['h'],
            'low': last['l'],
            'volume': last['v'],
            'prevClose': pc,
            'change': round(price - pc, 4),
            'changePct': round((price - pc) / pc * 100, 2),
            'ohlcv': ohlcv,
        }
