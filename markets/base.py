"""Base market class - Progressive loading"""
from abc import ABC, abstractmethod
import logging
import asyncio
from core.data_provider import DataProvider
from core.signals import detect_signals

log = logging.getLogger(__name__)


class BaseMarket(ABC):
    
    KEY = ""
    NAME = ""
    CURRENCY_SYMBOL = "$"
    DECIMALS = 2
    USE_REAL_DATA = False
    LIMIT_UP = 999
    LIMIT_DN = -999
    UNIT = "symbols"
    
    EXCHANGES = []
    SECTORS = []
    QUICK_FILTERS = []
    INDICES = []
    TRADING_HOURS = []
    
    SIMULATION_VOL = 0.025
    
    def __init__(self):
        self.symbols = []
        self._loaded = False
        self._live_upgrade_done = False
        self._live_upgrade_progress = 0
        self._live_upgrade_total = 0
    
    @abstractmethod
    def get_symbol_list(self):
        pass
    
    @abstractmethod
    def get_quick_key_map(self, symbol):
        pass
    
    async def initialize(self):
        """Phase 1: Load ALL symbols — CSV data first, then simulation for rest."""
        if self._loaded:
            return

        templates = self.get_symbol_list()
        log.info("[" + self.KEY + "] Loading " + str(len(templates)) + " symbols...")

        # Determine CSV dir from config if available
        csv_dir = getattr(self, 'CSV_DIR', None)

        for t in templates:
            tpl = dict(t)
            code = tpl.get('code', '')

            # Check if this symbol has CSV data available
            if tpl.get('csvData') and csv_dir:
                from core.csv_loader import CSVLoader
                tf = tpl.get('csvTimeframe', '60min')
                result = CSVLoader.load_ohlcv(csv_dir, code, tf)

                if result and result['ohlcv']:
                    # Build symbol from CSV data
                    latest = dict(result['latest'])
                    latest['prevClose'] = result['prevClose']
                    # Compute change/changePct from latest price and prevClose
                    pc = latest['prevClose']
                    latest['change'] = round(latest['price'] - pc, 4)
                    latest['changePct'] = round((latest['price'] - pc) / pc * 100, 2) if pc else 0
                    symbol = self._build_symbol(
                        tpl, latest, result['ohlcv'], is_sim=False
                    )
                    symbol['csvFile'] = result.get('file', '')
                    symbol['csvCount'] = result.get('count', 0)
                    log.info("[" + self.KEY + "] " + code + ": loaded " +
                             str(result['count']) + " bars from CSV")
                else:
                    # Graceful degradation: fall back to simulation
                    log.warning("[" + self.KEY + "] " + code +
                                ": CSV load failed, falling back to simulation")
                    sim = DataProvider.simulate_quote(tpl, self.SIMULATION_VOL)
                    symbol = self._build_symbol(tpl, sim, sim['ohlcv'], is_sim=True)
            else:
                # Use simulation data
                sim = DataProvider.simulate_quote(tpl, self.SIMULATION_VOL)
                symbol = self._build_symbol(tpl, sim, sim['ohlcv'], is_sim=True)

            self.symbols.append(symbol)

        self._loaded = True
        live_count = sum(1 for s in self.symbols if not s.get('isSimulated'))
        sim_count = len(self.symbols) - live_count
        log.info("[" + self.KEY + "] Ready: " + str(len(self.symbols)) +
                 " symbols (CSV: " + str(live_count) + ", SIM: " + str(sim_count) + ")")
        
        # Phase 2: Start background task to upgrade to LIVE data
        if self.USE_REAL_DATA:
            self._live_upgrade_total = len(self.symbols)
            asyncio.create_task(self._upgrade_to_live_data())
    
    async def _upgrade_to_live_data(self):
        """Phase 2: Progressively replace simulated data with LIVE yfinance data"""
        log.info("[" + self.KEY + "] Phase 2: Upgrading to LIVE data in background...")
        
        upgraded_count = 0
        failed_count = 0
        
        # Process in small chunks to show progress and avoid rate limits
        chunk_size = 5
        for i in range(0, len(self.symbols), chunk_size):
            chunk = self.symbols[i:i + chunk_size]
            
            # Fetch quote + history for each symbol in chunk
            tasks = []
            for s in chunk:
                yfs = s.get('yfSymbol', s['code'])
                tasks.append(self._fetch_and_upgrade(s, yfs))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for r in results:
                if r is True:
                    upgraded_count += 1
                else:
                    failed_count += 1
            
            self._live_upgrade_progress = i + chunk_size
            
            # Log progress every 10 symbols
            if (i + chunk_size) % 10 == 0 or (i + chunk_size) >= len(self.symbols):
                done = min(i + chunk_size, len(self.symbols))
                log.info("[" + self.KEY + "] Live upgrade progress: " + 
                         str(done) + "/" + str(len(self.symbols)) + 
                         " (LIVE: " + str(upgraded_count) + ", failed: " + str(failed_count) + ")")
            
            # Small delay between chunks to avoid rate limits
            await asyncio.sleep(0.3)
        
        self._live_upgrade_done = True
        log.info("[" + self.KEY + "] Phase 2 COMPLETE: " + 
                 str(upgraded_count) + " LIVE, " + str(failed_count) + " SIM fallback")
    
    async def _fetch_and_upgrade(self, symbol_obj, yf_symbol):
        """Fetch one symbol's live data and upgrade it in-place"""
        try:
            quote = await DataProvider.fetch_yf_quote(yf_symbol)
            if not quote:
                return False
            
            hist = await DataProvider.fetch_yf_history(yf_symbol, period="1y")
            if not hist or len(hist) < 30:
                return False
            
            # Upgrade in place - keep same symbol object reference
            sigs = detect_signals(hist)
            last = hist[-1]
            intraday = [d['c'] for d in hist[-60:]]
            amp = ((last['h'] - last['l']) / quote['prevClose'] * 100) if quote.get('prevClose') else 0
            
            symbol_obj.update({
                'price': quote['price'],
                'prevClose': quote['prevClose'],
                'open': quote['open'],
                'high': quote['high'],
                'low': quote['low'],
                'volume': quote['volume'],
                'change': quote['change'],
                'changePct': quote['changePct'],
                'amplitude': round(amp, 2),
                'intraday': intraday,
                'ohlcv': hist,
                'sigs': sigs,
                'isSimulated': False,  # MARK AS LIVE
            })
            return True
        except Exception as e:
            log.debug("Failed to upgrade " + yf_symbol + ": " + str(e))
            return False
    
    def _build_symbol(self, tpl, quote, ohlcv, is_sim):
        sigs = detect_signals(ohlcv)
        last = ohlcv[-1]
        intraday = [d['c'] for d in ohlcv[-60:]]
        amp = ((last['h'] - last['l']) / quote['prevClose'] * 100) if quote.get('prevClose') else 0
        
        result = dict(tpl)
        result.update({
            'price': quote['price'],
            'prevClose': quote['prevClose'],
            'open': quote['open'],
            'high': quote['high'],
            'low': quote['low'],
            'volume': quote['volume'],
            'change': quote['change'],
            'changePct': quote['changePct'],
            'turnover': round(quote['price'] * quote['volume'] / 10000, 2),
            'pe': tpl.get('pe', round(15 + (hash(tpl['code']) % 50), 1)),
            'pb': tpl.get('pb', round(1 + (hash(tpl['code']) % 10) / 2, 2)),
            'marketCap': tpl.get('marketCap', round(quote['price'] * 1000, 2)),
            'amplitude': round(amp, 2),
            'turnoverRate': round(0.5 + (hash(tpl['code']) % 100) / 10, 2),
            'openInterest': tpl.get('oi', 0),
            'intraday': intraday,
            'ohlcv': ohlcv,
            'sigs': sigs,
            'isSimulated': is_sim,
        })
        return result
    
    async def refresh_quotes(self):
        """Refresh quotes for live updates"""
        if not self.USE_REAL_DATA:
            self._simulate_tick()
            return
        
        # If live upgrade is still in progress, just tick simulated symbols
        if not self._live_upgrade_done:
            self._simulate_tick()
            return
        
        # Only refresh symbols that are confirmed LIVE
        live_symbols = [s for s in self.symbols if not s.get('isSimulated')]
        
        if live_symbols:
            symbols_yf = [s.get('yfSymbol', s['code']) for s in live_symbols]
            quotes = await DataProvider.fetch_yf_batch_quotes(symbols_yf)
            
            for s in live_symbols:
                yfs = s.get('yfSymbol', s['code'])
                q = quotes.get(yfs)
                if q:
                    s['price'] = q['price']
                    s['change'] = q['change']
                    s['changePct'] = q['changePct']
                    s['high'] = max(s['high'], q['high'])
                    s['low'] = min(s['low'], q['low'])
                    s['volume'] = q['volume']
                    s['intraday'].append(q['price'])
                    if len(s['intraday']) > 60:
                        s['intraday'].pop(0)
        
        # Tick the SIM symbols with random walk
        sim_symbols = [s for s in self.symbols if s.get('isSimulated')]
        import random
        for s in sim_symbols:
            t = (random.random() - 0.5) * s['price'] * 0.002
            np_ = max(s['price'] + t, 0.0001)
            s['price'] = round(np_, self.DECIMALS)
            s['change'] = round(np_ - s['prevClose'], self.DECIMALS)
            s['changePct'] = round(s['change'] / s['prevClose'] * 100, 2)
            s['high'] = max(s['high'], np_)
            s['low'] = min(s['low'], np_)
            s['intraday'].append(np_)
            if len(s['intraday']) > 60:
                s['intraday'].pop(0)
    
    def _simulate_tick(self):
        import random
        for s in self.symbols:
            t = (random.random() - 0.5) * s['price'] * 0.002
            np_ = max(s['price'] + t, 0.0001)
            s['price'] = round(np_, self.DECIMALS)
            s['change'] = round(np_ - s['prevClose'], self.DECIMALS)
            s['changePct'] = round(s['change'] / s['prevClose'] * 100, 2)
            s['high'] = max(s['high'], np_)
            s['low'] = min(s['low'], np_)
            s['intraday'].append(np_)
            if len(s['intraday']) > 60:
                s['intraday'].pop(0)
    
    def to_metadata(self):
        return {
            'key': self.KEY,
            'name': self.NAME,
            'currencySymbol': self.CURRENCY_SYMBOL,
            'decimals': self.DECIMALS,
            'unit': self.UNIT,
            'limitUp': self.LIMIT_UP,
            'limitDn': self.LIMIT_DN,
            'exchanges': self.EXCHANGES,
            'sectors': self.SECTORS,
            'quickFilters': self.QUICK_FILTERS,
            'indices': self.INDICES,
            'tradingHours': self.TRADING_HOURS,
            'useRealData': self.USE_REAL_DATA,
        }
    
    def get_loading_status(self):
        """Detailed loading status"""
        live = sum(1 for s in self.symbols if not s.get('isSimulated'))
        sim = len(self.symbols) - live
        return {
            'loaded': self._loaded,
            'liveUpgradeDone': self._live_upgrade_done,
            'liveUpgradeProgress': self._live_upgrade_progress,
            'liveUpgradeTotal': self._live_upgrade_total,
            'total': len(self.symbols),
            'live': live,
            'simulated': sim,
            'useRealData': self.USE_REAL_DATA,
        }
    
    def get_symbols_payload(self):
        return [
            {k: v for k, v in s.items() if k != 'ohlcv'}
            for s in self.symbols
        ]
    
    def get_symbol_detail(self, code):
        for s in self.symbols:
            if s['code'] == code:
                return s
        return None
