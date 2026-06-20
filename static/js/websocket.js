class DashboardWS {
  constructor(url, onMessage) {
    this.url = url;
    this.onMessage = onMessage;
    this.ws = null;
    this.reconnectDelay = 1000;
    this.maxReconnectDelay = 30000;
    this.pingInterval = null;
    this.currentMarket = null;
    this.statusEl = document.getElementById('wsStatus');
  }
  
  connect() {
    try {
      this.setStatus('connecting');
      this.ws = new WebSocket(this.url);
      
      this.ws.onopen = () => {
        console.log('WS connected');
        this.setStatus('connected');
        this.reconnectDelay = 1000;
        this.startPing();
        if (this.currentMarket) {
          this.subscribe(this.currentMarket);
        }
      };
      
      this.ws.onmessage = (e) => {
        try {
          const msg = JSON.parse(e.data);
          if (msg.type === 'pong') return;
          if (this.onMessage) this.onMessage(msg);
        } catch (err) {
          console.error('WS parse error:', err);
        }
      };
      
      this.ws.onclose = () => {
        console.log('WS disconnected');
        this.setStatus('disconnected');
        this.stopPing();
        this.scheduleReconnect();
      };
      
      this.ws.onerror = (e) => {
        console.error('WS error:', e);
      };
    } catch (e) {
      console.error('WS init error:', e);
      this.scheduleReconnect();
    }
  }
  
  scheduleReconnect() {
    setTimeout(() => {
      this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, this.maxReconnectDelay);
      this.connect();
    }, this.reconnectDelay);
  }
  
  startPing() {
    this.stopPing();
    this.pingInterval = setInterval(() => {
      this.send({ action: 'ping' });
    }, 20000);
  }
  
  stopPing() {
    if (this.pingInterval) clearInterval(this.pingInterval);
  }
  
  send(obj) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(obj));
    }
  }
  
  subscribe(marketKey) {
    this.currentMarket = marketKey;
    this.send({ action: 'subscribe', market: marketKey });
  }
  
  setStatus(s) {
    if (!this.statusEl) return;
    this.statusEl.className = 'ws-status';
    if (s === 'connected') {
      this.statusEl.title = 'Connected';
    } else if (s === 'connecting') {
      this.statusEl.classList.add('connecting');
      this.statusEl.title = 'Connecting...';
    } else {
      this.statusEl.classList.add('dc');
      this.statusEl.title = 'Disconnected';
    }
  }
}
