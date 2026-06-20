"""A-Shares (China) - Simulated, English names"""
from .base import BaseMarket


class CNStockMarket(BaseMarket):
    KEY = 'CN_STOCK'
    NAME = 'A-Share'
    CURRENCY_SYMBOL = 'CNY'
    DECIMALS = 2
    USE_REAL_DATA = False
    LIMIT_UP = 9.9
    LIMIT_DN = -9.9
    UNIT = 'stocks'
    SIMULATION_VOL = 0.025
    
    EXCHANGES = [['', 'All'], ['SH', 'Shanghai'], ['SZ', 'Shenzhen']]
    SECTORS = ['Bank', 'Tech', 'Pharma', 'Consumer', 'Energy', 'RealEstate', 'Manufacturing', 'Finance']
    QUICK_FILTERS = [
        ['all', 'All'],
        ['sh50', 'SSE 50'],
        ['csi300', 'CSI 300'],
        ['gem', 'ChiNext']
    ]
    INDICES = [
        {'name': 'SSE Composite', 'code': '000001.SH', 'base': 3186},
        {'name': 'SZSE Component', 'code': '399001.SZ', 'base': 10380},
        {'name': 'ChiNext', 'code': '399006.SZ', 'base': 2048},
        {'name': 'CSI 300', 'code': '000300.SH', 'base': 3921},
        {'name': 'CSI 500', 'code': '000905.SH', 'base': 5836},
        {'name': 'STAR 50', 'code': '000688.SH', 'base': 988},
    ]
    TRADING_HOURS = [[9, 30, 11, 30], [13, 0, 15, 0]]
    
    BASE_SYMBOLS = [
        {'code':'600036','name':'CMB Bank','sector':'Bank','exchange':'SH','base':42.5,'sh50':True,'csi':True},
        {'code':'600519','name':'Kweichow Moutai','sector':'Consumer','exchange':'SH','base':1680,'sh50':True,'csi':True},
        {'code':'601318','name':'Ping An','sector':'Finance','exchange':'SH','base':48.2,'sh50':True,'csi':True},
        {'code':'600276','name':'Hengrui Pharma','sector':'Pharma','exchange':'SH','base':38.1,'csi':True},
        {'code':'601166','name':'Industrial Bank','sector':'Bank','exchange':'SH','base':19.3,'sh50':True,'csi':True},
        {'code':'600887','name':'Yili Group','sector':'Consumer','exchange':'SH','base':30.5,'csi':True},
        {'code':'600104','name':'SAIC Motor','sector':'Manufacturing','exchange':'SH','base':17.2,'sh50':True,'csi':True},
        {'code':'601088','name':'China Shenhua','sector':'Energy','exchange':'SH','base':38.6,'sh50':True,'csi':True},
        {'code':'600028','name':'Sinopec','sector':'Energy','exchange':'SH','base':6.2,'sh50':True,'csi':True},
        {'code':'601398','name':'ICBC','sector':'Bank','exchange':'SH','base':5.6,'sh50':True,'csi':True},
        {'code':'601939','name':'CCB Bank','sector':'Bank','exchange':'SH','base':7.1,'sh50':True,'csi':True},
        {'code':'601288','name':'ABC Bank','sector':'Bank','exchange':'SH','base':3.8,'sh50':True,'csi':True},
        {'code':'601857','name':'PetroChina','sector':'Energy','exchange':'SH','base':8.5,'sh50':True,'csi':True},
        {'code':'600585','name':'Conch Cement','sector':'Manufacturing','exchange':'SH','base':35.2,'csi':True},
        {'code':'601668','name':'China State Construction','sector':'RealEstate','exchange':'SH','base':5.2,'sh50':True,'csi':True},
        {'code':'600030','name':'CITIC Securities','sector':'Finance','exchange':'SH','base':22.4,'sh50':True,'csi':True},
        {'code':'600000','name':'SPD Bank','sector':'Bank','exchange':'SH','base':8.1,'csi':True},
        {'code':'000858','name':'Wuliangye','sector':'Consumer','exchange':'SZ','base':158.5,'csi':True},
        {'code':'000333','name':'Midea Group','sector':'Manufacturing','exchange':'SZ','base':62.3,'csi':True},
        {'code':'002415','name':'Hikvision','sector':'Tech','exchange':'SZ','base':32.1,'csi':True},
        {'code':'000725','name':'BOE Tech','sector':'Tech','exchange':'SZ','base':4.8,'csi':True},
        {'code':'002594','name':'BYD','sector':'Manufacturing','exchange':'SZ','base':248.6,'csi':True},
        {'code':'000002','name':'Vanke','sector':'RealEstate','exchange':'SZ','base':8.5,'csi':True},
        {'code':'300750','name':'CATL','sector':'Tech','exchange':'SZ','base':198.4,'csi':True,'gem':True},
        {'code':'000001','name':'Ping An Bank','sector':'Bank','exchange':'SZ','base':12.3,'csi':True},
        {'code':'002230','name':'iFlytek','sector':'Tech','exchange':'SZ','base':46.2,'csi':True},
        {'code':'300059','name':'East Money','sector':'Finance','exchange':'SZ','base':18.6,'csi':True,'gem':True},
        {'code':'000651','name':'Gree Electric','sector':'Manufacturing','exchange':'SZ','base':42.1,'csi':True},
        {'code':'002714','name':'Muyuan Foods','sector':'Consumer','exchange':'SZ','base':52.4,'csi':True},
        {'code':'300760','name':'Mindray Medical','sector':'Pharma','exchange':'SZ','base':268.5,'csi':True,'gem':True},
    ]
    
    ENAMES = ['NewEnergy','Chip','AI','Cloud','BioTech','Material','SemiCon','SmartMfg','Solar','Storage','Robot','Digital']
    SUFFS = ['Tech','Group','Holdings','Industry','Electric','Material','Equipment','Info','Comm','Corp']
    
    def get_symbol_list(self):
        import hashlib
        symbols = []
        for s in self.BASE_SYMBOLS:
            d = {'sh50': False, 'csi': False, 'gem': False}
            d.update(s)
            symbols.append(d)
        used = set(s['code'] for s in symbols)
        i = 0
        while len(symbols) < 150:
            is_gem = i % 7 == 0
            exc = 'SH' if i % 3 == 0 else 'SZ'
            h = int(hashlib.md5(("cn" + str(i)).encode()).hexdigest(), 16)
            if exc == 'SH':
                code = str(600100 + h % 3000).zfill(6)
            elif is_gem:
                code = str(300001 + h % 899).zfill(6)
            else:
                code = str(2001 + h % 897999).zfill(6)
            i += 1
            if code in used: continue
            used.add(code)
            name = self.ENAMES[h % len(self.ENAMES)] + ' ' + self.SUFFS[(h >> 4) % len(self.SUFFS)]
            symbols.append({
                'code': code, 'name': name,
                'sector': self.SECTORS[(h >> 8) % len(self.SECTORS)],
                'exchange': exc,
                'base': round((h % 20000) / 100 + 3, 2),
                'sh50': False, 'csi': False, 'gem': is_gem
            })
        return symbols
    
    def get_quick_key_map(self, s):
        return {
            'sh50': s.get('sh50', False),
            'csi300': s.get('csi', False),
            'gem': s.get('gem', False),
        }
