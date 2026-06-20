"""Main FastAPI Server - Progressive Loading"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config import Config
from markets import MarketManager
from ws.manager import ConnectionManager
from core.data_provider import DataProvider

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
log = logging.getLogger("dashboard")

logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('peewee').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('uvicorn.access').setLevel(logging.WARNING)

mm = MarketManager()
cm = ConnectionManager()


async def quote_broadcaster():
    while True:
        try:
            await asyncio.sleep(Config.WS_QUOTE_INTERVAL)
            for key, market in mm.all().items():
                if key not in cm.subscriptions or not cm.subscriptions[key]:
                    continue
                
                await market.refresh_quotes()
                payload = [
                    {
                        'code': s['code'],
                        'price': s['price'],
                        'change': s['change'],
                        'changePct': s['changePct'],
                        'high': s['high'],
                        'low': s['low'],
                        'volume': s['volume'],
                        'isSimulated': s.get('isSimulated', True),
                    }
                    for s in market.symbols
                ]
                await cm.broadcast_to_market(key, {
                    'type': 'quote_update',
                    'market': key,
                    'data': payload,
                })
        except asyncio.CancelledError:
            break
        except Exception as e:
            log.error("Broadcaster error: " + str(e), exc_info=True)


async def loading_progress_broadcaster():
    """Broadcast loading progress to subscribed clients"""
    while True:
        try:
            await asyncio.sleep(5)
            for key, market in mm.all().items():
                if not market.USE_REAL_DATA or market._live_upgrade_done:
                    continue
                if key not in cm.subscriptions or not cm.subscriptions[key]:
                    continue
                
                status = market.get_loading_status()
                await cm.broadcast_to_market(key, {
                    'type': 'loading_progress',
                    'market': key,
                    'data': status,
                })
        except asyncio.CancelledError:
            break
        except Exception:
            pass


async def periodic_summary():
    """Print summary periodically until all done"""
    await asyncio.sleep(10)  # initial wait
    
    consecutive_done = 0
    while True:
        try:
            await asyncio.sleep(20)
            
            log.info("=" * 60)
            log.info("MARKET STATUS")
            log.info("=" * 60)
            
            all_done = True
            for key, market in mm.all().items():
                status = market.get_loading_status()
                if not market._loaded:
                    log.info("  [" + key + "] still loading...")
                    all_done = False
                    continue
                
                if market.USE_REAL_DATA:
                    if status['liveUpgradeDone']:
                        log.info("  [" + key + "] " + market.NAME + ": " + 
                                 str(status['total']) + " symbols (LIVE: " + 
                                 str(status['live']) + ", SIM fallback: " + 
                                 str(status['simulated']) + ") - COMPLETE")
                    else:
                        progress_pct = (status['liveUpgradeProgress'] * 100 // max(status['liveUpgradeTotal'], 1))
                        log.info("  [" + key + "] " + market.NAME + ": " + 
                                 str(status['total']) + " symbols (LIVE: " + 
                                 str(status['live']) + "/" + str(status['liveUpgradeTotal']) + 
                                 ", " + str(progress_pct) + "% upgraded)")
                        all_done = False
                else:
                    log.info("  [" + key + "] " + market.NAME + ": " + 
                             str(status['total']) + " symbols (all simulated)")
            
            log.info("=" * 60)
            
            if all_done:
                consecutive_done += 1
                if consecutive_done >= 2:
                    log.info("All markets fully loaded. Switching to passive monitoring.")
                    return
            else:
                consecutive_done = 0
        except asyncio.CancelledError:
            break
        except Exception as e:
            log.error("Summary error: " + str(e))


async def periodic_retry():
    """Periodically clear failed-symbol cache to retry yfinance fetches"""
    while True:
        try:
            await asyncio.sleep(300)
            stats = DataProvider.get_stats()
            if stats['failed_count'] > 0:
                log.info("Clearing " + str(stats['failed_count']) + " failed symbols for retry")
                DataProvider.clear_failed_cache()
        except asyncio.CancelledError:
            break
        except Exception:
            pass


@asynccontextmanager
async def lifespan(app):
    log.info("=" * 60)
    log.info("Starting Multi-Market Dashboard")
    log.info("Enabled markets: " + str(Config.ENABLED_MARKETS))
    log.info("Mode: Progressive Loading (instant SIM, then upgrade to LIVE)")
    log.info("=" * 60)
    
    # Initialize markets (this is now FAST - just builds simulated data)
    init_task = asyncio.create_task(mm.initialize(Config.ENABLED_MARKETS))
    
    bc_task = asyncio.create_task(quote_broadcaster())
    progress_task = asyncio.create_task(loading_progress_broadcaster())
    retry_task = asyncio.create_task(periodic_retry())
    summary_task = asyncio.create_task(periodic_summary())
    
    log.info("Server ready at http://" + Config.HOST + ":" + str(Config.PORT))
    log.info("UI available IMMEDIATELY with simulated data")
    log.info("LIVE data will progressively upgrade symbols in background")
    yield
    
    log.info("Shutting down...")
    bc_task.cancel()
    progress_task.cancel()
    retry_task.cancel()
    summary_task.cancel()
    init_task.cancel()


app = FastAPI(title="Multi-Market Dashboard", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def index():
    with open(os.path.join(static_dir, "index.html"), "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/api/markets")
async def get_markets():
    return {
        'markets': [m.to_metadata() for m in mm.all().values()],
        'default': Config.ENABLED_MARKETS[0],
    }


@app.get("/api/market/{key}/symbols")
async def get_symbols(key):
    market = mm.get(key)
    if not market:
        raise HTTPException(404, "Market not found: " + key)
    if not market._loaded:
        return JSONResponse({'loading': True, 'symbols': []})
    return {
        'market': key,
        'count': len(market.symbols),
        'symbols': market.get_symbols_payload(),
        'loadingStatus': market.get_loading_status(),
    }


@app.get("/api/market/{key}/symbol/{code}")
async def get_symbol_detail(key, code):
    market = mm.get(key)
    if not market:
        raise HTTPException(404, "Market not found: " + key)
    
    sym = market.get_symbol_detail(code)
    if not sym:
        raise HTTPException(404, "Symbol not found: " + code)
    
    return sym


@app.get("/api/market/{key}/indices")
async def get_indices(key):
    market = mm.get(key)
    if not market:
        raise HTTPException(404, "Market not found: " + key)
    
    indices_out = []
    if market.USE_REAL_DATA:
        for idx in market.INDICES:
            quote = await DataProvider.fetch_yf_quote(idx['code'])
            if quote:
                out = dict(idx)
                out.update({
                    'value': quote['price'],
                    'change': quote['change'],
                    'pct': quote['changePct'],
                })
                indices_out.append(out)
            else:
                import random
                p = (random.random() - 0.46) * 0.025
                v = idx['base'] * (1 + p)
                out = dict(idx)
                out.update({'value': v, 'change': v - idx['base'], 'pct': p * 100})
                indices_out.append(out)
    else:
        import random
        for idx in market.INDICES:
            p = (random.random() - 0.46) * 0.025
            v = idx['base'] * (1 + p)
            out = dict(idx)
            out.update({'value': v, 'change': v - idx['base'], 'pct': p * 100})
            indices_out.append(out)
    
    return {'market': key, 'indices': indices_out}


@app.get("/api/loading")
async def get_loading_status():
    """Show progressive loading status for all markets"""
    return {
        'markets': {k: m.get_loading_status() for k, m in mm.all().items()}
    }


@app.get("/api/health")
async def health():
    markets_info = {}
    for k, m in mm.all().items():
        status = m.get_loading_status()
        markets_info[k] = status
    return {
        'status': 'ok',
        'connections': cm.total_connections,
        'markets': markets_info,
        'data_provider': DataProvider.get_stats(),
    }


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await cm.connect(ws)
    try:
        while True:
            data = await ws.receive_json()
            action = data.get('action')
            
            if action == 'subscribe':
                market_key = data.get('market')
                if market_key in mm.all():
                    await cm.subscribe(ws, market_key)
                    market = mm.get(market_key)
                    await ws.send_json({
                        'type': 'subscribed',
                        'market': market_key,
                        'loadingStatus': market.get_loading_status()
                    })
            
            elif action == 'ping':
                await ws.send_json({'type': 'pong'})
            
            elif action == 'get_loading':
                await ws.send_json({
                    'type': 'loading_status',
                    'markets': {k: m.get_loading_status() for k, m in mm.all().items()}
                })
    
    except WebSocketDisconnect:
        await cm.disconnect(ws)
    except Exception as e:
        log.error("WS error: " + str(e))
        await cm.disconnect(ws)


if __name__ == "__main__":
    import uvicorn
    print("")
    print("=" * 70)
    print("  Multi-Market Trading Dashboard (Progressive Loading)")
    print("  URL:     http://localhost:" + str(Config.PORT))
    print("  Health:  http://localhost:" + str(Config.PORT) + "/api/health")
    print("  Loading: http://localhost:" + str(Config.PORT) + "/api/loading")
    print("  Markets: " + ", ".join(Config.ENABLED_MARKETS))
    print("=" * 70)
    print("")
    print("  UI loads IMMEDIATELY with simulated data")
    print("  Symbols are progressively upgraded to LIVE data")
    print("  Watch the console for upgrade progress")
    print("")
    print("=" * 70)
    print("")
    
    uvicorn.run("app:app", host=Config.HOST, port=Config.PORT, reload=False, log_level="info")
