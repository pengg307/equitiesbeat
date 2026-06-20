const SIG_LABELS = {
  ma_golden:'MA Golden Cross', ma_death:'MA Death Cross',
  ma_bull_arr:'Bull Arrangement', ma_bear_arr:'Bear Arrangement',
  ma_above:'Price>MAs', ma_below:'Price<MAs',
  boll_upper:'BOLL Upper', boll_lower:'BOLL Lower',
  boll_abmid:'Above MidBand', boll_blmid:'Below MidBand',
  boll_squeeze:'BOLL Squeeze', boll_expand:'BOLL Expand',
  macd_golden:'MACD Golden', macd_death:'MACD Death',
  macd_red_grow:'MACD Red+', macd_grn_grow:'MACD Green+',
  macd_above_zero:'MACD>0', macd_below_zero:'MACD<0',
  rsi_oversold:'RSI Oversold', rsi_overbought:'RSI Overbought',
  rsi_strong:'RSI Strong', rsi_weak:'RSI Weak', rsi_cross50:'RSI Cross50',
  kdj_golden:'KDJ Golden', kdj_death:'KDJ Death',
  kdj_oversold:'KDJ Oversold', kdj_overbought:'KDJ Overbought',
  kdj_kabove:'K>D', kdj_kbelow:'K<D',
  obv_up:'OBV Up', obv_dn:'OBV Down',
  obv_bull_div:'OBV Bull Div', obv_bear_div:'OBV Bear Div'
};

const Filters = {
  state: {
    search: '', exch: '', sector: '', chg: '', quick: 'all',
    sort: 'changePct', dir: 'desc', page: 1, pageSize: 20,
    chips: new Set(), logic: 'AND', filtered: []
  },
  
  renderIndicatorAccordions() {
    const cfg = [
      { id:'ma', name:'MA', dot:'#f43f5e', sub:'5/10/20/60/200',
        chips:[
          ['ma_golden','MA5x10 Golden','s-bull'],['ma_death','MA5x10 Death','s-bear'],
          ['ma_bull_arr','Bull Arr','s-bull'],['ma_bear_arr','Bear Arr','s-bear'],
          ['ma_above','Price>3MA','s-bull'],['ma_below','Price<3MA','s-bear']
        ]},
      { id:'boll', name:'BOLL', dot:'#3b82f6', sub:'20 2sigma',
        chips:[
          ['boll_upper','Upper Band','s-bear'],['boll_lower','Lower Band','s-bull'],
          ['boll_abmid','Above Mid','s-bull'],['boll_blmid','Below Mid','s-bear'],
          ['boll_squeeze','Squeeze','s-blue'],['boll_expand','Expand','s-neu']
        ]},
      { id:'macd', name:'MACD', dot:'#a78bfa', sub:'EMA(12,26,9)',
        chips:[
          ['macd_golden','Golden','s-bull'],['macd_death','Death','s-bear'],
          ['macd_red_grow','Red+','s-bull'],['macd_grn_grow','Green+','s-bear'],
          ['macd_above_zero','>0','s-bull'],['macd_below_zero','<0','s-bear']
        ]},
      { id:'rsi', name:'RSI', dot:'#f59e0b', sub:'14-day',
        chips:[
          ['rsi_oversold','<30','s-bull'],['rsi_overbought','>70','s-bear'],
          ['rsi_strong','Strong 50-70','s-bull'],['rsi_weak','Weak 30-50','s-bear'],
          ['rsi_cross50','Cross 50','s-blue']
        ]},
      { id:'kdj', name:'KDJ', dot:'#14b8a6', sub:'9-day',
        chips:[
          ['kdj_golden','Golden','s-bull'],['kdj_death','Death','s-bear'],
          ['kdj_oversold','K<20','s-bull'],['kdj_overbought','K>80','s-bear'],
          ['kdj_kabove','K>D','s-bull'],['kdj_kbelow','K<D','s-bear']
        ]},
      { id:'obv', name:'OBV', dot:'#f97316', sub:'Vol-Price',
        chips:[
          ['obv_up','Up','s-bull'],['obv_dn','Down','s-bear'],
          ['obv_bull_div','Bull Div','s-bull'],['obv_bear_div','Bear Div','s-bear']
        ]}
    ];
    let html = '';
    cfg.forEach((c, i) => {
      html += '<div class="ind-acc">';
      html += '<div class="acc-hd" onclick="Filters.toggleAcc(\'' + c.id + '\')">';
      html += '<div class="acc-hd-l">';
      html += '<span class="ind-dot" style="background:' + c.dot + '"></span>';
      html += '<div><div class="acc-name">' + c.name + '</div><div class="acc-sub">' + c.sub + '</div></div>';
      html += '</div>';
      html += '<span class="acc-ico' + (i === 0 ? ' open' : '') + '" id="ico_' + c.id + '">v</span>';
      html += '</div>';
      html += '<div class="acc-body' + (i === 0 ? ' open' : '') + '" id="body_' + c.id + '">';
      html += '<div class="chip-row">';
      c.chips.forEach(ch => {
        html += '<button class="chip" data-sig="' + ch[0] + '" data-cls="' + ch[2] + '" onclick="Filters.toggleChip(this)">' + ch[1] + '</button>';
      });
      html += '</div></div></div>';
    });
    document.getElementById('indicatorAccordions').innerHTML = html;
  },
  
  toggleAcc(id) {
    const b = document.getElementById('body_' + id);
    const i = document.getElementById('ico_' + id);
    const o = b.classList.toggle('open');
    i.classList.toggle('open', o);
  },
  
  toggleChip(el) {
    const sig = el.dataset.sig, cls = el.dataset.cls;
    if (this.state.chips.has(sig)) {
      this.state.chips.delete(sig);
      el.className = 'chip';
    } else {
      this.state.chips.add(sig);
      el.className = 'chip ' + cls;
    }
    this.updateBadge();
  },
  
  updateBadge() {
    const n = this.state.chips.size;
    const b = document.getElementById('filterBadge');
    b.textContent = n;
    b.style.display = n ? '' : 'none';
    document.getElementById('applyBtn').textContent = n ? 'Apply (' + n + ')' : 'Apply Filters';
  },
  
  setQuick(q) {
    this.state.quick = q;
    this.state.page = 1;
    document.querySelectorAll('#quickPills .pill').forEach(p => p.classList.toggle('on', p.dataset.quick === q));
    App.applyFilters();
  },
  
  setChg(v) {
    this.state.chg = v;
    this.state.page = 1;
    document.querySelectorAll('#chgPills .pill').forEach(p => p.classList.toggle('on', p.dataset.chg === v));
    App.applyFilters();
  },
  
  apply(symbols, market) {
    const s = this.state;
    const q = s.search.toLowerCase();
    let list = symbols.slice();
    
    if (q) list = list.filter(x => x.name.toLowerCase().indexOf(q) >= 0 || x.code.toLowerCase().indexOf(q) >= 0);
    if (s.exch) list = list.filter(x => x.exchange === s.exch);
    if (s.sector) list = list.filter(x => x.sector === s.sector);
    
    if (s.quick !== 'all') {
      const mapFn = QuickKeyMap[market.key] || function() { return {}; };
      list = list.filter(x => mapFn(x)[s.quick]);
    }
    
    switch (s.chg) {
      case 'up5': list = list.filter(x => x.changePct >= 5); break;
      case 'up3': list = list.filter(x => x.changePct >= 3); break;
      case 'up':  list = list.filter(x => x.changePct > 0); break;
      case 'dn':  list = list.filter(x => x.changePct < 0); break;
      case 'dn3': list = list.filter(x => x.changePct <= -3); break;
      case 'lup': list = list.filter(x => x.changePct >= market.limitUp); break;
      case 'ldn': list = list.filter(x => x.changePct <= market.limitDn); break;
    }
    
    if (s.chips.size > 0) {
      const chipArr = Array.from(s.chips);
      if (s.logic === 'AND') {
        list = list.filter(x => chipArr.every(sig => x.sigs && x.sigs[sig] === true));
      } else {
        list = list.filter(x => chipArr.some(sig => x.sigs && x.sigs[sig] === true));
      }
    }
    
    list.sort((a, b) => {
      const av = a[s.sort], bv = b[s.sort];
      if (typeof av === 'string') return s.dir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
      return s.dir === 'asc' ? av - bv : bv - av;
    });
    
    s.filtered = list;
    return list;
  }
};

const QuickKeyMap = {
  CN_STOCK: s => ({ sh50: s.sh50, csi300: s.csi, gem: s.gem }),
  US_STOCK: s => ({ sp500: s.sp500, dow: s.dow, nasdaq100: s.nasdaq100 }),
  US_FUT:   s => ({ index:s.group==='index', energy:s.group==='energy', metals:s.group==='metals', ags:s.group==='ags', fx:s.group==='fx', rates:s.group==='rates' }),
  CN_FUT:   s => ({ index:s.group==='index', rates:s.group==='rates', metals:s.group==='metals', energy:s.group==='energy', chems:s.group==='chems', ags:s.group==='ags' })
};

function setLogic(l) {
  Filters.state.logic = l;
  document.getElementById('optAND').className = 'logic-opt' + (l === 'AND' ? ' active-and' : '');
  document.getElementById('optOR').className = 'logic-opt' + (l === 'OR' ? ' active-or' : '');
  App.applyFilters();
}

function applyFilters() { App.applyFilters(); }

function resetAll() {
  Object.assign(Filters.state, {
    search: '', exch: '', sector: '', chg: '', quick: 'all', chips: new Set(), logic: 'AND'
  });
  document.getElementById('searchInp').value = '';
  document.getElementById('exchSel').value = '';
  document.getElementById('sectorSel').value = '';
  document.querySelectorAll('.chip').forEach(c => c.className = 'chip');
  Filters.setQuick('all');
  Filters.setChg('');
  document.getElementById('optAND').className = 'logic-opt active-and';
  document.getElementById('optOR').className = 'logic-opt';
  Filters.updateBadge();
  App.applyFilters();
}
