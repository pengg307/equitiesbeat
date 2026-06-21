"""Global configuration"""

class Config:
    HOST = "0.0.0.0"
    PORT = 8080
    DEBUG = True
    
    QUOTE_CACHE_TTL = 5
    HISTORY_CACHE_TTL = 300
    INDEX_CACHE_TTL = 10
    
    WS_QUOTE_INTERVAL = 3
    WS_INDEX_INTERVAL = 5
    
    MAX_HISTORY_DAYS = 365
    DEFAULT_PAGE_SIZE = 20
    
    YF_TIMEOUT = 10
    YF_MAX_RETRIES = 3
    
    ENABLED_MARKETS = ['CN_STOCK', 'US_STOCK', 'US_FUT', 'CN_FUT']

    # CN Futures local CSV data path
    CN_FUT_CSV_DIR = r"E:\aiprojects\kandlecnen\cnenkandle\data_prod"
    CN_FUT_CSV_ENABLED = True  # Global switch for CSV data loading
