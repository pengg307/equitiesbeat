Multi-Market Trading Dashboard
==============================

A real-time trading dashboard supporting 4 markets:
  - CN Stock (A-Shares, simulated)
  - US Stock (NYSE/NASDAQ, real data via yfinance)
  - US Futures (CME/CBOT/NYMEX/COMEX/ICE, real data)
  - CN Futures (SHFE/DCE/CZCE/CFFEX, simulated)

Features
--------
  - Real-time WebSocket updates with auto-reconnect
  - Technical indicators: MA, BOLL, MACD, RSI, KDJ, OBV
  - Volume Profile with POC/VAH/VAL
  - 30+ filterable signals (AND/OR logic)
  - Resizable 3-panel chart
  - Auto-fallback to simulation when API fails

Quick Start
-----------
Linux/Mac:
    chmod +x run.sh
    ./run.sh

Windows:
    run.bat

Manual:
    pip install -r requirements.txt
    python app.py

Then open: http://localhost:8080

API Endpoints
-------------
  GET  /                                Dashboard UI
  GET  /api/markets                     List markets
  GET  /api/market/{key}/symbols        Get symbols
  GET  /api/market/{key}/symbol/{code}  Symbol detail
  GET  /api/market/{key}/indices        Market indices
  GET  /api/health                      Health check
  WS   /ws                              WebSocket live updates
