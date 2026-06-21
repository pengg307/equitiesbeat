"""Monitor CSV file changes and push incremental updates via WebSocket.

Phase 2: Incremental update support for CN futures CSV data.
Scans CSV files every 30 seconds, detects new rows, and pushes updates.
"""
import os
import time
import asyncio
from typing import Dict, Any, Optional
from core.csv_loader import CSVLoader


class CSVWatcher:
    """
    Watch CSV files for incremental updates.
    
    Every 30 seconds:
    1. Snapshot row count + last line timestamp for each CSV file
    2. Compare with previous snapshot
    3. Parse new rows as ohlcv entries
    4. Append to corresponding symbol's ohlcv array
    5. Recalculate signals
    6. Push quote_update via WebSocket
    """
    
    def __init__(self, csv_dir: str, market_manager=None):
        self.csv_dir = csv_dir
        self.market_manager = market_manager
        # Track snapshots: {contract_code: {'rows': int, 'last_ts': str, 'mtime': float}}
        self._snapshots: Dict[str, Dict[str, Any]] = {}
        self._running = False
    
    def _get_snapshot(self, csv_file: str, contract_code: str) -> Optional[Dict[str, Any]]:
        """Take a snapshot of the current CSV file state."""
        if not os.path.exists(csv_file):
            return None
        
        stat = os.stat(csv_file)
        mtime = stat.st_mtime
        
        # Count rows
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            row_count = len(lines) - 1  # Exclude header
            last_line = lines[-1].strip() if row_count > 0 else ""
            # Extract timestamp from last line (first column)
            last_ts = last_line.split(',')[0] if last_line else ""
        
        return {
            'rows': row_count,
            'last_ts': last_ts,
            'mtime': mtime,
            'file': csv_file
        }
    
    def detect_changes(self) -> Dict[str, Dict[str, Any]]:
        """Detect new rows in all watched CSV files.
        
        Returns: {contract_code: {'new_rows': int, 'new_data': [...], 'latest': {...}}}
        """
        changes = {}
        
        for code, mapping in CSVLoader.CONTRACT_MAP.items():
            for timeframe in ['15min', '60min', '5min', '1min']:
                csv_file = CSVLoader.find_csv(self.csv_dir, code, timeframe)
                if not csv_file or not os.path.exists(csv_file):
                    continue
                
                snapshot = self._get_snapshot(csv_file, code)
                if snapshot is None:
                    continue
                
                prev = self._snapshots.get(code, {})
                
                if prev and prev.get('rows', 0) < snapshot['rows']:
                    # New rows detected
                    new_row_count = snapshot['rows'] - prev['rows']
                    
                    # Read new rows
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        new_lines = lines[1 + prev['rows']:]  # Skip header + old rows
                    
                    # Parse new rows into ohlcv format
                    new_ohlcv = []
                    for line in new_lines:
                        parts = line.strip().split(',')
                        if len(parts) >= 5:
                            try:
                                new_ohlcv.append({
                                    't': parts[0],
                                    'o': float(parts[1]),
                                    'h': float(parts[2]),
                                    'l': float(parts[3]),
                                    'c': float(parts[4]),
                                    'v': int(float(parts[5])) if len(parts) > 5 else 0
                                })
                            except (ValueError, IndexError):
                                continue
                    
                    if new_ohlcv:
                        changes[code] = {
                            'timeframe': timeframe,
                            'new_rows': len(new_ohlcv),
                            'new_data': new_ohlcv,
                            'latest_ts': snapshot['last_ts'],
                            'csv_file': csv_file
                        }
                
                # Update snapshot
                self._snapshots[code] = snapshot
        
        return changes
    
    async def watch_loop(self, interval: int = 30):
        """Main watch loop. Runs indefinitely until stopped."""
        self._running = True
        print(f"[CSVWatcher] Starting watch loop (interval={interval}s)")
        
        while self._running:
            try:
                changes = self.detect_changes()
                
                if changes:
                    for code, change_info in changes.items():
                        print(f"[CSVWatcher] {code}: +{change_info['new_rows']} new rows ({change_info['timeframe']})")
                        
                        # Update market manager symbols if available
                        if self.market_manager:
                            await self._update_symbols(code, change_info)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                print(f"[CSVWatcher] Error: {e}")
                await asyncio.sleep(interval)
    
    async def _update_symbols(self, contract_code: str, change_info: Dict[str, Any]):
        """Update symbol data with new CSV rows."""
        if not self.market_manager:
            return
        
        # Find the CN_FUT market
        cn_fut_market = None
        for market in self.market_manager.markets.values():
            if hasattr(market, '__class__') and 'CN' in market.__class__.__name__:
                cn_fut_market = market
                break
        
        if not cn_fut_market or not hasattr(cn_fut_market, 'symbols'):
            return
        
        # Find the symbol and append new ohlcv data
        for symbol in cn_fut_market.symbols:
            if symbol.code == contract_code:
                new_data = change_info.get('new_data', [])
                if new_data and hasattr(symbol, 'ohlcv'):
                    symbol.ohlcv.extend(new_data)
                    
                    # Update latest price
                    if new_data:
                        last = new_data[-1]
                        symbol.price = last['c']
                        symbol.high = last['h']
                        symbol.low = last['l']
                        symbol.volume = last['v']
                        symbol.timestamp = last['t']
                        
                        # Recalculate change/changePct
                        symbol.change = symbol.price - symbol.prevClose
                        symbol.changePct = (symbol.change / symbol.prevClose * 100) if symbol.prevClose else 0
                        
                        print(f"[CSVWatcher] Updated {contract_code}: price={symbol.price}, ohlcv count={len(symbol.ohlcv)}")
                        break
    
    def stop(self):
        """Stop the watch loop."""
        self._running = False
        print("[CSVWatcher] Stopping watch loop.")
    
    def reset_snapshots(self):
        """Reset all snapshots (useful after manual CSV regeneration)."""
        self._snapshots.clear()
        print("[CSVWatcher] Snapshots reset.")
