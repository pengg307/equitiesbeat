"""US Futures - Real data via yfinance
NOTE: Some futures (especially Treasuries) have unreliable yfinance data.
For Treasury exposure, we use bond ETFs (TLT, IEF, SHY, IEI) instead of futures.
"""
from .base import BaseMarket


class USFuturesMarket(BaseMarket):
    KEY = 'US_FUT'
    NAME = 'US Futures'
    CURRENCY_SYMBOL = '$'
    DECIMALS = 4
    USE_REAL_DATA = True
    LIMIT_UP = 999
    LIMIT_DN = -999
    UNIT = 'contracts'
    SIMULATION_VOL = 0.018
    
    EXCHANGES = [['', 'All Exchanges'], ['CME', 'CME'], ['CBOT', 'CBOT'], ['NYMEX', 'NYMEX'], ['COMEX', 'COMEX'], ['ICE', 'ICE'], ['NYSE', 'NYSE (ETF)']]
    SECTORS = ['Index','Energy','Metals','Grains','Softs','Livestock','Currency','Rates']
    QUICK_FILTERS = [
        ['all', 'All'],
        ['index', 'Indices'],
        ['energy', 'Energy'],
        ['metals', 'Metals'],
        ['ags', 'Agriculture'],
        ['fx', 'FX'],
        ['rates', 'Rates (ETF)']
    ]
    INDICES = [
        {'name': 'ES Front', 'code': 'ES=F', 'base': 5280},
        {'name': 'NQ Front', 'code': 'NQ=F', 'base': 18450},
        {'name': 'YM Front', 'code': 'YM=F', 'base': 39850},
        {'name': 'CL Oil', 'code': 'CL=F', 'base': 78.45},
        {'name': 'GC Gold', 'code': 'GC=F', 'base': 2385},
        {'name': 'DXY', 'code': 'DX-Y.NYB', 'base': 104.85},
    ]
    TRADING_HOURS = [[0, 0, 23, 59]]
    
    BASE_SYMBOLS = [
        # Equity Index Futures (reliable)
        {'code':'ES','yfSymbol':'ES=F','name':'E-mini S&P 500','sector':'Index','exchange':'CME','base':5280.5,'month':'Front','oi':2350000,'group':'index'},
        {'code':'NQ','yfSymbol':'NQ=F','name':'E-mini Nasdaq 100','sector':'Index','exchange':'CME','base':18450,'month':'Front','oi':285000,'group':'index'},
        {'code':'YM','yfSymbol':'YM=F','name':'E-mini Dow','sector':'Index','exchange':'CBOT','base':39850,'month':'Front','oi':95000,'group':'index'},
        {'code':'RTY','yfSymbol':'RTY=F','name':'E-mini Russell 2000','sector':'Index','exchange':'CME','base':2125.5,'month':'Front','oi':485000,'group':'index'},
        # Volatility ETF (proxy for VIX futures)
        {'code':'VIX-ETF','yfSymbol':'VXX','name':'iPath VIX ETN','sector':'Index','exchange':'NYSE','base':52.5,'month':'ETF','oi':125000,'group':'index'},
        
        # Energy Futures (mostly reliable)
        {'code':'CL','yfSymbol':'CL=F','name':'Crude Oil WTI','sector':'Energy','exchange':'NYMEX','base':78.45,'month':'Front','oi':1850000,'group':'energy'},
        {'code':'BZ','yfSymbol':'BZ=F','name':'Brent Crude','sector':'Energy','exchange':'ICE','base':82.5,'month':'Front','oi':985000,'group':'energy'},
        {'code':'NG','yfSymbol':'NG=F','name':'Natural Gas','sector':'Energy','exchange':'NYMEX','base':2.85,'month':'Front','oi':1250000,'group':'energy'},
        {'code':'RB','yfSymbol':'RB=F','name':'RBOB Gasoline','sector':'Energy','exchange':'NYMEX','base':2.42,'month':'Front','oi':285000,'group':'energy'},
        {'code':'HO','yfSymbol':'HO=F','name':'Heating Oil','sector':'Energy','exchange':'NYMEX','base':2.58,'month':'Front','oi':185000,'group':'energy'},
        # Energy ETFs as backup
        {'code':'USO','yfSymbol':'USO','name':'US Oil Fund ETF','sector':'Energy','exchange':'NYSE','base':78.5,'month':'ETF','oi':95000,'group':'energy'},
        {'code':'UNG','yfSymbol':'UNG','name':'Natural Gas ETF','sector':'Energy','exchange':'NYSE','base':14.5,'month':'ETF','oi':45000,'group':'energy'},
        
        # Metals Futures
        {'code':'GC','yfSymbol':'GC=F','name':'Gold','sector':'Metals','exchange':'COMEX','base':2385.5,'month':'Front','oi':485000,'group':'metals'},
        {'code':'SI','yfSymbol':'SI=F','name':'Silver','sector':'Metals','exchange':'COMEX','base':28.75,'month':'Front','oi':185000,'group':'metals'},
        {'code':'HG','yfSymbol':'HG=F','name':'Copper','sector':'Metals','exchange':'COMEX','base':4.485,'month':'Front','oi':285000,'group':'metals'},
        {'code':'PL','yfSymbol':'PL=F','name':'Platinum','sector':'Metals','exchange':'NYMEX','base':985.5,'month':'Front','oi':85000,'group':'metals'},
        {'code':'PA','yfSymbol':'PA=F','name':'Palladium','sector':'Metals','exchange':'NYMEX','base':1025.5,'month':'Front','oi':25000,'group':'metals'},
        # Metals ETFs
        {'code':'GLD','yfSymbol':'GLD','name':'SPDR Gold ETF','sector':'Metals','exchange':'NYSE','base':218.5,'month':'ETF','oi':285000,'group':'metals'},
        {'code':'SLV','yfSymbol':'SLV','name':'iShares Silver ETF','sector':'Metals','exchange':'NYSE','base':26.8,'month':'ETF','oi':185000,'group':'metals'},
        
        # Agriculture Futures
        {'code':'ZC','yfSymbol':'ZC=F','name':'Corn','sector':'Grains','exchange':'CBOT','base':425.5,'month':'Front','oi':1850000,'group':'ags'},
        {'code':'ZS','yfSymbol':'ZS=F','name':'Soybeans','sector':'Grains','exchange':'CBOT','base':1185.5,'month':'Front','oi':785000,'group':'ags'},
        {'code':'ZW','yfSymbol':'ZW=F','name':'Wheat','sector':'Grains','exchange':'CBOT','base':625.5,'month':'Front','oi':485000,'group':'ags'},
        {'code':'ZM','yfSymbol':'ZM=F','name':'Soybean Meal','sector':'Grains','exchange':'CBOT','base':385.5,'month':'Front','oi':285000,'group':'ags'},
        {'code':'ZL','yfSymbol':'ZL=F','name':'Soybean Oil','sector':'Grains','exchange':'CBOT','base':48.5,'month':'Front','oi':385000,'group':'ags'},
        {'code':'KC','yfSymbol':'KC=F','name':'Coffee','sector':'Softs','exchange':'ICE','base':235.5,'month':'Front','oi':285000,'group':'ags'},
        {'code':'SB','yfSymbol':'SB=F','name':'Sugar','sector':'Softs','exchange':'ICE','base':22.5,'month':'Front','oi':885000,'group':'ags'},
        {'code':'CC','yfSymbol':'CC=F','name':'Cocoa','sector':'Softs','exchange':'ICE','base':9850,'month':'Front','oi':285000,'group':'ags'},
        {'code':'CT','yfSymbol':'CT=F','name':'Cotton','sector':'Softs','exchange':'ICE','base':78.5,'month':'Front','oi':185000,'group':'ags'},
        {'code':'OJ','yfSymbol':'OJ=F','name':'Orange Juice','sector':'Softs','exchange':'ICE','base':385.5,'month':'Front','oi':25000,'group':'ags'},
        {'code':'LE','yfSymbol':'LE=F','name':'Live Cattle','sector':'Livestock','exchange':'CME','base':185.5,'month':'Front','oi':285000,'group':'ags'},
        {'code':'HE','yfSymbol':'HE=F','name':'Lean Hogs','sector':'Livestock','exchange':'CME','base':95.5,'month':'Front','oi':185000,'group':'ags'},
        {'code':'GF','yfSymbol':'GF=F','name':'Feeder Cattle','sector':'Livestock','exchange':'CME','base':258.5,'month':'Front','oi':45000,'group':'ags'},
        # Agriculture ETF
        {'code':'DBA','yfSymbol':'DBA','name':'Agriculture ETF','sector':'Grains','exchange':'NYSE','base':22.5,'month':'ETF','oi':35000,'group':'ags'},
        
        # FX Futures (use ETFs/spot for FX too since some =F futures are unreliable)
        {'code':'6E','yfSymbol':'6E=F','name':'Euro FX','sector':'Currency','exchange':'CME','base':1.0850,'month':'Front','oi':685000,'group':'fx'},
        {'code':'6J','yfSymbol':'6J=F','name':'Japanese Yen','sector':'Currency','exchange':'CME','base':0.006782,'month':'Front','oi':285000,'group':'fx'},
        {'code':'6B','yfSymbol':'6B=F','name':'British Pound','sector':'Currency','exchange':'CME','base':1.2685,'month':'Front','oi':185000,'group':'fx'},
        {'code':'6A','yfSymbol':'6A=F','name':'Australian Dollar','sector':'Currency','exchange':'CME','base':0.6585,'month':'Front','oi':145000,'group':'fx'},
        {'code':'6C','yfSymbol':'6C=F','name':'Canadian Dollar','sector':'Currency','exchange':'CME','base':0.7385,'month':'Front','oi':125000,'group':'fx'},
        # FX via spot - very reliable
        {'code':'EURUSD','yfSymbol':'EURUSD=X','name':'EUR/USD Spot','sector':'Currency','exchange':'NYSE','base':1.085,'month':'Spot','oi':0,'group':'fx'},
        {'code':'GBPUSD','yfSymbol':'GBPUSD=X','name':'GBP/USD Spot','sector':'Currency','exchange':'NYSE','base':1.268,'month':'Spot','oi':0,'group':'fx'},
        {'code':'USDJPY','yfSymbol':'USDJPY=X','name':'USD/JPY Spot','sector':'Currency','exchange':'NYSE','base':148.5,'month':'Spot','oi':0,'group':'fx'},
        {'code':'AUDUSD','yfSymbol':'AUDUSD=X','name':'AUD/USD Spot','sector':'Currency','exchange':'NYSE','base':0.658,'month':'Spot','oi':0,'group':'fx'},
        {'code':'USDCAD','yfSymbol':'USDCAD=X','name':'USD/CAD Spot','sector':'Currency','exchange':'NYSE','base':1.355,'month':'Spot','oi':0,'group':'fx'},
        {'code':'DXY','yfSymbol':'DX-Y.NYB','name':'US Dollar Index','sector':'Currency','exchange':'ICE','base':104.85,'month':'Spot','oi':48000,'group':'fx'},
        
        # Rates - Use BOND ETFs instead of unreliable ZB/ZN/ZF/ZT futures
        # These ETFs always have data on yfinance
        {'code':'TLT','yfSymbol':'TLT','name':'20+ Year Treasury ETF','sector':'Rates','exchange':'NYSE','base':92.5,'month':'ETF','oi':1250000,'group':'rates'},
        {'code':'IEF','yfSymbol':'IEF','name':'7-10 Year Treasury ETF','sector':'Rates','exchange':'NYSE','base':94.2,'month':'ETF','oi':4850000,'group':'rates'},
        {'code':'IEI','yfSymbol':'IEI','name':'3-7 Year Treasury ETF','sector':'Rates','exchange':'NYSE','base':118.5,'month':'ETF','oi':2850000,'group':'rates'},
        {'code':'SHY','yfSymbol':'SHY','name':'1-3 Year Treasury ETF','sector':'Rates','exchange':'NYSE','base':82.1,'month':'ETF','oi':5850000,'group':'rates'},
        {'code':'BIL','yfSymbol':'BIL','name':'1-3 Month T-Bill ETF','sector':'Rates','exchange':'NYSE','base':91.6,'month':'ETF','oi':4250000,'group':'rates'},
        {'code':'TIP','yfSymbol':'TIP','name':'TIPS ETF (Inflation)','sector':'Rates','exchange':'NYSE','base':108.5,'month':'ETF','oi':985000,'group':'rates'},
        {'code':'LQD','yfSymbol':'LQD','name':'Investment Grade Corp ETF','sector':'Rates','exchange':'NYSE','base':108.5,'month':'ETF','oi':685000,'group':'rates'},
        {'code':'HYG','yfSymbol':'HYG','name':'High Yield Corp ETF','sector':'Rates','exchange':'NYSE','base':77.5,'month':'ETF','oi':985000,'group':'rates'},
    ]
    
    def get_symbol_list(self):
        return [dict(s) for s in self.BASE_SYMBOLS]
    
    def get_quick_key_map(self, s):
        g = s.get('group', '')
        return {
            'index': g == 'index',
            'energy': g == 'energy',
            'metals': g == 'metals',
            'ags': g == 'ags',
            'fx': g == 'fx',
            'rates': g == 'rates',
        }
