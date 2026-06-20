const MarketUI = {
  flag(key) {
    const m = { CN_STOCK: 'CN', US_STOCK: 'US', US_FUT: 'US', CN_FUT: 'CN' };
    return m[key] || 'GL';
  },
  
  shortName(key) {
    const m = {
      CN_STOCK: 'CN Stock',
      US_STOCK: 'US Stock',
      US_FUT: 'US Futures',
      CN_FUT: 'CN Futures'
    };
    return m[key] || key;
  },
  
  renderTabs(markets, currentKey, onClick) {
    const tabs = document.getElementById('mktTabs');
    let html = '';
    markets.forEach(m => {
      html += '<button class="mkt-tab' + (m.key === currentKey ? ' on' : '') + '" data-mkt="' + m.key + '">';
      html += '<span class="flag">' + MarketUI.flag(m.key) + '</span>';
      html += '<div><div>' + m.name + '</div><div class="sub">' + MarketUI.shortName(m.key) + '</div></div>';
      html += '<span class="' + (m.useRealData ? 'badge-real' : 'badge-sim') + '">' + (m.useRealData ? 'LIVE' : 'SIM') + '</span>';
      html += '</button>';
    });
    tabs.innerHTML = html;
    tabs.querySelectorAll('.mkt-tab').forEach(t => {
      t.onclick = () => onClick(t.dataset.mkt);
    });
  },
  
  renderIndexBar(indices) {
    let html = '';
    indices.forEach(d => {
      const dec = d.value > 1000 ? 2 : d.value > 10 ? 2 : 4;
      const cls = d.pct > 0 ? 'c-up' : d.pct < 0 ? 'c-dn' : 'c-flat';
      const arrow = d.pct > 0 ? '+' : d.pct < 0 ? '-' : '=';
      html += '<div class="idx-card">';
      html += '<div class="idx-name">' + d.name + '</div>';
      html += '<div class="idx-val">' + d.value.toLocaleString('en-US', {minimumFractionDigits:dec, maximumFractionDigits:dec}) + '</div>';
      html += '<div class="idx-chg ' + cls + '">' + arrow + Math.abs(d.change).toFixed(dec) + ' (' + (d.pct > 0 ? '+' : '') + d.pct.toFixed(2) + '%)</div>';
      html += '</div>';
    });
    document.getElementById('idxBar').innerHTML = html;
  },
  
  buildSidebar(market) {
    const exchSel = document.getElementById('exchSel');
    let html = '';
    market.exchanges.forEach(e => {
      html += '<option value="' + e[0] + '">' + e[1] + '</option>';
    });
    exchSel.innerHTML = html;
    
    const sectorSel = document.getElementById('sectorSel');
    html = '<option value="">All Sectors</option>';
    market.sectors.forEach(s => {
      html += '<option value="' + s + '">' + s + '</option>';
    });
    sectorSel.innerHTML = html;
    
    const pills = document.getElementById('quickPills');
    html = '';
    market.quickFilters.forEach(q => {
      html += '<button class="pill' + (q[0] === 'all' ? ' on' : '') + '" data-quick="' + q[0] + '">' + q[1] + '</button>';
    });
    pills.innerHTML = html;
    pills.querySelectorAll('.pill').forEach(p => {
      p.onclick = () => Filters.setQuick(p.dataset.quick);
    });
    
    const chgPills = document.getElementById('chgPills');
    const chgOpts = [['', 'All'], ['up5', '>5%'], ['up3', '>3%'], ['up', 'Up'], ['dn', 'Down'], ['dn3', '<-3%']];
    if (market.limitUp < 100) {
      chgOpts.push(['lup', 'Limit+']);
      chgOpts.push(['ldn', 'Limit-']);
    }
    html = '';
    chgOpts.forEach(c => {
      html += '<button class="pill' + (c[0] === '' ? ' on' : '') + '" data-chg="' + c[0] + '">' + c[1] + '</button>';
    });
    chgPills.innerHTML = html;
    chgPills.querySelectorAll('.pill').forEach(p => {
      p.onclick = () => Filters.setChg(p.dataset.chg);
    });
    
    document.getElementById('unitTxt').textContent = market.unit;
    document.getElementById('quickLbl').textContent = '(' + market.name + ')';
    
    Filters.renderIndicatorAccordions();
  }
};
