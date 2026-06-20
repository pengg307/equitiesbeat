const ChartUtil = {
  sma(a, n) {
    const o = [];
    for (let i = 0; i < a.length; i++) {
      if (i < n - 1) { o.push(null); continue; }
      let sum = 0;
      for (let j = i - n + 1; j <= i; j++) sum += a[j];
      o.push(sum / n);
    }
    return o;
  },
  ema(arr, n) {
    const k = 2 / (n + 1);
    let p = null, c = 0;
    const o = [];
    for (let i = 0; i < arr.length; i++) {
      if (arr[i] === null) { o.push(null); continue; }
      if (p === null) {
        if (c < n - 1) { c++; o.push(null); continue; }
        let sum = 0, cnt = 0;
        for (let j = i - n + 1; j <= i; j++) {
          if (arr[j] !== null) { sum += arr[j]; cnt++; }
        }
        p = sum / cnt;
      } else p = arr[i] * k + p * (1 - k);
      o.push(+p.toFixed(4));
    }
    return o;
  },
  calcBOLL(cls, n, m) {
    n = n || 20; m = m || 2;
    const mid = this.sma(cls, n);
    const u = [], l = [];
    for (let i = 0; i < cls.length; i++) {
      if (mid[i] === null) { u.push(null); l.push(null); continue; }
      let sum = 0;
      for (let j = i - n + 1; j <= i; j++) {
        sum += (cls[j] - mid[i]) * (cls[j] - mid[i]);
      }
      const sd = Math.sqrt(sum / n);
      u.push(+(mid[i] + m * sd).toFixed(4));
      l.push(+(mid[i] - m * sd).toFixed(4));
    }
    return { upper: u, mid: mid, lower: l };
  },
  calcMACD(cls) {
    const e12 = this.ema(cls, 12), e26 = this.ema(cls, 26);
    const dif = e12.map((v, i) => v === null || e26[i] === null ? null : v - e26[i]);
    const dea = this.ema(dif, 9);
    const bar = dif.map((v, i) => v === null || dea[i] === null ? null : +(2 * (v - dea[i])).toFixed(4));
    return { dif: dif, dea: dea, bar: bar };
  },
  calcRSI(cls, n) {
    n = n || 14;
    const o = []; let ag = 0, al = 0;
    for (let i = 0; i < cls.length; i++) {
      if (i === 0) { o.push(null); continue; }
      const d = cls[i] - cls[i-1], g = d > 0 ? d : 0, l = d < 0 ? -d : 0;
      if (i <= n) { ag += g/n; al += l/n; if (i < n) { o.push(null); continue; } }
      else { ag = (ag*(n-1)+g)/n; al = (al*(n-1)+l)/n; }
      o.push(+(100 - 100/(1 + (al === 0 ? 100 : ag/al))).toFixed(2));
    }
    return o;
  },
  calcKDJ(hi, lo, cls, n) {
    n = n || 9;
    const K = [], D = [], J = []; let pk = 50, pd = 50;
    for (let i = 0; i < cls.length; i++) {
      if (i < n - 1) { K.push(null); D.push(null); J.push(null); continue; }
      let hh = -Infinity, ll = Infinity;
      for (let j = i - n + 1; j <= i; j++) {
        if (hi[j] > hh) hh = hi[j];
        if (lo[j] < ll) ll = lo[j];
      }
      const rsv = hh === ll ? 50 : (cls[i] - ll) / (hh - ll) * 100;
      const kk = (2/3)*pk + (1/3)*rsv, dd = (2/3)*pd + (1/3)*kk;
      K.push(+kk.toFixed(2)); D.push(+dd.toFixed(2)); J.push(+(3*kk - 2*dd).toFixed(2));
      pk = kk; pd = dd;
    }
    return { K: K, D: D, J: J };
  }
};

const Charts = {
  state: {
    period: '5d',
    overlays: { ma5: true, ma10: true, ma20: true, ma60: false, ma200: false, boll: false },
    showVP: true,
    p3: new Set(['macd']),
    charts: { c1: null, c2: null, c3: null, cVP: null },
    symbol: null,
    market: null
  },
  
  UP: '#f43f5e', DN: '#22c55e',
  
  buildToolbar() {
    const t = document.getElementById('chartToolbar');
    const self = this;
    let html = '<div class="toolbar-group"><span class="tbar-label">Period:</span><div class="period-btns" id="periodBtns">';
    ['1d','5d','1m','3m','6m','1y'].forEach(p => {
      html += '<button class="period-btn' + (p === self.state.period ? ' on' : '') + '" data-p="' + p + '">' + p + '</button>';
    });
    html += '</div></div><div class="tbar-sep"></div><div class="toolbar-group"><span class="tbar-label">MA:</span>';
    ['ma5','ma10','ma20','ma60','ma200','boll'].forEach(k => {
      html += '<label class="cb-item' + (self.state.overlays[k] ? ' on' : '') + '" data-ov="' + k + '">';
      html += '<input type="checkbox"' + (self.state.overlays[k] ? ' checked' : '') + '> ' + k.toUpperCase() + '</label>';
    });
    html += '</div><div class="tbar-sep"></div><div class="toolbar-group"><span class="tbar-label">VP:</span>';
    html += '<label class="cb-item' + (self.state.showVP ? ' on' : '') + '" id="vpToggle">';
    html += '<input type="checkbox"' + (self.state.showVP ? ' checked' : '') + '> Volume Profile</label>';
    html += '</div><div class="tbar-sep"></div><div class="toolbar-group"><span class="tbar-label">Sub:</span>';
    ['macd','rsi','kdj','obv'].forEach(k => {
      html += '<label class="cb-item' + (self.state.p3.has(k) ? ' on' : '') + '" data-p3="' + k + '">';
      html += '<input type="checkbox"' + (self.state.p3.has(k) ? ' checked' : '') + '> ' + k.toUpperCase() + '</label>';
    });
    html += '</div>';
    t.innerHTML = html;
    
    t.querySelectorAll('#periodBtns .period-btn').forEach(b => {
      b.onclick = () => { 
        t.querySelectorAll('.period-btn').forEach(x => x.classList.remove('on'));
        b.classList.add('on');
        self.state.period = b.dataset.p; 
        self.drawAll(); 
      };
    });
    t.querySelectorAll('[data-ov]').forEach(l => {
      l.onclick = (e) => {
        if (e.target.tagName === 'INPUT') return;
        const cb = l.querySelector('input');
        cb.checked = !cb.checked;
        self.state.overlays[l.dataset.ov] = cb.checked;
        l.classList.toggle('on', cb.checked);
        self.drawAll();
      };
    });
    t.querySelector('#vpToggle').onclick = (e) => {
      if (e.target.tagName === 'INPUT') return;
      const cb = t.querySelector('#vpToggle input');
      cb.checked = !cb.checked;
      self.state.showVP = cb.checked;
      t.querySelector('#vpToggle').classList.toggle('on', cb.checked);
      document.getElementById('vpSidebar').style.display = cb.checked ? '' : 'none';
      self.drawAll();
    };
    t.querySelectorAll('[data-p3]').forEach(l => {
      l.onclick = (e) => {
        if (e.target.tagName === 'INPUT') return;
        const cb = l.querySelector('input');
        cb.checked = !cb.checked;
        if (cb.checked) self.state.p3.add(l.dataset.p3); else self.state.p3.delete(l.dataset.p3);
        l.classList.toggle('on', cb.checked);
        self.drawPanel3();
        self.updateP3Label();
      };
    });
  },
  
  updateP3Label() {
    document.getElementById('p3lbl').textContent = this.state.p3.size ? Array.from(this.state.p3).map(s => s.toUpperCase()).join(' + ') : 'Sub';
  },
  
  getPeriodData() {
    const s = this.state.symbol;
    if (!s.ohlcv) return { data: [], isIntraday: false };
    if (this.state.period === '1d') {
      const ip = s.intraday || [];
      return {
        data: ip.map((c, i) => ({ o: i === 0 ? s.open : ip[i-1], h: c, l: c, c: c, v: Math.floor(Math.random()*30000+500) })),
        isIntraday: true
      };
    }
    const nMap = { '5d':5, '1m':22, '3m':66, '6m':132, '1y':252 };
    return { data: s.ohlcv.slice(-(nMap[this.state.period] || 60)), isIntraday: false };
  },
  
  makeLabels(data, isIntraday) {
    if (isIntraday) {
      return data.map((_, i) => {
        const m = 570 + Math.floor(i * 240 / data.length);
        return i % 30 === 0 ? Math.floor(m/60) + ':' + String(m%60).padStart(2,'0') : '';
      });
    }
    const interval = Math.max(1, Math.floor(data.length / 8));
    return data.map((_, i) => {
      const d = new Date();
      d.setDate(d.getDate() - (data.length - 1 - i));
      return i % interval === 0 ? (d.getMonth()+1) + '/' + d.getDate() : '';
    });
  },
  
  baseOpts(extraY) {
    extraY = extraY || {};
    return {
      responsive: true, maintainAspectRatio: false, animation: { duration: 150 },
      interaction: { intersect: false, mode: 'index' },
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: {
        x: { grid: { color: 'rgba(28,48,80,.35)' }, ticks: { maxTicksLimit: 8, maxRotation: 0, font: { size: 8 }, color: '#4a6a8f' } },
        y: Object.assign({ grid: { color: 'rgba(28,48,80,.35)' }, position: 'right', ticks: { font: { size: 8 }, color: '#4a6a8f', maxTicksLimit: 5 } }, extraY)
      }
    };
  },
  
  destroy(key) {
    if (this.state.charts[key]) {
      try { this.state.charts[key].destroy(); } catch (e) {}
      this.state.charts[key] = null;
    }
  },
  
  drawAll() {
    this.drawPanel1();
    this.drawPanel2();
    this.drawPanel3();
    this.drawVP();
    this.setupCrosshair();
  },
  
  drawPanel1() {
    this.destroy('c1');
    const ctx = document.getElementById('c1').getContext('2d');
    const pd = this.getPeriodData();
    const ohlcv = pd.data, isIntraday = pd.isIntraday;
    if (!ohlcv.length) return;
    const cls = ohlcv.map(d => d.c);
    const labels = this.makeLabels(ohlcv, isIntraday);
    const datasets = [];
    
    if (isIntraday) {
      datasets.push({
        type: 'line', label: 'Price', data: cls,
        borderColor: this.state.symbol.changePct >= 0 ? this.UP : this.DN,
        backgroundColor: this.state.symbol.changePct >= 0 ? 'rgba(244,63,94,.06)' : 'rgba(34,197,94,.06)',
        borderWidth: 1.5, fill: true, tension: 0.3, pointRadius: 0
      });
    } else {
      datasets.push({
        type: 'bar', label: 'K', data: ohlcv.map(d => [d.o, d.c]),
        backgroundColor: ohlcv.map(d => d.c >= d.o ? 'rgba(244,63,94,.82)' : 'rgba(34,197,94,.82)'),
        borderColor: ohlcv.map(d => d.c >= d.o ? this.UP : this.DN),
        borderWidth: 1, borderSkipped: false, barPercentage: .65
      });
      const maConf = [['ma5','#f59e0b',5],['ma10','#a78bfa',10],['ma20','#22c55e',20],['ma60','#f97316',60],['ma200','#14b8a6',200]];
      const self = this;
      maConf.forEach(c => {
        if (!self.state.overlays[c[0]]) return;
        datasets.push({ type:'line', label:c[0].toUpperCase(), data:ChartUtil.sma(cls,c[2]), borderColor:c[1], borderWidth:1.1, pointRadius:0, tension:0.2, fill:false });
      });
      if (this.state.overlays.boll) {
        const b = ChartUtil.calcBOLL(cls);
        datasets.push({ type:'line', label:'BOLL+', data:b.upper, borderColor:'rgba(59,130,246,.6)', borderWidth:1, pointRadius:0, borderDash:[3,3], fill:false });
        datasets.push({ type:'line', label:'BOLL=', data:b.mid, borderColor:'rgba(245,158,11,.6)', borderWidth:1, pointRadius:0, borderDash:[3,3], fill:false });
        datasets.push({ type:'line', label:'BOLL-', data:b.lower, borderColor:'rgba(59,130,246,.6)', borderWidth:1, pointRadius:0, borderDash:[3,3], fill:false });
      }
    }
    
    const opts = this.baseOpts();
    opts.plugins.legend = { display: !isIntraday, position: 'top', align: 'end', labels: { color: '#5a7fa8', boxWidth: 20, boxHeight: 1, font: { size: 8 }, filter: i => i.text !== 'K' } };
    this.state.charts.c1 = new Chart(ctx, { type: 'bar', data: { labels: labels, datasets: datasets }, options: opts });
    document.getElementById('p1lbl').textContent = isIntraday ? 'Intraday' : 'K-Line';
  },
  
  drawPanel2() {
    this.destroy('c2');
    const ctx = document.getElementById('c2').getContext('2d');
    const pd = this.getPeriodData();
    const ohlcv = pd.data, isIntraday = pd.isIntraday;
    if (!ohlcv.length) return;
    const labels = this.makeLabels(ohlcv, isIntraday);
    const opts = this.baseOpts({ ticks: { font:{size:8}, color:'#4a6a8f', maxTicksLimit:3, callback: v => v>=1e6?(v/1e6).toFixed(1)+'M':v>=1e3?(v/1e3).toFixed(0)+'K':v } });
    this.state.charts.c2 = new Chart(ctx, { type:'bar', data:{ labels: labels, datasets:[{ label:'Vol', data:ohlcv.map(d=>d.v),
      backgroundColor: ohlcv.map(d => d.c >= d.o ? 'rgba(244,63,94,.6)' : 'rgba(34,197,94,.6)'),
      borderColor: ohlcv.map(d => d.c >= d.o ? this.UP : this.DN), borderWidth: 0, barPercentage: .8 }] }, options:opts });
  },
  
  drawPanel3() {
    this.destroy('c3');
    if (this.state.p3.size === 0) return;
    const ctx = document.getElementById('c3').getContext('2d');
    const pd = this.getPeriodData();
    const ohlcv = pd.data, isIntraday = pd.isIntraday;
    if (!ohlcv.length) return;
    const cls = ohlcv.map(d => d.c), hi = ohlcv.map(d => d.h), lo = ohlcv.map(d => d.l);
    const labels = this.makeLabels(ohlcv, isIntraday);
    const datasets = [];
    let yMin, yMax;
    
    if (this.state.p3.has('macd')) {
      const m = ChartUtil.calcMACD(cls);
      datasets.push({ type:'line', label:'DIF', data:m.dif, borderColor:'#60a5fa', borderWidth:1.2, pointRadius:0, tension:0.3, fill:false });
      datasets.push({ type:'line', label:'DEA', data:m.dea, borderColor:'#f59e0b', borderWidth:1.2, pointRadius:0, tension:0.3, fill:false });
      datasets.push({ type:'bar', label:'MACD', data:m.bar,
        backgroundColor: m.bar.map(v => v === null ? 'transparent' : v >= 0 ? 'rgba(244,63,94,.65)' : 'rgba(34,197,94,.65)'),
        borderWidth: 0, barPercentage: .8 });
    }
    if (this.state.p3.has('rsi')) {
      const r = ChartUtil.calcRSI(cls);
      datasets.push({ type:'line', label:'RSI', data:r, borderColor:'#f59e0b', borderWidth:1.2, pointRadius:0, tension:0.3, fill:false });
      yMin = 0; yMax = 100;
    }
    if (this.state.p3.has('kdj')) {
      const k = ChartUtil.calcKDJ(hi, lo, cls);
      datasets.push({ type:'line', label:'K', data:k.K, borderColor:'#60a5fa', borderWidth:1.2, pointRadius:0, tension:0.3, fill:false });
      datasets.push({ type:'line', label:'D', data:k.D, borderColor:'#f59e0b', borderWidth:1.2, pointRadius:0, tension:0.3, fill:false });
      datasets.push({ type:'line', label:'J', data:k.J, borderColor:'#f43f5e', borderWidth:1, pointRadius:0, tension:0.3, fill:false });
      if (!this.state.p3.has('rsi')) { yMin = -10; yMax = 110; }
    }
    
    const extraY = yMin !== undefined ? { min: yMin, max: yMax } : {};
    const opts = this.baseOpts(extraY);
    opts.plugins.legend = { display: true, position: 'top', align: 'end', labels: { color:'#5a7fa8', boxWidth:16, boxHeight:1, font:{size:8} } };
    this.state.charts.c3 = new Chart(ctx, { type:'bar', data:{ labels: labels, datasets: datasets }, options:opts });
    this.updateP3Label();
  },
  
  drawVP() {
    this.destroy('cVP');
    const vp = document.getElementById('vpSidebar');
    if (!this.state.showVP) { vp.style.display = 'none'; return; }
    vp.style.display = '';
    const pd = this.getPeriodData();
    const ohlcv = pd.data;
    if (!ohlcv.length) return;
    let minP = Infinity, maxP = -Infinity;
    ohlcv.forEach(d => { if (d.l < minP) minP = d.l; if (d.h > maxP) maxP = d.h; });
    const BINS = 30, binSize = (maxP - minP) / BINS || 1;
    const upVol = new Array(BINS).fill(0), dnVol = new Array(BINS).fill(0);
    ohlcv.forEach(d => {
      const mid = (d.h + d.l) / 2;
      const bin = Math.min(Math.floor((mid - minP) / binSize), BINS - 1);
      if (d.c >= d.o) upVol[bin] += d.v; else dnVol[bin] += d.v;
    });
    const dec = this.state.market.decimals;
    const priceLabels = [];
    for (let i = 0; i < BINS; i++) {
      const p = minP + (i + 0.5) * binSize;
      priceLabels.push(p > 100 ? p.toFixed(0) : p.toFixed(dec));
    }
    const totalVol = upVol.map((u, i) => u + dnVol[i]);
    let maxV = 1;
    totalVol.forEach(v => { if (v > maxV) maxV = v; });
    const pocIdx = totalVol.indexOf(maxV);
    const totalAll = totalVol.reduce((a, b) => a + b, 0);
    const target = totalAll * 0.7;
    let acc = totalVol[pocIdx], vah = pocIdx, val = pocIdx;
    while (acc < target) {
      const u = vah+1 < BINS ? totalVol[vah+1] : 0;
      const d = val-1 >= 0 ? totalVol[val-1] : 0;
      if (u >= d && vah+1 < BINS) { vah++; acc += u; }
      else if (val-1 >= 0) { val--; acc += d; }
      else break;
    }
    this.state.charts.cVP = new Chart(document.getElementById('cVP').getContext('2d'), {
      type: 'bar',
      data: { labels: priceLabels, datasets: [
        { label:'Up', data:upVol, backgroundColor:upVol.map((_,i) => i===pocIdx?'rgba(255,200,0,.9)':(i>=val&&i<=vah)?'rgba(244,63,94,.55)':'rgba(244,63,94,.3)'), borderWidth:0 },
        { label:'Dn', data:dnVol, backgroundColor:dnVol.map((_,i) => i===pocIdx?'rgba(255,200,0,.7)':(i>=val&&i<=vah)?'rgba(34,197,94,.5)':'rgba(34,197,94,.25)'), borderWidth:0 }
      ] },
      options: {
        indexAxis: 'y', responsive: true, maintainAspectRatio: false, animation: { duration: 150 },
        plugins: { legend: { display: false }, tooltip: { enabled: true } },
        scales: {
          x: { display: false, stacked: true },
          y: { display: true, stacked: true, position: 'right',
            ticks: { font:{size:7}, color:'#4a6a8f', maxTicksLimit:8, callback:(v,i)=> i%Math.ceil(BINS/8)===0?priceLabels[i]:null },
            grid: { display: false }, border: { display: false } }
        }
      }
    });
  },
  
  setupCrosshair() {
    const tip = document.getElementById('xhTip');
    const m = this.state.market;
    const self = this;
    ['c1', 'c2', 'c3'].forEach(key => {
      const canvas = document.getElementById(key);
      canvas.onmousemove = (e) => {
        const chart = self.state.charts[key] || self.state.charts.c1;
        if (!chart) return;
        const pts = chart.getElementsAtEventForMode(e, 'index', { intersect: false }, false);
        if (!pts.length) { tip.style.display = 'none'; return; }
        const idx = pts[0].index;
        const pd = self.getPeriodData();
        const d = pd.data[idx]; if (!d) return;
        const chg = d.c - d.o, sign = chg >= 0 ? '+' : '';
        const dec = m.decimals;
        tip.innerHTML = 
          '<div class="ct-title">' + (chart.data.labels[idx] || 'Bar') + '</div>' +
          '<div class="ct-row"><span class="ct-k">Open</span><span class="ct-v">' + d.o.toFixed(dec) + '</span></div>' +
          '<div class="ct-row"><span class="ct-k">High</span><span class="ct-v c-up">' + d.h.toFixed(dec) + '</span></div>' +
          '<div class="ct-row"><span class="ct-k">Low</span><span class="ct-v c-dn">' + d.l.toFixed(dec) + '</span></div>' +
          '<div class="ct-row"><span class="ct-k">Close</span><span class="ct-v ' + (chg>=0?'c-up':'c-dn') + '">' + d.c.toFixed(dec) + '</span></div>' +
          '<div class="ct-row"><span class="ct-k">Chg</span><span class="ct-v ' + (chg>=0?'c-up':'c-dn') + '">' + sign + chg.toFixed(dec) + ' (' + sign + (chg/d.o*100).toFixed(2) + '%)</span></div>' +
          '<div class="ct-row"><span class="ct-k">Vol</span><span class="ct-v">' + (d.v/100).toLocaleString() + '</span></div>';
        tip.style.display = 'block';
        tip.style.left = (e.clientX + 14) + 'px';
        tip.style.top = (e.clientY + 14) + 'px';
        const r = tip.getBoundingClientRect();
        if (r.right > window.innerWidth - 10) tip.style.left = (e.clientX - r.width - 14) + 'px';
      };
      canvas.onmouseleave = () => tip.style.display = 'none';
    });
  }
};
