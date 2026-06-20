"""US Stocks - Real data via yfinance"""
from .base import BaseMarket


class USStockMarket(BaseMarket):
    KEY = 'US_STOCK'
    NAME = 'US Stock'
    CURRENCY_SYMBOL = '$'
    DECIMALS = 2
    USE_REAL_DATA = True
    LIMIT_UP = 999
    LIMIT_DN = -999
    UNIT = 'symbols'
    SIMULATION_VOL = 0.022
    
    EXCHANGES = [['', 'All Exchanges'], ['NYSE', 'NYSE'], ['NASDAQ', 'NASDAQ']]
    SECTORS = ['Technology','Healthcare','Financial','Consumer','Energy','Industrial','Materials','Utilities','RealEstate','Communication']
    QUICK_FILTERS = [
        ['all', 'All'],
        ['sp500', 'S&P 500'],
        ['dow', 'Dow 30'],
        ['nasdaq100', 'NASDAQ 100']
    ]
    INDICES = [
        {'name': 'S&P 500', 'code': '^GSPC', 'base': 5280},
        {'name': 'NASDAQ', 'code': '^IXIC', 'base': 16850},
        {'name': 'Dow Jones', 'code': '^DJI', 'base': 39450},
        {'name': 'Russell 2000', 'code': '^RUT', 'base': 2095},
        {'name': 'VIX', 'code': '^VIX', 'base': 14.5},
        {'name': 'NASDAQ 100', 'code': '^NDX', 'base': 18420},
    ]
    TRADING_HOURS = [[9, 30, 16, 0]]
    
    BASE_SYMBOLS = [
        {'code':'AAPL','yfSymbol':'AAPL','name':'Apple Inc','sector':'Technology','exchange':'NASDAQ','base':175.4,'sp500':True,'dow':True,'nasdaq100':True},
        {'code':'MSFT','yfSymbol':'MSFT','name':'Microsoft','sector':'Technology','exchange':'NASDAQ','base':412.3,'sp500':True,'dow':True,'nasdaq100':True},
        {'code':'GOOGL','yfSymbol':'GOOGL','name':'Alphabet A','sector':'Communication','exchange':'NASDAQ','base':142.6,'sp500':True,'nasdaq100':True},
        {'code':'GOOG','yfSymbol':'GOOG','name':'Alphabet C','sector':'Communication','exchange':'NASDAQ','base':144.2,'sp500':True,'nasdaq100':True},
        {'code':'AMZN','yfSymbol':'AMZN','name':'Amazon','sector':'Consumer','exchange':'NASDAQ','base':178.2,'sp500':True,'nasdaq100':True},
        {'code':'NVDA','yfSymbol':'NVDA','name':'NVIDIA','sector':'Technology','exchange':'NASDAQ','base':875.5,'sp500':True,'nasdaq100':True},
        {'code':'META','yfSymbol':'META','name':'Meta Platforms','sector':'Communication','exchange':'NASDAQ','base':485.2,'sp500':True,'nasdaq100':True},
        {'code':'TSLA','yfSymbol':'TSLA','name':'Tesla','sector':'Consumer','exchange':'NASDAQ','base':248.5,'sp500':True,'nasdaq100':True},
        {'code':'BRK-B','yfSymbol':'BRK-B','name':'Berkshire B','sector':'Financial','exchange':'NYSE','base':412.8,'sp500':True},
        {'code':'JPM','yfSymbol':'JPM','name':'JPMorgan Chase','sector':'Financial','exchange':'NYSE','base':198.4,'sp500':True,'dow':True},
        {'code':'V','yfSymbol':'V','name':'Visa','sector':'Financial','exchange':'NYSE','base':278.6,'sp500':True,'dow':True},
        {'code':'JNJ','yfSymbol':'JNJ','name':'Johnson Johnson','sector':'Healthcare','exchange':'NYSE','base':152.3,'sp500':True,'dow':True},
        {'code':'WMT','yfSymbol':'WMT','name':'Walmart','sector':'Consumer','exchange':'NYSE','base':62.4,'sp500':True,'dow':True},
        {'code':'PG','yfSymbol':'PG','name':'Procter Gamble','sector':'Consumer','exchange':'NYSE','base':165.8,'sp500':True,'dow':True},
        {'code':'XOM','yfSymbol':'XOM','name':'Exxon Mobil','sector':'Energy','exchange':'NYSE','base':115.2,'sp500':True},
        {'code':'CVX','yfSymbol':'CVX','name':'Chevron','sector':'Energy','exchange':'NYSE','base':158.6,'sp500':True,'dow':True},
        {'code':'MA','yfSymbol':'MA','name':'Mastercard','sector':'Financial','exchange':'NYSE','base':458.3,'sp500':True},
        {'code':'HD','yfSymbol':'HD','name':'Home Depot','sector':'Consumer','exchange':'NYSE','base':362.4,'sp500':True,'dow':True},
        {'code':'BAC','yfSymbol':'BAC','name':'Bank of America','sector':'Financial','exchange':'NYSE','base':38.2,'sp500':True},
        {'code':'KO','yfSymbol':'KO','name':'Coca-Cola','sector':'Consumer','exchange':'NYSE','base':63.1,'sp500':True,'dow':True},
        {'code':'PFE','yfSymbol':'PFE','name':'Pfizer','sector':'Healthcare','exchange':'NYSE','base':28.5,'sp500':True},
        {'code':'NFLX','yfSymbol':'NFLX','name':'Netflix','sector':'Communication','exchange':'NASDAQ','base':625.8,'sp500':True,'nasdaq100':True},
        {'code':'AMD','yfSymbol':'AMD','name':'AMD','sector':'Technology','exchange':'NASDAQ','base':158.2,'sp500':True,'nasdaq100':True},
        {'code':'INTC','yfSymbol':'INTC','name':'Intel','sector':'Technology','exchange':'NASDAQ','base':32.4,'sp500':True,'nasdaq100':True},
        {'code':'DIS','yfSymbol':'DIS','name':'Walt Disney','sector':'Communication','exchange':'NYSE','base':98.6,'sp500':True,'dow':True},
        {'code':'BA','yfSymbol':'BA','name':'Boeing','sector':'Industrial','exchange':'NYSE','base':182.4,'sp500':True,'dow':True},
        {'code':'GS','yfSymbol':'GS','name':'Goldman Sachs','sector':'Financial','exchange':'NYSE','base':425.5,'sp500':True,'dow':True},
        {'code':'CAT','yfSymbol':'CAT','name':'Caterpillar','sector':'Industrial','exchange':'NYSE','base':345.2,'sp500':True,'dow':True},
        {'code':'CRM','yfSymbol':'CRM','name':'Salesforce','sector':'Technology','exchange':'NYSE','base':285.6,'sp500':True,'dow':True},
        {'code':'IBM','yfSymbol':'IBM','name':'IBM','sector':'Technology','exchange':'NYSE','base':195.4,'sp500':True,'dow':True},
        {'code':'MCD','yfSymbol':'MCD','name':'McDonalds','sector':'Consumer','exchange':'NYSE','base':278.5,'sp500':True,'dow':True},
        {'code':'NKE','yfSymbol':'NKE','name':'Nike','sector':'Consumer','exchange':'NYSE','base':92.6,'sp500':True,'dow':True},
        {'code':'AXP','yfSymbol':'AXP','name':'American Express','sector':'Financial','exchange':'NYSE','base':242.5,'sp500':True,'dow':True},
        {'code':'HON','yfSymbol':'HON','name':'Honeywell','sector':'Industrial','exchange':'NASDAQ','base':205.3,'sp500':True,'dow':True,'nasdaq100':True},
        {'code':'AVGO','yfSymbol':'AVGO','name':'Broadcom','sector':'Technology','exchange':'NASDAQ','base':1325.5,'sp500':True,'nasdaq100':True},
        {'code':'COST','yfSymbol':'COST','name':'Costco','sector':'Consumer','exchange':'NASDAQ','base':785.2,'sp500':True,'nasdaq100':True},
        {'code':'ADBE','yfSymbol':'ADBE','name':'Adobe','sector':'Technology','exchange':'NASDAQ','base':485.6,'sp500':True,'nasdaq100':True},
        {'code':'PEP','yfSymbol':'PEP','name':'PepsiCo','sector':'Consumer','exchange':'NASDAQ','base':172.4,'sp500':True,'nasdaq100':True},
        {'code':'CSCO','yfSymbol':'CSCO','name':'Cisco','sector':'Technology','exchange':'NASDAQ','base':48.5,'sp500':True,'nasdaq100':True},
        {'code':'TMO','yfSymbol':'TMO','name':'Thermo Fisher','sector':'Healthcare','exchange':'NYSE','base':562.3,'sp500':True},
        {'code':'ABT','yfSymbol':'ABT','name':'Abbott Labs','sector':'Healthcare','exchange':'NYSE','base':108.2,'sp500':True},
        {'code':'UNH','yfSymbol':'UNH','name':'UnitedHealth','sector':'Healthcare','exchange':'NYSE','base':485.6,'sp500':True,'dow':True},
        {'code':'LLY','yfSymbol':'LLY','name':'Eli Lilly','sector':'Healthcare','exchange':'NYSE','base':785.4,'sp500':True},
        {'code':'MRK','yfSymbol':'MRK','name':'Merck','sector':'Healthcare','exchange':'NYSE','base':125.6,'sp500':True,'dow':True},
        {'code':'F','yfSymbol':'F','name':'Ford Motor','sector':'Consumer','exchange':'NYSE','base':11.5,'sp500':True},
        {'code':'GM','yfSymbol':'GM','name':'General Motors','sector':'Consumer','exchange':'NYSE','base':42.8,'sp500':True},
        {'code':'T','yfSymbol':'T','name':'AT&T','sector':'Communication','exchange':'NYSE','base':18.5,'sp500':True},
        {'code':'VZ','yfSymbol':'VZ','name':'Verizon','sector':'Communication','exchange':'NYSE','base':41.2,'sp500':True,'dow':True},
        {'code':'WFC','yfSymbol':'WFC','name':'Wells Fargo','sector':'Financial','exchange':'NYSE','base':58.5,'sp500':True},
        {'code':'C','yfSymbol':'C','name':'Citigroup','sector':'Financial','exchange':'NYSE','base':62.4,'sp500':True},
        {'code':'PYPL','yfSymbol':'PYPL','name':'PayPal','sector':'Financial','exchange':'NASDAQ','base':68.5,'sp500':True,'nasdaq100':True},
        {'code':'SBUX','yfSymbol':'SBUX','name':'Starbucks','sector':'Consumer','exchange':'NASDAQ','base':92.3,'sp500':True,'nasdaq100':True},
        {'code':'QCOM','yfSymbol':'QCOM','name':'Qualcomm','sector':'Technology','exchange':'NASDAQ','base':168.2,'sp500':True,'nasdaq100':True},
        {'code':'TXN','yfSymbol':'TXN','name':'Texas Instruments','sector':'Technology','exchange':'NASDAQ','base':198.5,'sp500':True,'nasdaq100':True},
        {'code':'AMAT','yfSymbol':'AMAT','name':'Applied Materials','sector':'Technology','exchange':'NASDAQ','base':225.4,'sp500':True,'nasdaq100':True},
        {'code':'MU','yfSymbol':'MU','name':'Micron','sector':'Technology','exchange':'NASDAQ','base':108.6,'sp500':True,'nasdaq100':True},
    ]
    
    def get_symbol_list(self):
        result = []
        for s in self.BASE_SYMBOLS:
            d = {'sp500': False, 'dow': False, 'nasdaq100': False}
            d.update(s)
            result.append(d)
        return result
    
    def get_quick_key_map(self, s):
        return {
            'sp500': s.get('sp500', False),
            'dow': s.get('dow', False),
            'nasdaq100': s.get('nasdaq100', False),
        }
