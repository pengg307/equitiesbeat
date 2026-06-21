"""Chinese Futures - Simulated (with CSV data for precious metals)"""
from .base import BaseMarket
from config import Config


class CNFuturesMarket(BaseMarket):
    KEY = 'CN_FUT'
    NAME = 'CN Futures'
    CURRENCY_SYMBOL = 'CNY'
    DECIMALS = 2
    USE_REAL_DATA = False
    LIMIT_UP = 999
    LIMIT_DN = -999
    UNIT = 'contracts'
    SIMULATION_VOL = 0.020

    # CSV data directory for CN futures
    CSV_DIR = Config.CN_FUT_CSV_DIR if getattr(Config, 'CN_FUT_CSV_ENABLED', False) else None
    
    EXCHANGES = [
        ['', 'All Exchanges'],
        ['SHFE', 'SHFE'],
        ['DCE', 'DCE'],
        ['CZCE', 'CZCE'],
        ['CFFEX', 'CFFEX'],
        ['INE', 'INE'],
    ]
    SECTORS = ['StockIndex', 'Bonds', 'NonFerrous', 'Precious', 'Ferrous', 'Energy/Chem', 'Agriculture']
    QUICK_FILTERS = [
        ['all', 'All'],
        ['index', 'Index'],
        ['rates', 'Bonds'],
        ['metals', 'Metals'],
        ['energy', 'Energy'],
        ['chems', 'Chemicals'],
        ['ags', 'Agriculture']
    ]
    INDICES = [
        {'name': 'IF Main', 'code': 'IF.CFFEX', 'base': 3920},
        {'name': 'IH Main', 'code': 'IH.CFFEX', 'base': 2685},
        {'name': 'IC Main', 'code': 'IC.CFFEX', 'base': 5825},
        {'name': 'Rebar Main', 'code': 'rb.SHFE', 'base': 3585},
        {'name': 'Copper Main', 'code': 'cu.SHFE', 'base': 82500},
        {'name': 'Crude Main', 'code': 'sc.INE', 'base': 585},
    ]
    TRADING_HOURS = [[9, 0, 11, 30], [13, 30, 15, 0], [21, 0, 23, 0]]
    
    BASE_SYMBOLS = [
        {'code':'IF2506','name':'CSI 300 Index','sector':'StockIndex','exchange':'CFFEX','base':3920.5,'month':'2506','oi':185000,'group':'index'},
        {'code':'IH2506','name':'SSE 50 Index','sector':'StockIndex','exchange':'CFFEX','base':2685.5,'month':'2506','oi':85000,'group':'index'},
        {'code':'IC2506','name':'CSI 500 Index','sector':'StockIndex','exchange':'CFFEX','base':5825.5,'month':'2506','oi':185000,'group':'index'},
        {'code':'IM2506','name':'CSI 1000 Index','sector':'StockIndex','exchange':'CFFEX','base':6285.5,'month':'2506','oi':285000,'group':'index'},
        {'code':'T2506','name':'10Y Treasury','sector':'Bonds','exchange':'CFFEX','base':104.5,'month':'2506','oi':285000,'group':'rates'},
        {'code':'TF2506','name':'5Y Treasury','sector':'Bonds','exchange':'CFFEX','base':103.5,'month':'2506','oi':185000,'group':'rates'},
        {'code':'TS2506','name':'2Y Treasury','sector':'Bonds','exchange':'CFFEX','base':101.5,'month':'2506','oi':85000,'group':'rates'},
        {'code':'cu2506','name':'Copper','sector':'NonFerrous','exchange':'SHFE','base':82500,'month':'2506','oi':285000,'group':'metals'},
        {'code':'al2506','name':'Aluminum','sector':'NonFerrous','exchange':'SHFE','base':20850,'month':'2506','oi':485000,'group':'metals'},
        {'code':'zn2506','name':'Zinc','sector':'NonFerrous','exchange':'SHFE','base':24850,'month':'2506','oi':185000,'group':'metals'},
        {'code':'ni2506','name':'Nickel','sector':'NonFerrous','exchange':'SHFE','base':148500,'month':'2506','oi':85000,'group':'metals'},
        {'code':'pb2506','name':'Lead','sector':'NonFerrous','exchange':'SHFE','base':18250,'month':'2506','oi':85000,'group':'metals'},
        {'code':'sn2506','name':'Tin','sector':'NonFerrous','exchange':'SHFE','base':268500,'month':'2506','oi':45000,'group':'metals'},
        {'code':'au2506','name':'Gold','sector':'Precious','exchange':'SHFE','base':548.5,'month':'2506','oi':285000,'group':'metals','csvData':True,'csvTimeframe':'15min'},
        {'code':'ag2506','name':'Silver','sector':'Precious','exchange':'SHFE','base':6885,'month':'2506','oi':485000,'group':'metals','csvData':True,'csvTimeframe':'15min'},
        {'code':'rb2510','name':'Rebar','sector':'Ferrous','exchange':'SHFE','base':3585,'month':'2510','oi':1850000,'group':'metals'},
        {'code':'hc2510','name':'Hot Rolled Coil','sector':'Ferrous','exchange':'SHFE','base':3725,'month':'2510','oi':485000,'group':'metals'},
        {'code':'i2509','name':'Iron Ore','sector':'Ferrous','exchange':'DCE','base':825.5,'month':'2509','oi':685000,'group':'metals'},
        {'code':'j2509','name':'Coke','sector':'Ferrous','exchange':'DCE','base':2185,'month':'2509','oi':185000,'group':'metals'},
        {'code':'jm2509','name':'Coking Coal','sector':'Ferrous','exchange':'DCE','base':1485,'month':'2509','oi':285000,'group':'metals'},
        {'code':'ss2510','name':'Stainless Steel','sector':'Ferrous','exchange':'SHFE','base':13850,'month':'2510','oi':185000,'group':'metals'},
        {'code':'sc2507','name':'Crude Oil','sector':'Energy/Chem','exchange':'INE','base':585.5,'month':'2507','oi':185000,'group':'energy'},
        {'code':'fu2509','name':'Fuel Oil','sector':'Energy/Chem','exchange':'SHFE','base':3285,'month':'2509','oi':485000,'group':'energy'},
        {'code':'bu2509','name':'Asphalt','sector':'Energy/Chem','exchange':'SHFE','base':3685,'month':'2509','oi':285000,'group':'energy'},
        {'code':'lpg2509','name':'LPG','sector':'Energy/Chem','exchange':'DCE','base':4585,'month':'2509','oi':85000,'group':'energy'},
        {'code':'pp2509','name':'Polypropylene','sector':'Energy/Chem','exchange':'DCE','base':7585,'month':'2509','oi':385000,'group':'chems'},
        {'code':'l2509','name':'Polyethylene','sector':'Energy/Chem','exchange':'DCE','base':8285,'month':'2509','oi':285000,'group':'chems'},
        {'code':'v2509','name':'PVC','sector':'Energy/Chem','exchange':'DCE','base':5485,'month':'2509','oi':485000,'group':'chems'},
        {'code':'ma509','name':'Methanol','sector':'Energy/Chem','exchange':'CZCE','base':2485,'month':'2509','oi':585000,'group':'chems'},
        {'code':'ta509','name':'PTA','sector':'Energy/Chem','exchange':'CZCE','base':5785,'month':'2509','oi':885000,'group':'chems'},
        {'code':'eg2509','name':'Ethylene Glycol','sector':'Energy/Chem','exchange':'DCE','base':4585,'month':'2509','oi':385000,'group':'chems'},
        {'code':'eb2509','name':'Styrene','sector':'Energy/Chem','exchange':'DCE','base':8485,'month':'2509','oi':185000,'group':'chems'},
        {'code':'ur509','name':'Urea','sector':'Energy/Chem','exchange':'CZCE','base':1885,'month':'2509','oi':285000,'group':'chems'},
        {'code':'m2509','name':'Soybean Meal','sector':'Agriculture','exchange':'DCE','base':3185,'month':'2509','oi':1850000,'group':'ags'},
        {'code':'y2509','name':'Soybean Oil','sector':'Agriculture','exchange':'DCE','base':7885,'month':'2509','oi':585000,'group':'ags'},
        {'code':'p2509','name':'Palm Oil','sector':'Agriculture','exchange':'DCE','base':8485,'month':'2509','oi':485000,'group':'ags'},
        {'code':'c2509','name':'Corn','sector':'Agriculture','exchange':'DCE','base':2385,'month':'2509','oi':1485000,'group':'ags'},
        {'code':'cs2509','name':'Corn Starch','sector':'Agriculture','exchange':'DCE','base':2785,'month':'2509','oi':185000,'group':'ags'},
        {'code':'a2509','name':'Soybean 1','sector':'Agriculture','exchange':'DCE','base':4385,'month':'2509','oi':285000,'group':'ags'},
        {'code':'b2509','name':'Soybean 2','sector':'Agriculture','exchange':'DCE','base':3685,'month':'2509','oi':85000,'group':'ags'},
        {'code':'cf509','name':'Cotton','sector':'Agriculture','exchange':'CZCE','base':15850,'month':'2509','oi':585000,'group':'ags'},
        {'code':'sr509','name':'Sugar','sector':'Agriculture','exchange':'CZCE','base':6285,'month':'2509','oi':685000,'group':'ags'},
        {'code':'oi509','name':'Rapeseed Oil','sector':'Agriculture','exchange':'CZCE','base':8485,'month':'2509','oi':385000,'group':'ags'},
        {'code':'rm509','name':'Rapeseed Meal','sector':'Agriculture','exchange':'CZCE','base':2785,'month':'2509','oi':285000,'group':'ags'},
        {'code':'ap510','name':'Apple','sector':'Agriculture','exchange':'CZCE','base':8285,'month':'2510','oi':185000,'group':'ags'},
        {'code':'cj510','name':'Red Date','sector':'Agriculture','exchange':'CZCE','base':12850,'month':'2510','oi':85000,'group':'ags'},
    ]
    
    def get_symbol_list(self):
        return [dict(s) for s in self.BASE_SYMBOLS]
    
    def get_quick_key_map(self, s):
        g = s.get('group', '')
        return {
            'index': g == 'index',
            'rates': g == 'rates',
            'metals': g == 'metals',
            'energy': g == 'energy',
            'chems': g == 'chems',
            'ags': g == 'ags',
        }
