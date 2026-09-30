#!/usr/bin/env python3
from __future__ import annotations
import json, time, re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'market-close.json'
HISTORY=ROOT/'market-history.json'
KEEP_TRADING_DAYS=180
TWSE_INDEX_URL='https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX'
TPEX_INDEX_URL='https://www.tpex.org.tw/www/zh-tw/afterTrading/indexSummary?date=&response=json'
TWSE_COMPANY_URL='https://openapi.twse.com.tw/v1/opendata/t187ap03_L'
# MOPS-style OTC endpoint is attempted opportunistically. Failure does not affect quotes/benchmarks.
OTC_COMPANY_CANDIDATES=[
    'https://openapi.twse.com.tw/v1/opendata/t187ap03_O',
    'https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O',
]
SOURCES=[
    ('twse','listed','證交所','https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL'),
    ('tpex','otc','櫃買中心','https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes')
]

MARKET_META={
    'TAIEX':{'name':'臺灣加權指數','source':'TWSE MI_INDEX','scope':'上市市場基準','kind':'market','market':'listed'},
    'TPEX':{'name':'櫃買指數','source':'TPEx indexSummary','scope':'上櫃市場基準','kind':'market','market':'otc'},
}

def roc_date(value):
    s=''.join(ch for ch in str(value or '').strip() if ch.isdigit())
    if len(s)==7:return f'{int(s[:3])+1911:04d}-{s[3:5]}-{s[5:7]}'
    if len(s)==8:return f'{int(s[:4]):04d}-{s[4:6]}-{s[6:8]}'
    return ''

def num(value):
    try:return float(str(value or '').replace(',','').replace('%','').strip())
    except Exception:return 0.0

def fetch_json(url):
    last=None
    for attempt in range(3):
        try:
            req=Request(url,headers={'User-Agent':'Mozilla/5.0 GitHubActions StockRecord/2.5','Accept':'application/json,text/plain,*/*','Referer':'https://www.tpex.org.tw/'})
            with urlopen(req,timeout=35) as r:return json.loads(r.read().decode('utf-8-sig'))
        except Exception as e:
            last=e;time.sleep(2*(attempt+1))
    raise last

def load_json(path,default):
    try:return json.loads(path.read_text(encoding='utf-8'))
    except Exception:return default

def norm_industry(s):
    s=str(s or '').strip()
    s=re.sub(r'[\s　()（）/／\-]+','',s)
    for tail in ('類指數','指數','產業','工業','業'):
        if s.endswith(tail) and len(s)>len(tail)+1:s=s[:-len(tail)]
    aliases={'電腦及週邊設備':'電腦週邊','觀光餐旅':'觀光','數位雲端':'資訊服務','綠能環保':'綠能環保'}
    return aliases.get(s,s)

def industry_key(market,name):
    return f'IND:{market}:{norm_industry(name)}'

def industry_meta(market,name,source):
    clean=str(name or '').strip()
    return {'name':clean if clean.endswith('指數') else f'{clean}產業指數','source':source,'scope':'產業基準','kind':'industry','market':market,'industry':clean}

def iter_nested_rows(obj):
    """Yield row-like dict/list values from TPEx JSON of varying schemas."""
    if isinstance(obj,dict):
        # Common table schema: fields/columns plus data/aaData
        cols=obj.get('fields') or obj.get('columns') or obj.get('columnNames')
        data=obj.get('data') or obj.get('aaData')
        if isinstance(data,list):
            if isinstance(cols,list):
                names=[]
                for c in cols:
                    if isinstance(c,dict): names.append(str(c.get('title') or c.get('name') or c.get('data') or ''))
                    else:names.append(str(c))
                for row in data:
                    if isinstance(row,list):yield {names[i] if i<len(names) else str(i):v for i,v in enumerate(row)}
                    elif isinstance(row,dict):yield row
            else:
                for row in data:
                    if isinstance(row,(dict,list)):yield row
        for v in obj.values():
            if isinstance(v,(dict,list)):yield from iter_nested_rows(v)
    elif isinstance(obj,list):
        for x in obj:
            if isinstance(x,dict):
                yield x
                yield from iter_nested_rows(x)
            elif isinstance(x,list):yield x

def row_get(row,candidates):
    if not isinstance(row,dict):return None
    for k,v in row.items():
        ks=str(k).strip().lower().replace(' ','')
        if any(c.lower().replace(' ','') in ks for c in candidates):return v
    return None

def parse_twse_indices(rows, fallback_date):
    values={}; meta={}
    for row in rows if isinstance(rows,list) else []:
        if not isinstance(row,dict):continue
        name=str(row.get('指數') or row.get('Index') or row.get('IndexName') or '').strip()
        close=num(row.get('收盤指數') if '收盤指數' in row else row.get('ClosingIndex') or row.get('Close'))
        date=roc_date(row.get('日期') or row.get('Date')) or fallback_date
        if not name or not (close>0) or not date:continue
        if name=='發行量加權股價指數':
            values.setdefault(date,{})['TAIEX']=round(close,4)
            meta['TAIEX']=MARKET_META['TAIEX']
            continue
        # Industry/category indices only. Exclude total-return/thematic variants.
        if ('類指數' in name or name.endswith('業指數')) and not any(x in name for x in ('報酬','槓桿','反向','臺灣50','公司治理','高股息')):
            k=industry_key('listed',name)
            values.setdefault(date,{})[k]=round(close,4)
            meta[k]=industry_meta('listed',name,'TWSE MI_INDEX')
    return values,meta

def parse_tpex_indices(payload, fallback_date):
    values={};meta={};date=fallback_date
    # Try top-level date hints first.
    if isinstance(payload,dict):
        for k,v in payload.items():
            if 'date' in str(k).lower() or '日期' in str(k):
                date=roc_date(v) or date
    seen=set()
    for row in iter_nested_rows(payload):
        name='';close=0.0
        if isinstance(row,dict):
            name=str(row_get(row,['指數','index','名稱','name']) or '').strip()
            close=num(row_get(row,['收市指數','收盤指數','closing','close','indexvalue']))
            rd=roc_date(row_get(row,['日期','date']))
            if rd:date=rd
        elif isinstance(row,list) and len(row)>=2:
            name=str(row[0] or '').strip();close=num(row[1])
        if not name or not close or (name,close) in seen:continue
        seen.add((name,close))
        if name=='櫃買指數':
            values.setdefault(date,{})['TPEX']=round(close,4);meta['TPEX']=MARKET_META['TPEX'];continue
        # TPEx page publishes both sector indices and thematic indices. Keep sector-like names only.
        thematic=('富櫃','Quality','ESG','氣候','公司治理','高殖利率','薪酬','永續','就業','報酬','正向','反向')
        if not any(t in name for t in thematic) and len(name)<=16:
            k=industry_key('otc',name)
            values.setdefault(date,{})[k]=round(close,4);meta[k]=industry_meta('otc',name,'TPEx indexSummary')
    return values,meta

def parse_company_industries(rows,market):
    out={}
    if not isinstance(rows,list):return out
    for row in rows:
        if not isinstance(row,dict):continue
        sym=str(row_get(row,['公司代號','股票代號','code','symbol']) or '').strip().upper()
        ind=str(row_get(row,['產業別','產業類別','industry']) or '').strip()
        if sym and ind:out[sym]={'market':market,'industry':ind,'industryNorm':norm_industry(ind)}
    return out

def merge_nested(dst,src):
    for date,vals in src.items():
        d=dst.get(date) if isinstance(dst.get(date),dict) else {}
        d.update(vals);dst[date]=d

def main():
    old=load_json(OUT,{})
    old_quotes=old.get('quotes') if isinstance(old.get('quotes'),dict) else {}
    by_market={'listed':{},'otc':{}}
    for sym,q in old_quotes.items():
        if isinstance(q,dict) and q.get('market') in by_market:by_market[q['market']][sym]=q
    status={};trading_dates={};success=0;fresh_by_date={};volume_by_date={};quote_industries={}
    for key,market,label,url in SOURCES:
        try:
            rows=fetch_json(url)
            if not isinstance(rows,list) or not rows:raise RuntimeError('empty response')
            fresh={}
            for row in rows:
                if not isinstance(row,dict):continue
                sym=str(row.get('Code') or row.get('SecuritiesCompanyCode') or '').strip().upper()
                price=num(row.get('ClosingPrice') if 'ClosingPrice' in row else row.get('Close'))
                date=roc_date(row.get('Date'))
                name=str(row.get('Name') or row.get('CompanyName') or '').strip()
                industry=str(row_get(row,['Industry','產業']) or '').strip()
                volume=num(row_get(row,['TradeVolume','TradingShares','成交股數','成交量','Volume']))
                if sym and price>0 and date:
                    fresh[sym]={'symbol':sym,'stockName':name,'price':price,'priceDate':date,'market':market,'source':label,'volume':round(volume,4) if volume>0 else None}
                    if industry:quote_industries[sym]={'market':market,'industry':industry,'industryNorm':norm_industry(industry)}
                    fresh_by_date.setdefault(date,{})[sym]=price
                    if volume>0: volume_by_date.setdefault(date,{})[sym]=volume
            if not fresh:raise RuntimeError('no recognizable quote rows')
            by_market[market]=fresh
            dates=sorted({q['priceDate'] for q in fresh.values()});trading_dates[key]=dates[-1] if dates else ''
            status[key]={'ok':True,'count':len(fresh),'message':'official sync complete','tradingDate':trading_dates[key]};success+=1
        except Exception as e:
            kept=len(by_market[market]);status[key]={'ok':False,'count':kept,'message':f'{type(e).__name__}: {e}; kept previous {kept} quotes'}

    benchmark_fresh={};benchmark_meta={}
    # TWSE broad-market + listed industry indices
    try:
        rows=fetch_json(TWSE_INDEX_URL)
        vals,meta=parse_twse_indices(rows,trading_dates.get('twse',''))
        merge_nested(benchmark_fresh,vals);benchmark_meta.update(meta)
        status['twse_indices']={'ok':bool(vals),'count':sum(len(v) for v in vals.values()),'message':'TWSE market/industry indices sync complete' if vals else 'no TWSE index rows parsed'}
    except Exception as e:status['twse_indices']={'ok':False,'count':0,'message':f'{type(e).__name__}: {e}; kept previous benchmark history'}
    # TPEx broad-market + OTC industry indices
    try:
        payload=fetch_json(TPEX_INDEX_URL)
        vals,meta=parse_tpex_indices(payload,trading_dates.get('tpex',''))
        merge_nested(benchmark_fresh,vals);benchmark_meta.update(meta)
        status['tpex_indices']={'ok':bool(vals),'count':sum(len(v) for v in vals.values()),'message':'TPEx market/industry indices sync complete' if vals else 'no TPEx index rows parsed'}
    except Exception as e:status['tpex_indices']={'ok':False,'count':0,'message':f'{type(e).__name__}: {e}; kept previous benchmark history'}

    # Official listed company industry map + best-effort OTC map.
    company_industries={}
    try:
        company_industries.update(parse_company_industries(fetch_json(TWSE_COMPANY_URL),'listed'))
        status['listed_industries']={'ok':bool(company_industries),'count':sum(1 for x in company_industries.values() if x['market']=='listed'),'message':'listed company industry map synced'}
    except Exception as e:status['listed_industries']={'ok':False,'count':0,'message':f'{type(e).__name__}: {e}'}
    otc_ok=False
    for u in OTC_COMPANY_CANDIDATES:
        try:
            got=parse_company_industries(fetch_json(u),'otc')
            if got:
                company_industries.update(got);otc_ok=True;break
        except Exception:pass
    # Daily TPEx rows may carry industry in some API revisions; merge if present.
    company_industries.update(quote_industries)
    status['otc_industries']={'ok':otc_ok or any(x['market']=='otc' for x in company_industries.values()),'count':sum(1 for x in company_industries.values() if x['market']=='otc'),'message':'OTC industry map synced when public field/endpoint available; market benchmark remains available otherwise'}

    quotes={**by_market['listed'],**by_market['otc']}
    if not quotes:raise SystemExit('No quote data available from official sources and no previous data to preserve.')
    tz=timezone(timedelta(hours=8))
    payload={'version':3,'generatedAt':datetime.now(tz).isoformat(timespec='seconds'),'tradingDates':trading_dates,'quotes':dict(sorted(quotes.items())),'sourceStatus':status}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')

    hist=load_json(HISTORY,{})
    dates=hist.get('dates') if isinstance(hist.get('dates'),dict) else {}
    benchmarks=hist.get('benchmarks') if isinstance(hist.get('benchmarks'),dict) else {}
    volumes=hist.get('volumes') if isinstance(hist.get('volumes'),dict) else {}
    old_meta=hist.get('benchmarkMeta') if isinstance(hist.get('benchmarkMeta'),dict) else {}
    symbol_markets=hist.get('symbolMarkets') if isinstance(hist.get('symbolMarkets'),dict) else {}
    symbol_industries=hist.get('symbolIndustries') if isinstance(hist.get('symbolIndustries'),dict) else {}
    for date,prices in fresh_by_date.items():
        merged=dates.get(date) if isinstance(dates.get(date),dict) else {};merged.update({k:round(v,4) for k,v in prices.items() if v>0});dates[date]=dict(sorted(merged.items()))
    for date,values in volume_by_date.items():
        merged=volumes.get(date) if isinstance(volumes.get(date),dict) else {};merged.update({k:round(v,4) for k,v in values.items() if v>0});volumes[date]=dict(sorted(merged.items()))
    for date,values in benchmark_fresh.items():
        merged=benchmarks.get(date) if isinstance(benchmarks.get(date),dict) else {};merged.update({k:round(v,4) for k,v in values.items() if v>0});benchmarks[date]=dict(sorted(merged.items()))
    for sym,q in quotes.items():
        market=q.get('market') if isinstance(q,dict) else None
        if market in ('listed','otc'):symbol_markets[sym]=market
    for sym,info in company_industries.items():
        if info.get('industry'):
            symbol_industries[sym]={'market':info.get('market') or symbol_markets.get(sym),'industry':info['industry'],'industryNorm':info.get('industryNorm') or norm_industry(info['industry'])}
    keep=sorted(dates.keys())[-KEEP_TRADING_DAYS:];keep_set=set(keep)
    dates={d:dates[d] for d in keep};benchmarks={d:benchmarks[d] for d in sorted(benchmarks.keys()) if d in keep_set};volumes={d:volumes[d] for d in sorted(volumes.keys()) if d in keep_set}
    all_meta={**MARKET_META,**old_meta,**benchmark_meta}
    history_payload={
        'version':4,'generatedAt':datetime.now(tz).isoformat(timespec='seconds'),'keepTradingDays':KEEP_TRADING_DAYS,'tradingDayCount':len(dates),
        'dates':dates,'volumes':volumes,'benchmarks':benchmarks,'benchmarkMeta':all_meta,'symbolMarkets':dict(sorted(symbol_markets.items())),'symbolIndustries':dict(sorted(symbol_industries.items())),
        'notice':'v2.5：除收盤價、市場與產業基準外，每日同步累積個股成交量，用於新聞事件當下的量價、均線、波動與事件後最大漲幅/最大回撤分析。缺少成交量或歷史天數時會顯示待累積，不補假值。'
    }
    HISTORY.write_text(json.dumps(history_payload,ensure_ascii=False,separators=(',',':'))+'\n',encoding='utf-8')
    print(f'wrote {len(quotes)} quotes; history={len(dates)} days; benchmark_days={len(benchmarks)}; benchmark_keys={len(all_meta)}; industry_symbols={len(symbol_industries)}')
if __name__=='__main__':main()
