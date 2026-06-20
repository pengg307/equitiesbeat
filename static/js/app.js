const App = {
  state: {
    markets: [],
    currentMarket: null,
    currentMarketKey: null,
    symbols: [],
    indices: [],
    currentSymbol: null,
    loadingProgress: {}
  },
  ws: null,
  _refreshTimer: null,
  
  async init() {
    Chart.defaults.color = '#5a7fa8';
    Chart.defaults.borderColor = '#1c3050';
    
    const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
    this.ws = new DashboardWS(proto + '//' + location.host + '/ws', this.handleWSMessage.bind(this));
    this.ws.connect();
    
    this.tickClock();
    const self = this;
    setInterval(() => self.tickClock(), 1000);
    
    document.getElementById('searchInp').addEventListener('input', e => {
      Filters.state.search = e.target.value.trim();
      self.applyFilters();
    });
    document.getElementById('exchSel').addEventListener('change', e => {
      Filters.state.exch = e.target.value;
      self.applyFilters();
    });
    document.getElementById('sectorSel').addEventListener('change', e => {
      Filters.state.sector = e.target.value;
      self.applyFilters();
    });
    document.getElementById('pgSzSel').addEventListener('change', e => {
      Filters.state.pageSize = +e.target.value;
      Filters.state.page = 1;
      self.renderAll();
    });
    
    document.getElementById('overlay').addEventListener('click', e => {
      if (e.target === e.currentTarget) closeModal();
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape') closeModal();
    });
    
    await this.loadMarkets();
  },
  
  async loadMarkets() {
    try {
      const res = await fetch('/api/markets');
      const data = await res.json();
      this.state.markets = data.markets;
      const def = data.default || (data.markets[0] && data.markets[0].key);
      
      const self = this;
      MarketUI.renderTabs(this.state.markets, def, k => self.switchMarket(k));
      await this.switchMarket(def);
    } catch (e) {
      console.error('Failed to load markets:', e);
      document.getElementById('tblArea').innerHTML = '<div class="empty"><div class="ei">!</div><div class="em">Failed to load markets</div></div>';
    }
  },
  
  async switchMarket(key) {
    this.state.currentMarketKey = key;
    this.state.currentMarket = this.state.markets.find(m => m.key === key);
    if (!this.state.currentMarket) return;
    
    document.querySelectorAll('.mkt-tab').forEach(t => t.classList.toggle('on', t.dataset.mkt === key));
    
    MarketUI.buildSidebar(this.state.currentMarket);
    
    Object.assign(Filters.state, { search:'', exch:'', sector:'', chg:'', quick:'all', chips:new Set(), logic:'AND', page:1 });
    document.getElementById('searchInp').value = '';
    Filters.updateBadge();
    
    document.getElementById('tblArea').innerHTML = '<div class="empty"><div class="ei">...</div><div class="em">Loading symbols...</div></div>';
    
    this.ws.subscribe(key);
    
    // Stop any old refresh timer
    if (this._refreshTimer) {
      clearInterval(this._refreshTimer);
      this._refreshTimer = null;
    }
    
    await Promise.all([this.loadSymbols(key), this.loadIndices(key)]);
    
    // For LIVE markets, periodically refresh to catch upgraded symbols
    if (this.state.currentMarket.useRealData) {
      const self = this;
      this._refreshTimer = setInterval(() => {
        if (self.state.currentMarketKey === key) {
          self.loadSymbols(key, true);  // silent refresh
        }
      }, 8000);
    }
  },
  
  async loadSymbols(key, silent) {
    try {
      const res = await fetch('/api/market/' + key + '/symbols');
      const data = await res.json();
      if (data.loading) {
        const self = this;
        setTimeout(() => self.loadSymbols(key), 2000);
        return;
      }
      this.state.symbols = data.symbols || [];
      if (data.loadingStatus) {
        this.state.loadingProgress[key] = data.loadingStatus;
        this.updateProgressBanner();
      }
      this.applyFilters();
    } catch (e) {
      if (!silent) console.error('loadSymbols error:', e);
    }
  },
  
  updateProgressBanner() {
    const M = this.state.currentMarket;
    if (!M || !M.useRealData) return;
    
    const status = this.state.loadingProgress[M.key];
    if (!status) return;
    
    let banner = document.getElementById('progressBanner');
    
    if (status.liveUpgradeDone) {
      if (banner) banner.remove();
      return;
    }
    
    if (!banner) {
      banner = document.createElement('div');
      banner.id = 'progressBanner';
      banner.style.cssText = 'background:rgba(245,158,11,.15);color:var(--yellow);padding:6px 14px;font-size:11px;border-bottom:1px solid rgba(245,158,11,.3);display:flex;align-items:center;gap:8px';
      const resBar = document.querySelector('.res-bar');
      if (resBar) resBar.parentNode.insertBefore(banner, resBar.nextSibling);
    }
    
    const pct = Math.round((status.liveUpgradeProgress / Math.max(status.liveUpgradeTotal, 1)) * 100);
    banner.innerHTML = 
      '<span>Upgrading to LIVE data...</span>' +
      '<div style="flex:1;background:rgba(0,0,0,.3);border-radius:3px;overflow:hidden;height:6px">' +
      '<div style="width:' + pct + '%;background:var(--yellow);height:100%;transition:width .3s"></div>' +
      '</div>' +
      '<span><strong>' + status.live + '</strong>/' + status.liveUpgradeTotal + ' LIVE (' + pct + '%)</span>';
  },
  
  async loadIndices(key) {
    try {
      const res = await fetch('/api/market/' + key + '/indices');
      const data = await res.json();
      this.state.indices = data.indices || [];
      MarketUI.renderIndexBar(this.state.indices);
    } catch (e) {
      console.error('loadIndices error:', e);
    }
  },
  
  handleWSMessage(msg) {
    if (msg.type === 'subscribed' && msg.loadingStatus) {
      this.state.loadingProgress[msg.market] = msg.loadingStatus;
      this.updateProgressBanner();
    }
    
    if (msg.type === 'loading_progress' && msg.market === this.state.currentMarketKey) {
      this.state.loadingProgress[msg.market] = msg.data;
      this.updateProgressBanner();
      // Refresh table to show new LIVE symbols
      this.loadSymbols(msg.market, true);
    }
    
    if (msg.type === 'quote_update' && msg.market === this.state.currentMarketKey) {
      const updates = msg.data;
      const map = new Map(updates.map(u => [u.code, u]));
      let changed = false;
      const self = this;
      this.state.symbols.forEach(s => {
        const u = map.get(s.code);
        if (u) {
          const oldPrice = s.price;
          Object.assign(s, u);
          if (s.intraday) {
            s.intraday.push(u.price);
            if (s.intraday.length > 60) s.intraday.shift();
          }
          changed = true;
          self.flashRow(s.code, u.price > oldPrice);
        }
      });
      if (changed) {
        this.applyFilters();
        if (this.state.currentSymbol) {
          const u = map.get(this.state.currentSymbol.code);
          if (u) {
            Object.assign(this.state.currentSymbol, u);
            this.refreshModalHeader();
          }
        }
      }
    }
  },
  
  flashRow(code, isUp) {
    const row = document.querySelector('tr[data-code="' + code + '"]');
    if (!row) return;
    row.classList.remove('flash-up', 'flash-dn');
    void row.offsetWidth;
    row.classList.add(isUp ? 'flash-up' : 'flash-dn');
    setTimeout(() => row.classList.remove('flash-up', 'flash-dn'), 1000);
  },
  
  applyFilters() {
    if (!this.state.currentMarket) return;
    Filters.state.page = 1;
    Filters.apply(this.state.symbols, this.state.currentMarket);
    this.renderAll();
  },
  
  renderAll() {
    const list = Filters.state.filtered;
    this.renderResBar(list);
    this.renderTagBar();
    this.renderTable(list);
    this.renderPagination(list.length);
  },
  
  renderResBar(list) {
    const M = this.state.currentMarket;
    document.getElementById('totalCnt').textContent = list.length;
    const up = list.filter(s => s.changePct > 0).length;
    const dn = list.filter(s => s.changePct < 0).length;
    const lu = list.filter(s => s.changePct >= M.limitUp).length;
    const liveInList = list.filter(s => !s.isSimulated).length;
    const avg = list.length ? (list.reduce((a,s) => a + s.changePct, 0) / list.length).toFixed(2) : '0.00';
    let meta = '[' + M.name + ']';
    const qf = M.quickFilters.find(q => q[0] === Filters.state.quick);
    if (Filters.state.quick !== 'all' && qf) meta += ' - ' + qf[1];
    if (Filters.state.sector) meta += ' - ' + Filters.state.sector;
    if (Filters.state.chips.size) meta += ' - ' + Filters.state.chips.size + ' signals (' + Filters.state.logic + ')';
    if (M.useRealData) meta += ' - LIVE: ' + liveInList + '/' + list.length;
    document.getElementById('resMeta').textContent = meta;
    let chips = '<div class="sc"><span class="c-up">+</span>Up <strong class="c-up">' + up + '</strong></div>';
    chips += '<div class="sc"><span class="c-dn">-</span>Down <strong class="c-dn">' + dn + '</strong></div>';
    if (M.limitUp < 100) chips += '<div class="sc">Limit+ <strong class="c-up">' + lu + '</strong></div>';
    chips += '<div class="sc">Avg <strong style="' + (+avg > 0 ? 'color:var(--up)' : +avg < 0 ? 'color:var(--down)' : '') + '">' + (+avg > 0 ? '+' : '') + avg + '%</strong></div>';
    document.getElementById('statChips').innerHTML = chips;
  },
  
  renderTagBar() {
    const bar = document.getElementById('tagBar');
    if (Filters.state.chips.size === 0) { bar.className = 'tag-bar empty'; bar.innerHTML = ''; return; }
    bar.className = 'tag-bar';
    let html = '<span style="font-size:9px;color:var(--muted)">Signals:</span>';
    html += '<span class="logic-badge ' + Filters.state.logic.toLowerCase() + '">' + Filters.state.logic + '</span>';
    Array.from(Filters.state.chips).forEach(s => {
      html += '<span class="tag">' + (SIG_LABELS[s] || s) + '<button onclick="App.removeChip(\'' + s + '\')">x</button></span>';
    });
    html += '<button class="tag-clear" onclick="App.clearChips()">Clear</button>';
    bar.innerHTML = html;
  },
  
  removeChip(sig) {
    Filters.state.chips.delete(sig);
    const b = document.querySelector('[data-sig="' + sig + '"]');
    if (b) b.className = 'chip';
    Filters.updateBadge();
    this.applyFilters();
  },
  
  clearChips() {
    Filters.state.chips.clear();
    document.querySelectorAll('.chip').forEach(c => c.className = 'chip');
    Filters.updateBadge();
    this.applyFilters();
  },
  
  renderTable(list) {
    const M = this.state.currentMarket;
    const isFut = M.key === 'US_FUT' || M.key === 'CN_FUT';
    const area = document.getElementById('tblArea');
    if (!list.length) {
      area.innerHTML = '<div class="empty"><div class="ei">?</div><div class="em">No matching symbols</div></div>';
      return;
    }
    const start = (Filters.state.page - 1) * Filters.state.pageSize;
    const page = list.slice(start, start + Filters.state.pageSize);
    
    const cols = [
      ['#', null, 'right'],
      ['Symbol/Name', 'name', 'left'],
      ['Last', 'price', 'left'],
      ['Chg%', 'changePct', 'left'],
      ['Chg', 'change', 'left'],
      ['Open', 'open', 'left'],
      ['High', 'high', 'left'],
      ['Low', 'low', 'left'],
      ['Volume', 'volume', 'left']
    ];
    if (isFut) {
      cols.push(['Open Int', 'openInterest', 'left']);
    } else {
      cols.push(['Turn%', 'turnoverRate', 'left']);
      cols.push(['MktCap', 'marketCap', 'left']);
      cols.push(['PE', 'pe', 'left']);
    }
    cols.push(['Sector', 'sector', 'left']);
    cols.push(['Signals', null, 'left']);
    cols.push(['Trend', null, 'left']);
    
    const ico = f => {
      if (!f) return '';
      if (Filters.state.sort !== f) return '<span class="sarr">v</span>';
      return '<span class="sarr on">' + (Filters.state.dir === 'asc' ? '^' : 'v') + '</span>';
    };
    
    let thead = '<thead><tr>';
    cols.forEach(c => {
      thead += '<th onclick="' + (c[1] ? "App.sortBy('" + c[1] + "')" : 'void 0') + '" style="text-align:' + c[2] + '">' + c[0] + ico(c[1]) + '</th>';
    });
    thead += '</tr></thead>';
    
    const self = this;
    let tbody = '<tbody>';
    page.forEach((s, i) => {
      const up = s.changePct > 0, dn = s.changePct < 0, sign = up ? '+' : '';
      const lu = s.changePct >= M.limitUp, ld = s.changePct <= M.limitDn;
      const dec = M.decimals;
      tbody += '<tr data-code="' + s.code + '" onclick="App.openModal(\'' + s.code + '\')">';
      tbody += '<td style="text-align:right;color:var(--muted);font-size:9px">' + (start + i + 1) + '</td>';
      tbody += '<td><div class="s-nw"><span class="s-name">' + s.name;
      if (lu) tbody += '<span class="lim-tag lim-up">LIM+</span>';
      if (ld) tbody += '<span class="lim-tag lim-dn">LIM-</span>';
      if (isFut && s.month) tbody += '<span class="contract-tag">' + s.month + '</span>';
      if (s.isSimulated) tbody += '<span class="sim-tag">SIM</span>';
      else if (M.useRealData) tbody += '<span class="sim-tag" style="background:rgba(34,197,94,.2);color:#22c55e">LIVE</span>';
      tbody += '</span><span class="s-code">' + s.exchange + ':' + s.code + '</span></div></td>';
      tbody += '<td class="' + (up ? 'p-up' : dn ? 'p-dn' : 'p-fl') + '">' + M.currencySymbol + s.price.toFixed(dec) + '</td>';
      tbody += '<td><span class="bdg ' + (up ? 'b-up' : dn ? 'b-dn' : 'b-fl') + '">' + sign + s.changePct.toFixed(2) + '%</span></td>';
      tbody += '<td class="' + (up ? 'c-up' : dn ? 'c-dn' : 'c-flat') + '">' + sign + s.change.toFixed(dec) + '</td>';
      tbody += '<td style="color:#888">' + s.open.toFixed(dec) + '</td>';
      tbody += '<td class="c-up">' + s.high.toFixed(dec) + '</td>';
      tbody += '<td class="c-dn">' + s.low.toFixed(dec) + '</td>';
      tbody += '<td style="color:#888">' + (s.volume/100).toLocaleString() + '</td>';
      if (isFut) {
        tbody += '<td style="color:#888">' + (s.openInterest/1000).toFixed(0) + 'K</td>';
      } else {
        tbody += '<td style="color:#888">' + s.turnoverRate.toFixed(2) + '</td>';
        tbody += '<td style="color:#888">' + s.marketCap.toFixed(2) + '</td>';
        tbody += '<td style="color:#888">' + s.pe.toFixed(1) + '</td>';
      }
      tbody += '<td><span class="sec-tag">' + s.sector + '</span></td>';
      tbody += '<td>' + self.sigBadges(s.sigs || {}) + '</td>';
      tbody += '<td>' + self.spark(s.intraday || [], up) + '</td>';
      tbody += '</tr>';
    });
    tbody += '</tbody>';
    
    area.innerHTML = '<table class="stk-tbl">' + thead + tbody + '</table>';
  },
  
  sigBadges(sigs) {
    const SBM = {
      ma_golden:{l:'MA+',t:'bull'}, ma_death:{l:'MA-',t:'bear'},
      ma_bull_arr:{l:'Bull',t:'bull'}, ma_bear_arr:{l:'Bear',t:'bear'},
      boll_lower:{l:'BOLL-',t:'bull'}, boll_upper:{l:'BOLL+',t:'bear'},
      boll_squeeze:{l:'Squeeze',t:'blue'},
      macd_golden:{l:'MACD+',t:'bull'}, macd_death:{l:'MACD-',t:'bear'},
      rsi_oversold:{l:'RSI<30',t:'bull'}, rsi_overbought:{l:'RSI>70',t:'bear'},
      kdj_golden:{l:'KDJ+',t:'bull'}, kdj_death:{l:'KDJ-',t:'bear'},
      obv_up:{l:'OBV+',t:'bull'}, obv_dn:{l:'OBV-',t:'bear'}
    };
    const o = [];
    for (const k in sigs) {
      if (!sigs[k] || !SBM[k]) continue;
      o.push('<span class="sb2 sb2-' + SBM[k].t + '">' + SBM[k].l + '</span>');
      if (o.length >= 4) break;
    }
    return '<div class="sig-w">' + o.join('') + '</div>';
  },
  
  spark(p, up) {
    const w = 60, h = 22, pts = p.slice(-40);
    if (pts.length < 2) return '';
    let mn = Infinity, mx = -Infinity;
    pts.forEach(v => { if (v < mn) mn = v; if (v > mx) mx = v; });
    const rng = mx - mn || 1;
    const d = pts.map((v, i) => ((i/(pts.length-1))*w) + ',' + (h-((v-mn)/rng)*h)).join(' ');
    return '<svg width="' + w + '" height="' + h + '"><polyline points="' + d + '" fill="none" stroke="' + (up?'#f43f5e':'#22c55e') + '" stroke-width="1.5" stroke-linejoin="round"/></svg>';
  },
  
  sortBy(f) {
    Filters.state.dir = Filters.state.sort === f ? (Filters.state.dir === 'asc' ? 'desc' : 'asc') : 'desc';
    Filters.state.sort = f;
    Filters.state.page = 1;
    this.renderAll();
  },
  
  renderPagination(total) {
    const tp = Math.ceil(total / Filters.state.pageSize);
    if (tp <= 1) { document.getElementById('pag').innerHTML = ''; return; }
    const cur = Filters.state.page;
    let pages = [];
    if (tp <= 7) { for (let i = 1; i <= tp; i++) pages.push(i); }
    else {
      pages = [1];
      if (cur > 3) pages.push('...');
      for (let i = Math.max(2, cur - 1); i <= Math.min(tp - 1, cur + 1); i++) pages.push(i);
      if (cur < tp - 2) pages.push('...');
      pages.push(tp);
    }
    let html = '<button class="pg" onclick="App.goPage(' + (cur-1) + ')"' + (cur===1?' disabled':'') + '>&lt;</button>';
    pages.forEach(p => {
      if (p === '...') html += '<span style="color:var(--muted);padding:0 3px">...</span>';
      else html += '<button class="pg ' + (p===cur?'cur':'') + '" onclick="App.goPage(' + p + ')">' + p + '</button>';
    });
    html += '<button class="pg" onclick="App.goPage(' + (cur+1) + ')"' + (cur===tp?' disabled':'') + '>&gt;</button>';
    html += '<span class="pg-inf">' + cur + '/' + tp + '</span>';
    document.getElementById('pag').innerHTML = html;
  },
  
  goPage(p) {
    const tp = Math.ceil(Filters.state.filtered.length / Filters.state.pageSize);
    if (p < 1 || p > tp) return;
    Filters.state.page = p;
    this.renderAll();
    document.getElementById('tblArea').scrollTop = 0;
  },
  
  async openModal(code) {
    const local = this.state.symbols.find(s => s.code === code);
    if (!local) return;
    
    try {
      const res = await fetch('/api/market/' + this.state.currentMarketKey + '/symbol/' + code);
      this.state.currentSymbol = await res.json();
    } catch (e) {
      this.state.currentSymbol = local;
    }
    
    Charts.state.symbol = this.state.currentSymbol;
    Charts.state.market = this.state.currentMarket;
    
    this.refreshModalHeader();
    
    document.getElementById('overlay').classList.add('on');
    const self = this;
    setTimeout(() => {
      Charts.buildToolbar();
      self.initResize();
      Charts.drawAll();
    }, 60);
  },
  
  refreshModalHeader() {
    const s = this.state.currentSymbol;
    const M = this.state.currentMarket;
    const up = s.changePct >= 0, cl = up ? 'c-up' : 'c-dn', sign = up ? '+' : '';
    const dec = M.decimals;
    const isFut = M.key === 'US_FUT' || M.key === 'CN_FUT';
    
    document.getElementById('m-ttl').textContent = s.name + ' (' + s.exchange + ':' + s.code + (isFut && s.month ? ' - ' + s.month : '') + ')';
    document.getElementById('m-sub').textContent = '[' + M.name + '] ' + s.sector + ' - Prev ' + M.currencySymbol + s.prevClose.toFixed(dec) + ' - Open ' + M.currencySymbol + s.open.toFixed(dec) + ' - Range ' + s.amplitude.toFixed(2) + '% ' + (s.isSimulated ? '- SIMULATED' : '- LIVE');
    
    let hero = '<div style="display:flex;align-items:flex-end;gap:7px">';
    hero += '<div class="ph-price ' + cl + '">' + M.currencySymbol + s.price.toFixed(dec) + '</div>';
    hero += '<div class="ph-chg ' + cl + '">' + sign + s.change.toFixed(dec) + ' (' + sign + s.changePct.toFixed(2) + '%)</div>';
    hero += '<div class="ph-prev">Prev ' + M.currencySymbol + s.prevClose.toFixed(dec) + '</div>';
    hero += '</div><div class="ph-stats">';
    hero += '<div><div class="phs-l">High</div><div class="phs-v c-up">' + M.currencySymbol + s.high.toFixed(dec) + '</div></div>';
    hero += '<div><div class="phs-l">Low</div><div class="phs-v c-dn">' + M.currencySymbol + s.low.toFixed(dec) + '</div></div>';
    hero += '<div><div class="phs-l">Volume</div><div class="phs-v">' + (s.volume/1e6).toFixed(2) + 'M</div></div>';
    if (isFut) {
      hero += '<div><div class="phs-l">Open Int</div><div class="phs-v">' + (s.openInterest/1000).toFixed(0) + 'K</div></div>';
    } else {
      hero += '<div><div class="phs-l">Turn%</div><div class="phs-v">' + s.turnoverRate.toFixed(2) + '%</div></div>';
      hero += '<div><div class="phs-l">MktCap</div><div class="phs-v">' + s.marketCap.toFixed(2) + '</div></div>';
      hero += '<div><div class="phs-l">PE</div><div class="phs-v">' + s.pe.toFixed(1) + '</div></div>';
    }
    hero += '</div>';
    document.getElementById('m-hero').innerHTML = hero;
    
    const sg = s.sigs || {};
    const vl = sg._vals || {};
    const fmt = (v, d) => v == null ? '--' : v.toFixed(d || 2);
    const ISC = [
      { n:'MA', sig: sg.ma_golden?'Golden+':sg.ma_death?'Death-':sg.ma_bull_arr?'Bull+':sg.ma_bear_arr?'Bear-':'Neutral', cls: sg.ma_golden||sg.ma_bull_arr?'bull':sg.ma_death||sg.ma_bear_arr?'bear':'neu', val: 'MA5:' + fmt(vl.m5, dec) + ' MA20:' + fmt(vl.m20, dec) },
      { n:'BOLL', sig: sg.boll_lower?'Oversold':sg.boll_upper?'Overbought':sg.boll_squeeze?'Squeeze':sg.boll_abmid?'Above Mid':'Below Mid', cls: sg.boll_lower?'bull':sg.boll_upper?'bear':'neu', val:'U:' + fmt(vl.bu, dec) },
      { n:'MACD', sig: sg.macd_golden?'Golden':sg.macd_death?'Death':sg.macd_above_zero?'>0':'<0', cls: sg.macd_golden||sg.macd_above_zero?'bull':'bear', val:'DIF:' + fmt(vl.dif, 3) },
      { n:'RSI', sig: sg.rsi_oversold?'<30':sg.rsi_overbought?'>70':sg.rsi_strong?'Strong+':'Weak-', cls: sg.rsi_oversold||sg.rsi_strong?'bull':sg.rsi_overbought?'bear':'neu', val: fmt(vl.rsiV, 1) },
      { n:'KDJ', sig: sg.kdj_golden?'Golden+':sg.kdj_death?'Death-':sg.kdj_oversold?'Oversold':sg.kdj_overbought?'Overbought':'Neutral', cls: sg.kdj_golden||sg.kdj_oversold?'bull':sg.kdj_death||sg.kdj_overbought?'bear':'neu', val:'K:' + fmt(vl.kv, 1) + ' D:' + fmt(vl.dv, 1) },
      { n:'OBV', sig: sg.obv_bull_div?'Bull Div':sg.obv_bear_div?'Bear Div':sg.obv_up?'Vol+':'Vol-', cls: sg.obv_up||sg.obv_bull_div?'bull':'bear', val:'Vol-Price' }
    ];
    let indHtml = '';
    ISC.forEach(d => {
      indHtml += '<div class="isc ' + d.cls + '"><div class="isc-name">' + d.n + '</div>';
      indHtml += '<div class="isc-sig ' + (d.cls==='bull'?'c-up':d.cls==='bear'?'c-dn':'c-flat') + '">' + d.sig + '</div>';
      indHtml += '<div class="isc-val">' + d.val + '</div></div>';
    });
    document.getElementById('m-ind').innerHTML = indHtml;
  },
  
  initResize() {
    const wrap = document.getElementById('panelsWrap');
    const p1 = document.getElementById('panel1');
    const p2 = document.getElementById('panel2');
    const p3 = document.getElementById('panel3');
    const rh1 = document.getElementById('rh1');
    const rh2 = document.getElementById('rh2');
    let dragging = null, startY = 0, sh1, sh2, sh3;
    const getTotal = () => wrap.clientHeight - rh1.clientHeight - rh2.clientHeight;
    const onDown = (e, which) => {
      dragging = which; startY = e.clientY;
      sh1 = p1.clientHeight; sh2 = p2.clientHeight; sh3 = p3.clientHeight;
      document.body.style.userSelect = 'none';
      e.preventDefault();
    };
    const onMove = (e) => {
      if (!dragging) return;
      const dy = e.clientY - startY, total = getTotal();
      if (dragging === 1) {
        const nh1 = Math.max(60, Math.min(sh1 + dy, total - sh3 - 50));
        const nh2 = total - nh1 - sh3; if (nh2 < 40) return;
        p1.style.flex = '0 0 ' + nh1 + 'px'; p2.style.flex = '0 0 ' + nh2 + 'px';
      } else {
        const nh2 = Math.max(40, Math.min(sh2 + dy, total - sh1 - 40));
        const nh3 = total - sh1 - nh2; if (nh3 < 40) return;
        p2.style.flex = '0 0 ' + nh2 + 'px'; p3.style.flex = '0 0 ' + nh3 + 'px';
      }
      Object.values(Charts.state.charts).forEach(c => { if (c) try { c.resize(); } catch (e) {} });
    };
    const onUp = () => { dragging = null; document.body.style.userSelect = ''; };
    rh1.onmousedown = e => onDown(e, 1);
    rh2.onmousedown = e => onDown(e, 2);
    document.onmousemove = onMove;
    document.onmouseup = onUp;
  },
  
  tickClock() {
    const M = this.state.currentMarket;
    if (!M) return;
    const n = new Date();
    const cur = n.getHours() * 60 + n.getMinutes();
    let open = false;
    M.tradingHours.forEach(h => {
      if (cur >= h[0] * 60 + h[1] && cur <= h[2] * 60 + h[3]) open = true;
    });
    document.getElementById('clock').textContent = n.toLocaleTimeString('en-US', { hour12: false });
    const labels = {
      CN_STOCK: open ? 'Trading' : 'Closed - Sim',
      US_STOCK: open ? 'Market Open' : 'Closed',
      US_FUT: 'Trading 23h',
      CN_FUT: open ? 'Trading' : 'Closed - Sim'
    };
    document.getElementById('mktTxt').textContent = labels[M.key] || '';
  }
};

function closeModal() {
  document.getElementById('overlay').classList.remove('on');
  Object.values(Charts.state.charts).forEach(c => { if (c) try { c.destroy(); } catch (e) {} });
  Charts.state.charts = { c1: null, c2: null, c3: null, cVP: null };
  App.state.currentSymbol = null;
}

document.addEventListener('DOMContentLoaded', () => App.init());
