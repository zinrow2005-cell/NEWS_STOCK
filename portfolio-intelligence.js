(()=>{
  'use strict';
  const BUILD='4.7.23.2';
  const NEWS_FAV_KEY='安心股票簿-news-favorites-v1';
  const panelId='portfolioIntelligencePanel';
  const state={payload:null,loading:false,sort:'event',lastRenderKey:''};
  const esc=s=>String(s??'').replace(/[&<>\"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','\"':'&quot;',"'":'&#39;'}[c]));
  const norm=s=>String(s??'').trim().toUpperCase();
  const now=()=>Date.now();
  const parseDate=v=>{const t=new Date(v||0).getTime();return Number.isFinite(t)&&t>0?t:0};
  const fmtDate=v=>{const t=parseDate(v);if(!t)return'—';return new Date(t).toLocaleString('zh-TW',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'})};
  const numberFromText=v=>{const m=String(v??'').replace(/,/g,'').match(/-?\d+(?:\.\d+)?/);return m?Number(m[0]):null};
  const moneyFromText=v=>{const s=String(v??'').replace(/,/g,'').replace(/%/g,'').trim();const m=s.match(/([+-]?)\s*(?:NT\$|TWD|\$)?\s*([+-]?)\s*(\d+(?:\.\d+)?)/i);if(!m)return null;const sign=(m[1]==='-'||m[2]==='-')?-1:1;return sign*Number(m[3]);};
  const fmtMoney=v=>v!==null&&v!==''&&Number.isFinite(Number(v))?`NT$${Math.round(Number(v)).toLocaleString('zh-TW')}`:'—';
  const fmtPrice=v=>v!==null&&v!==''&&Number.isFinite(Number(v))?`$${Number(v).toLocaleString('zh-TW',{minimumFractionDigits:0,maximumFractionDigits:2})}`:'—';
  const fmtPct=v=>v!==null&&v!==''&&Number.isFinite(Number(v))?`${Number(v)>=0?'+':''}${Number(v).toFixed(2)}%`:'—';
  const itemStocks=x=>Array.isArray(x?.matchedStocks)?x.matchedStocks:[];
  const entry=(x,symbol)=>itemStocks(x).find(m=>norm(m?.symbol)===norm(symbol))||null;
  const matched=(x,symbol)=>!!entry(x,symbol);
  const nature=(x,symbol)=>{
    const m=entry(x,symbol)||{};
    if(m.relationNature)return m.relationNature;
    if(m.isCorePrimary||m.primaryTier==='core')return'company_core';
    if(m.isPrimary||m.primaryTier==='general')return'company_general';
    return'';
  };
  const relevance=(x,symbol)=>{const m=entry(x,symbol)||{};return{score:Number(m.relevanceScore||0),level:String(m.relevanceLevel||'')}};
  const importance=x=>Number(x?.eventImportance??x?.importance??0)||0;
  const within=(x,hours)=>{const t=parseDate(x?.publishedAt);return t&&t>=now()-hours*3600000};
  const isCompany=n=>n==='company_core'||n==='company_general';
  function newsFor(symbol,days=7){const cut=now()-days*86400000;return (state.payload?.items||[]).filter(x=>matched(x,symbol)&&parseDate(x.publishedAt)>=cut)}
  function summarize(symbol){
    const week=newsFor(symbol,7),day=week.filter(x=>within(x,24));
    const company=week.filter(x=>isCompany(nature(x,symbol)));
    const core=week.filter(x=>nature(x,symbol)==='company_core');
    const price=week.filter(x=>nature(x,symbol)==='price_action');
    const market=week.filter(x=>nature(x,symbol)==='market_theme');
    const major=week.filter(x=>importance(x)>=70);
    const freshCompany=day.filter(x=>isCompany(nature(x,symbol))||importance(x)>=70);
    const latest=[...week].sort((a,b)=>parseDate(b.publishedAt)-parseDate(a.publishedAt))[0]||null;
    const latestMajor=[...week].filter(x=>importance(x)>=70||isCompany(nature(x,symbol))).sort((a,b)=>importance(b)-importance(a)||parseDate(b.publishedAt)-parseDate(a.publishedAt))[0]||null;
    const activity=Math.min(100,week.length*3+company.length*8+major.length*6+day.length*4);
    return{week,day,company,core,price,market,major,freshCompany,latest,latestMajor,activity};
  }
  function parseHoldings(){
    return [...document.querySelectorAll('.holding-card')].map(card=>{
      const symbol=norm(card.querySelector('.stock-code')?.textContent);
      const stockName=String(card.querySelector('.stock-name')?.textContent||symbol).trim();
      const total=card.querySelector('.holding-total');
      const rawUnits=numberFromText(total?.querySelector('b')?.textContent)||0;
      const totalText=String(total?.textContent||'');
      // 主系統持股摘要以「張」顯示整張庫存，例如 6 張 = 6,000 股。
      // 若是零股則可能直接以「股」顯示。情報卡內部一律換算成實際股數計算市值。
      const unitKind=/張/.test(totalText)?'lot':'share';
      const units=unitKind==='lot'?rawUnits*1000:rawUnits;
      const displayUnits=unitKind==='lot'?`${rawUnits.toLocaleString('zh-TW',{maximumFractionDigits:3})} 張（${units.toLocaleString('zh-TW')} 股）`:`${units.toLocaleString('zh-TW')} 股`;
      const smalls=[...(total?.querySelectorAll('small')||[])].map(x=>x.textContent.trim());
      const spans=[...(total?.querySelectorAll('span')||[])];
      const costText=String(spans[0]?.textContent||'').trim();
      const unrealizedText=String(spans[1]?.textContent||'').trim();
      const cost=moneyFromText(costText);
      const closeText=smalls.find(x=>x.includes('最近收盤'))||'';
      const closePrice=numberFromText(closeText.replace(/最近收盤/g,''));
      const domUnrealized=moneyFromText(unrealizedText);
      // v4.7.23.2：市值不再用畫面上的損益文字反推，避免 -$150,515 這類格式的負號解析風險。
      // 正常情況：目前市值 = 最新收盤價 × 實際股數；未實現損益 = 目前市值 - 持有成本。
      // 只有行情或股數缺失時，才使用主系統 DOM 已計算的未實現損益作為備援。
      const quoteMarketValue=Number.isFinite(closePrice)&&closePrice>=0&&units>0?closePrice*units:null;
      const marketValue=Number.isFinite(quoteMarketValue)?quoteMarketValue:(Number.isFinite(cost)&&Number.isFinite(domUnrealized)?cost+domUnrealized:null);
      const unrealized=Number.isFinite(marketValue)&&Number.isFinite(cost)?marketValue-cost:(Number.isFinite(domUnrealized)?domUnrealized:null);
      const returnRate=Number.isFinite(unrealized)&&Number.isFinite(cost)&&cost>0?unrealized/cost*100:null;
      return{symbol,stockName,units,rawUnits,unitKind,displayUnits,cost,costText,closePrice,closeText,marketValue,unrealized,unrealizedText,returnRate,card};
    }).filter(x=>x.symbol);
  }
  function favorites(){try{const x=JSON.parse(localStorage.getItem(NEWS_FAV_KEY)||'[]');return Array.isArray(x)?x.map(y=>({symbol:norm(y.symbol),stockName:String(y.stockName||y.name||y.symbol||'').trim()})).filter(y=>y.symbol):[]}catch{return[]}}
  function rankRow(row){
    const s=row.news;
    if(state.sort==='profit')return Number.isFinite(row.unrealized)?row.unrealized:-Infinity;
    if(state.sort==='activity')return s.activity;
    const eventTs=parseDate(s.latestMajor?.publishedAt||s.latest?.publishedAt);
    const urgent=(s.freshCompany.length?1:0)*1e15 + importance(s.latestMajor)*1e12;
    return urgent+eventTs;
  }
  function cardHtml(row,watch=false){
    const s=row.news,badge=s.freshCompany.length?'<span class="pi-alert">有新事件</span>':'', latest=s.latestMajor||s.latest;
    const natureText=latest?({company_core:'核心公司事件',company_general:'公司事件',price_action:'股價行情',market_theme:'市場／產業題材'}[nature(latest,row.symbol)]||'相關新聞'):'近 7 日無新聞';
    const activityLabel=s.activity>=60?'高':s.activity>=25?'中':'低';
    const pnlClass=Number(row.unrealized)<0?'neg':Number(row.unrealized)>0?'pos':'';
    const marketMetrics=watch?'':`<div class="pi-value-grid">
        <span><small>持有成本</small><b>${fmtMoney(row.cost)}</b></span>
        <span><small>目前市值</small><b>${fmtMoney(row.marketValue)}</b></span>
        <span><small>未實現損益</small><b class="${pnlClass}">${fmtMoney(row.unrealized)}</b></span>
        <span><small>庫存報酬率</small><b class="${pnlClass}">${fmtPct(row.returnRate)}</b></span>
      </div>
      <div class="pi-close-line"><span>${esc(row.closeText||'最近收盤價待同步')}</span><span>持有 ${esc(row.displayUnits||`${Number(row.units||0).toLocaleString('zh-TW')} 股`)}</span></div>`;
    return `<article class="pi-stock-card ${s.freshCompany.length?'has-event':''}">
      <div class="pi-stock-top"><div><b>${esc(row.symbol)} ${esc(row.stockName)}</b>${badge}</div><span class="pi-activity">新聞活躍度：${activityLabel}</span></div>
      ${marketMetrics}
      <div class="pi-kpis"><span><small>近 7 日</small><b>${s.week.length}</b></span><span><small>公司事件</small><b>${s.company.length}</b></span><span><small>核心</small><b>${s.core.length}</b></span><span><small>重大</small><b>${s.major.length}</b></span></div>
      <div class="pi-event"><small>${latest?`${natureText} · ${fmtDate(latest.publishedAt)} · 重要性 ${importance(latest)}`:'近 7 日'}</small><p>${latest?esc(latest.title):'目前沒有可顯示的個股新聞事件。'}</p></div>
      <button class="pi-news-btn" type="button" data-pi-news="${esc(row.symbol)}">查看新聞情報 →</button>
    </article>`;
  }
  function panelHtml(rows,watchRows){
    const totalNews=rows.reduce((n,x)=>n+x.news.week.length,0), fresh=rows.filter(x=>x.news.freshCompany.length).length, major=rows.reduce((n,x)=>n+x.news.major.length,0), updated=state.payload?.generatedAt?fmtDate(state.payload.generatedAt):'尚未載入';
    return `<section id="${panelId}" class="portfolio-intelligence" data-build="${BUILD}">
      <div class="pi-head"><div><span class="pi-kicker">PORTFOLIO INTELLIGENCE</span><h2>我的持股情報中心</h2><p>把持股行情、損益與近 7 日新聞事件放在同一頁；「研究優先」只代表資訊閱讀順序，不是買賣建議。</p></div><div class="pi-updated"><small>新聞資料</small><b>${esc(updated)}</b></div></div>
      <div class="pi-summary"><span><small>目前持股</small><b>${rows.length}</b></span><span><small>24h 有新事件</small><b>${fresh}</b></span><span><small>近 7 日新聞</small><b>${totalNews}</b></span><span><small>重大事件</small><b>${major}</b></span></div>
      <div class="pi-toolbar"><b>持股情報</b><div><button data-pi-sort="event" class="${state.sort==='event'?'active':''}">最新事件</button><button data-pi-sort="activity" class="${state.sort==='activity'?'active':''}">新聞活躍度</button><button data-pi-sort="profit" class="${state.sort==='profit'?'active':''}">未實現損益</button></div></div>
      <div class="pi-grid">${rows.length?rows.map(x=>cardHtml(x)).join(''):'<div class="pi-empty">目前沒有持股資料。</div>'}</div>
      ${watchRows.length?`<details class="pi-watch"><summary>⭐ 觀察中（收藏但未持有） <b>${watchRows.length}</b></summary><div class="pi-grid watch">${watchRows.map(x=>cardHtml(x,true)).join('')}</div></details>`:''}
    </section>`;
  }
  async function fetchNews(){
    if(state.payload||state.loading)return;state.loading=true;
    const ctl=new AbortController(),tm=setTimeout(()=>ctl.abort(),8000);
    try{const r=await fetch(`./stock-news.json?t=${Date.now()}`,{cache:'no-store',signal:ctl.signal});if(!r.ok)throw Error(String(r.status));const p=await r.json();state.payload=p&&Array.isArray(p.items)?p:{items:[]}}
    catch{state.payload={items:[],generatedAt:null}}
    finally{clearTimeout(tm);state.loading=false}
  }
  function bind(panel){
    panel.querySelectorAll('[data-pi-sort]').forEach(b=>b.onclick=()=>{state.sort=b.dataset.piSort||'event';render(true)});
    panel.querySelectorAll('[data-pi-news]').forEach(b=>b.onclick=()=>{const symbol=b.dataset.piNews;if(window.StockNewsCenter?.openStock)window.StockNewsCenter.openStock(symbol,'overview');else{try{const pref=JSON.parse(localStorage.getItem('安心股票簿-news-filter-v6')||'{}');pref.selectedStock=symbol;pref.view='overview';localStorage.setItem('安心股票簿-news-filter-v6',JSON.stringify(pref))}catch{}document.querySelector('.news-launcher')?.click()}});
  }
  async function render(force=false){
    const anchor=document.querySelector('.market-sync-strip');
    const cards=document.querySelector('.holding-cards');
    if(!anchor||!cards){document.getElementById(panelId)?.remove();return}
    await fetchNews();
    const holdings=parseHoldings(),held=new Set(holdings.map(x=>x.symbol));
    let rows=holdings.map(x=>({...x,news:summarize(x.symbol)}));
    rows.sort((a,b)=>rankRow(b)-rankRow(a)||a.symbol.localeCompare(b.symbol));
    const watchRows=favorites().filter(x=>!held.has(x.symbol)).map(x=>({...x,units:0,cost:null,costText:'',closePrice:null,closeText:'',marketValue:null,unrealized:null,unrealizedText:'',returnRate:null,news:summarize(x.symbol)})).sort((a,b)=>rankRow(b)-rankRow(a));
    const key=JSON.stringify([state.sort,rows.map(x=>[x.symbol,x.cost,x.marketValue,x.unrealized,x.closeText,x.news.week.length,x.news.freshCompany.length]),watchRows.map(x=>[x.symbol,x.news.week.length])]);
    if(!force&&key===state.lastRenderKey)return;state.lastRenderKey=key;
    let panel=document.getElementById(panelId);if(!panel){panel=document.createElement('div');anchor.after(panel)}
    panel.outerHTML=panelHtml(rows,watchRows);
    bind(document.getElementById(panelId));
  }
  let timer=null;const schedule=()=>{clearTimeout(timer);timer=setTimeout(()=>render(false),180)};
  const observer=new MutationObserver(schedule);
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>{observer.observe(document.body,{childList:true,subtree:true,characterData:true});schedule()});else{observer.observe(document.body,{childList:true,subtree:true,characterData:true});schedule()}
  window.addEventListener('storage',schedule);window.addEventListener('online',()=>{state.payload=null;schedule()});
  window.PortfolioIntelligence={version:BUILD,refresh:()=>{state.payload=null;state.lastRenderKey='';return render(true)}};
})();
