"""Market registry"""
from .cn_stock import CNStockMarket
from .us_stock import USStockMarket
from .us_futures import USFuturesMarket
from .cn_futures import CNFuturesMarket

MARKET_REGISTRY = {
    'CN_STOCK': CNStockMarket,
    'US_STOCK': USStockMarket,
    'US_FUT': USFuturesMarket,
    'CN_FUT': CNFuturesMarket,
}


class MarketManager:
    def __init__(self):
        self.markets = {}
    
    async def initialize(self, enabled_keys):
        import asyncio
        tasks = []
        for key in enabled_keys:
            if key in MARKET_REGISTRY:
                m = MARKET_REGISTRY[key]()
                self.markets[key] = m
                tasks.append(m.initialize())
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def get(self, key):
        return self.markets.get(key)
    
    def all(self):
        return self.markets
