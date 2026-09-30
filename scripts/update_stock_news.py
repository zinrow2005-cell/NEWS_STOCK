#!/usr/bin/env python3
from __future__ import annotations
import hashlib, html, json, re, time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'stock-news.json'
DIRECTORY = ROOT / 'stock-directory.json'
TZ = timezone(timedelta(hours=8))

SOURCES = [
    # Official/free RSS feeds. Google News search feeds are fallbacks and need no API key.
    ('Yahoo股市・最新新聞', 'https://tw.stock.yahoo.com/rss?category=news'),
    ('Yahoo股市・台股動態', 'https://tw.stock.yahoo.com/rss?category=tw-market'),
    ('Yahoo股市・研究報導', 'https://tw.stock.yahoo.com/rss?category=research'),
    ('中央社・產經證券', 'https://feeds.feedburner.com/rsscna/finance'),
    ('Google新聞・台股', 'https://news.google.com/rss/search?q=' + quote_plus('台股 OR 上市公司 OR 上櫃公司') + '&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'),
    ('Google新聞・科技股', 'https://news.google.com/rss/search?q=' + quote_plus('台灣 科技股 半導體 電子股') + '&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'),
    ('Google新聞・財報法說', 'https://news.google.com/rss/search?q=' + quote_plus('台灣 上市櫃 營收 財報 法說') + '&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'),
]


# A rotating free Google News scan expands coverage beyond broad market headlines.
# The full ~2,000-stock directory is split across 8 half-hour slots, so one full scan
# completes in about four hours without requiring any paid API key.
def rotating_stock_sources(now=None):
    now = now or datetime.now(TZ)
    groups = 8
    slot = int(now.timestamp() // 1800) % groups
    selected = [row for i,row in enumerate(STOCK_DIRECTORY) if i % groups == slot]
    out=[]
    chunk_size=12
    for i in range(0, len(selected), chunk_size):
        chunk=selected[i:i+chunk_size]
        names=[name for _,name,_ in chunk if len(name)>=3]
        if not names: continue
        q='(' + ' OR '.join(f'"{name}"' for name in names) + ') 台股'
        out.append((f'Google新聞・全市場輪巡{slot+1}-{i//chunk_size+1}',
                    'https://news.google.com/rss/search?q=' + quote_plus(q) + '&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'))
    return out

def priority_stock_sources():
    # Stable smoke-check names plus common large-cap names; rotating scan handles the rest.
    symbols=['2330','2317','2454','2382','2308','2303','2881','2882','2891','2886','3711','2412']
    rows=[STOCK_BY_SYMBOL[s] for s in symbols if s in STOCK_BY_SYMBOL]
    out=[]
    for i in range(0,len(rows),6):
        chunk=rows[i:i+6]
        q='(' + ' OR '.join(f'"{name}"' for _,name,_ in chunk) + ') 台股'
        out.append((f'Google新聞・重點個股{i//6+1}',
                    'https://news.google.com/rss/search?q=' + quote_plus(q) + '&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'))
    return out

EVENT_RULES = {
    '財報/營收': ['營收','財報','季報','年報','eps','獲利','淨利','毛利','營益','每股盈餘','財測'],
    '股利/公司行動': ['股利','配息','配股','除息','除權','減資','增資','分割','庫藏股','現增'],
    '訂單/營運': ['接單','訂單','出貨','產能','擴產','稼動','需求','客戶','供應鏈','報價','漲價','降價'],
    '重大訊息': ['重大訊息','重訊','停牌','恢復交易','處分','裁罰','訴訟','調查','下市','終止上市','併購','收購','合併'],
    '籌碼/法人': ['外資','投信','自營商','三大法人','買超','賣超','持股','目標價','評等','券商'],
    '產業/政策': ['政策','法規','關稅','補貼','匯率','利率','央行','fed','產業','景氣','出口','進口'],
    '市場盤勢': ['台股','大盤','加權指數','櫃買','盤中','盤後','開盤','收盤','漲停','跌停'],
}
IMPORTANT = [
    ('重大', 22, ['重大訊息','停牌','恢復交易','裁罰','訴訟','併購','收購','合併','下市','董事會']),
    ('財務', 18, ['財報','eps','每股盈餘','營收','淨利','獲利','財測','毛利率','營益率']),
    ('資本', 15, ['股利','配息','配股','減資','增資','庫藏股','除權','除息']),
    ('營運', 12, ['訂單','接單','出貨','擴產','產能','客戶','漲價','降價','供應鏈']),
    ('法人', 8, ['外資','投信','目標價','評等','買超','賣超']),
]
POS = ['創高','成長','上修','優於預期','獲利增加','轉盈','大增','增加','擴產','接單','漲價','買超','調升','突破','利多']
NEG = ['衰退','下修','低於預期','虧損','轉虧','大減','減少','砍單','停產','裁員','跌停','賣超','調降','裁罰','訴訟','利空']

IMPACT_RULES = {
    '營收/獲利': ['營收','財報','eps','獲利','淨利','毛利','營益','財測','漲價','降價'],
    '訂單/需求': ['訂單','接單','出貨','需求','客戶','砍單','報價'],
    '產能/資本支出': ['產能','擴產','建廠','設備','資本支出','capex','稼動'],
    '股東權益': ['股利','配息','配股','除息','除權','減資','增資','庫藏股'],
    '法規/政策': ['政策','法規','關稅','補貼','裁罰','調查','央行','利率','fed'],
    '公司治理/重大事件': ['董事會','停牌','併購','收購','合併','訴訟','下市','處分'],
    '市場籌碼': ['外資','投信','自營商','三大法人','買超','賣超','持股','評等','目標價'],
}
SIGNALS = {
    '財報/營收': ['下一次月營收','下一季財報/法說','毛利率與營益率','公司財測是否調整'],
    '股利/公司行動': ['董事會/股東會日期','除權息基準日','現金股利入帳時程','增減資執行進度'],
    '訂單/營運': ['後續接單與出貨','產能利用率','主要客戶需求','報價與成本變化'],
    '重大訊息': ['公司正式重大訊息','主管機關後續公告','董事會決議','事件處理進度'],
    '籌碼/法人': ['三大法人連續買賣','外資持股變化','券商評等後續修正','成交量與籌碼集中度'],
    '產業/政策': ['政策正式生效日','主管機關細則','同業反應','匯率/利率變化'],
    '市場盤勢': ['大盤成交量','同族群強弱','外資期現貨動向','市場風險事件'],
    '其他財經': ['公司後續公告','是否有第二來源確認','相關產業/客戶動態'],
}

STOP = {'台股','股市','今日','最新','快訊','盤中','盤後','市場','公司','宣布','表示','指出','今年','明年','去年','大盤','法人','外資'}



def load_stock_directory():
    try:
        raw=json.loads(DIRECTORY.read_text(encoding='utf-8'))
        out=[]
        for row in raw.get('items',[]):
            if not isinstance(row,list) or len(row)<3: continue
            symbol,name,market=str(row[0]).strip(),str(row[1]).strip(),str(row[2]).strip()
            if not re.fullmatch(r'\d{4}', symbol): continue
            if market not in ('listed','otc'): continue
            if len(name)<2: continue
            out.append((symbol,name,market))
        return out
    except Exception:
        return []

STOCK_DIRECTORY = load_stock_directory()
STOCK_BY_SYMBOL = {x[0]: x for x in STOCK_DIRECTORY}
# Longer names first prevents e.g. 聯發科 from also matching 聯發.
STOCK_BY_NAME = sorted(STOCK_DIRECTORY, key=lambda x: (-len(x[1]), x[0]))

def match_stocks(title, summary):
    corpus=f'{title} {summary}'
    found=[]; seen=set(); matched_names=[]
    explicit=[]
    for sym in re.findall(r'(?<!\d)(\d{4})(?!\d)', corpus):
        if sym not in explicit: explicit.append(sym)
    for symbol in explicit:
        row=STOCK_BY_SYMBOL.get(symbol)
        if row and symbol not in seen:
            _,name,market=row
            found.append({'symbol':symbol,'name':name,'market':market})
            seen.add(symbol); matched_names.append(name)
            if len(found)>=8: return found
    for symbol,name,market in STOCK_BY_NAME:
        if symbol in seen or name not in corpus: continue
        # If this short name is contained in an already matched longer company name, skip it.
        if any(name != longer and name in longer for longer in matched_names):
            continue
        # Two-character company names are common in Taiwan, but substring collisions are noisy
        # (e.g. 新產 inside 新產品). Require at least one CJK boundary around the occurrence.
        if len(name) == 2:
            boundary_ok=False
            for mm in re.finditer(re.escape(name), corpus):
                left=corpus[mm.start()-1] if mm.start()>0 else ''
                right=corpus[mm.end()] if mm.end()<len(corpus) else ''
                left_cjk=bool(re.match(r'[\u4e00-\u9fff]', left)) if left else False
                right_cjk=bool(re.match(r'[\u4e00-\u9fff]', right)) if right else False
                if not (left_cjk and right_cjk):
                    boundary_ok=True; break
            if not boundary_ok:
                continue
        found.append({'symbol':symbol,'name':name,'market':market})
        seen.add(symbol); matched_names.append(name)
        if len(found)>=8: break
    return found

def text(v):
    return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', str(v or '')))).strip()

def fetch(url, timeout=10):
    # Keep failures isolated: one dead feed must not stall the whole GitHub Action.
    last = None
    for attempt in range(2):
        try:
            req = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (compatible; StockRecord-News/4.7.2; +https://github.com/)',
                'Accept': 'application/rss+xml, application/atom+xml, application/xml, text/xml, */*',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.6',
                'Cache-Control': 'no-cache',
            })
            with urlopen(req, timeout=timeout) as r:
                data = r.read(4 * 1024 * 1024)
                if not data:
                    raise RuntimeError('empty response')
                return data
        except Exception as e:
            last = e
            if attempt == 0:
                time.sleep(0.8)
    raise last

def child_text(node, names):
    local_names = {n.split(':')[-1].lower() for n in names}
    for name in names:
        found = node.find(name)
        if found is not None and found.text:
            return found.text
    for c in list(node):
        if c.tag.split('}')[-1].lower() in local_names and c.text:
            return c.text
    return ''

def parse_date(value):
    value = (value or '').strip()
    if not value:
        return ''
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None: dt = dt.replace(tzinfo=TZ)
        return dt.astimezone(TZ).isoformat(timespec='seconds')
    except Exception:
        pass
    try:
        dt = datetime.fromisoformat(value.replace('Z','+00:00'))
        if dt.tzinfo is None: dt = dt.replace(tzinfo=TZ)
        return dt.astimezone(TZ).isoformat(timespec='seconds')
    except Exception:
        return ''

def classify(title, summary):
    corpus = f'{title} {summary}'.lower()
    categories = []
    for cat, kws in EVENT_RULES.items():
        if any(k.lower() in corpus for k in kws): categories.append(cat)
    if not categories: categories = ['其他財經']
    score = 38
    reasons = []
    for label, pts, kws in IMPORTANT:
        hits = [k for k in kws if k.lower() in corpus]
        if hits:
            score += pts
            reasons.append(f'{label}:{hits[0]}')
    if re.search(r'\b\d{4}\b', corpus): score += 2
    score = max(0, min(100, score))
    p = sum(1 for k in POS if k in corpus)
    n = sum(1 for k in NEG if k in corpus)
    sentiment = '偏正面' if p > n else '偏負面' if n > p else '中性/待確認'
    return categories, score, sentiment, reasons[:3]

def impact_analysis(title, summary, categories, sentiment):
    corpus = f'{title} {summary}'.lower()
    areas = [label for label, kws in IMPACT_RULES.items() if any(k.lower() in corpus for k in kws)]
    if not areas: areas = ['待確認影響']
    primary = categories[0] if categories else '其他財經'
    signals = SIGNALS.get(primary, SIGNALS['其他財經'])[:4]
    if sentiment == '偏正面':
        short = '短期先確認消息是否由公司公告或多個來源交叉證實，並觀察市場是否已提前反映。'
    elif sentiment == '偏負面':
        short = '短期先確認事件範圍、一次性或持續性，以及公司是否提出說明或修正措施。'
    else:
        short = '短期以官方公告與後續數據為主，避免只由單一標題判斷事件方向。'
    mid = {
        '財報/營收':'中期追蹤後續營收、毛利率、EPS 與公司財測是否延續或反轉。',
        '股利/公司行動':'中期追蹤董事會/股東會決議與公司行動實際執行條件。',
        '訂單/營運':'中期追蹤訂單能見度、出貨節奏、產能利用率與主要客戶需求。',
        '重大訊息':'中期追蹤公司正式說明、主管機關處理與事件對營運的實際影響。',
        '籌碼/法人':'中期觀察法人買賣是否具連續性，並與基本面數據交叉比對。',
        '產業/政策':'中期追蹤政策細則、正式生效時間與同業受影響程度。',
        '市場盤勢':'中期將個股與產業族群、大盤及基本面變化一起比較。',
    }.get(primary, '中期持續追蹤公司公告、產業資訊與後續營運數據。')
    long = '長期仍應回到營收成長、獲利品質、現金流、競爭力與產業趨勢，不以單一新聞作結論。'
    dates = extract_dates(f'{title} {summary}')
    return areas[:4], {'short': short, 'mid': mid, 'long': long}, signals, dates

def extract_dates(corpus):
    out=[]
    patterns = [
        r'(?<!\d)(20\d{2})[年/\-.](\d{1,2})[月/\-.](\d{1,2})日?',
        r'(?<!\d)(\d{1,2})[月/\-.](\d{1,2})日',
    ]
    now=datetime.now(TZ)
    for p in patterns:
        for m in re.finditer(p, corpus):
            try:
                if len(m.groups())==3: y,mo,da=map(int,m.groups())
                else: y=now.year;mo,da=map(int,m.groups())
                dt=datetime(y,mo,da,tzinfo=TZ)
                label=f'{y:04d}-{mo:02d}-{da:02d}'
                if label not in out: out.append(label)
            except Exception: pass
    return out[:5]

def fingerprint(value):
    s = re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+', '', value).lower()
    return hashlib.sha1(s.encode('utf-8')).hexdigest()[:18]

def title_tokens(title):
    s=re.sub(r'[^0-9A-Za-z\u4e00-\u9fff]+',' ',title).lower()
    toks=set()
    for word in s.split():
        if len(word)>=2 and word not in STOP: toks.add(word)
    cjk=''.join(re.findall(r'[\u4e00-\u9fff]',s))
    for n in (2,3):
        for i in range(max(0,len(cjk)-n+1)):
            tok=cjk[i:i+n]
            if tok not in STOP: toks.add(tok)
    return toks

def similar(a,b):
    ta,tb=a['_tokens'],b['_tokens']
    if not ta or not tb: return False
    inter=len(ta&tb); union=len(ta|tb)
    j=inter/union if union else 0
    contain=inter/min(len(ta),len(tb)) if min(len(ta),len(tb)) else 0
    return j>=0.24 or (inter>=5 and contain>=0.25)

def cluster_items(items):
    # Cluster only nearby articles with overlapping primary event category.
    for x in items: x['_tokens']=title_tokens(x['title'])
    groups=[]
    for item in sorted(items,key=lambda x:x.get('publishedAt',''),reverse=True):
        placed=False
        idate=None
        try: idate=datetime.fromisoformat(item.get('publishedAt',''))
        except Exception: pass
        for g in groups:
            lead=g[0]
            if item['categories'][0] != lead['categories'][0]: continue
            try:
                ldate=datetime.fromisoformat(lead.get('publishedAt',''))
                if idate and abs((idate-ldate).days)>5: continue
            except Exception: pass
            if similar(item,lead):
                g.append(item); placed=True; break
        if not placed: groups.append([item])
    for group in groups:
        lead=max(group,key=lambda x:(x.get('importance',0),len(x.get('summary',''))))
        cid='evt-'+fingerprint(lead['title']+'|'+lead['categories'][0]+'|'+(lead.get('publishedAt','')[:10]))
        sources=sorted({x['source'] for x in group if x.get('source')})
        maximp=max(x.get('importance',0) for x in group)
        # Multiple independent reports modestly raise reading priority.
        cluster_bonus=min(8,max(0,len(sources)-1)*3)
        for x in group:
            x['clusterId']=cid
            x['clusterSize']=len(group)
            x['clusterSources']=sources
            x['eventImportance']=min(100,maximp+cluster_bonus)
            x.pop('_tokens',None)
    return items

def parse_feed(source_name, raw):
    root = ET.fromstring(raw)
    items = []
    candidates = root.findall('.//item')
    if not candidates:
        candidates = [n for n in root.iter() if n.tag.split('}')[-1].lower() == 'entry']
    for n in candidates:
        title = text(child_text(n, ['title']))
        link = child_text(n, ['link'])
        if not link:
            for c in list(n):
                if c.tag.split('}')[-1].lower() == 'link':
                    link = c.attrib.get('href','') or (c.text or '')
                    if link: break
        link = text(link)
        summary = text(child_text(n, ['description','summary','content','content:encoded']))[:650]
        pub = parse_date(child_text(n, ['pubDate','published','updated','date']))
        if not title or not link: continue
        cats, score, sentiment, reasons = classify(title, summary)
        areas, horizons, signals, dates = impact_analysis(title, summary, cats, sentiment)
        matched_stocks = match_stocks(title, summary)
        publisher = text(child_text(n, ['source']))
        display_source = publisher if (source_name.startswith('Google新聞') and publisher) else source_name
        items.append({
            'id': fingerprint(title + '|' + link),
            'fingerprint': fingerprint(title),
            'title': title,
            'url': link,
            'source': display_source,
            'aggregator': 'Google新聞' if source_name.startswith('Google新聞') else '',
            'feedSource': source_name,
            'publishedAt': pub,
            'summary': summary,
            'categories': cats,
            'importance': score,
            'sentiment': sentiment,
            'importanceReasons': reasons,
            'impactAreas': areas,
            'horizons': horizons,
            'watchSignals': signals,
            'mentionedDates': dates,
            'matchedStocks': matched_stocks,
        })
    return items

def main():
    # RSS feeds usually expose only recent articles. Preserve prior generated data so
    # the front-end 30/90-day intelligence views can build history over time.
    all_items = []
    status = {}
    history_cutoff = datetime.now(TZ) - timedelta(days=120)
    try:
        previous = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
        for item in previous.get('items', []):
            try:
                published = datetime.fromisoformat((item.get('publishedAt') or '').replace('Z','+00:00'))
                if published.tzinfo is None: published = published.replace(tzinfo=TZ)
                if published.astimezone(TZ) >= history_cutoff:
                    all_items.append(item)
            except Exception:
                pass
    except Exception:
        pass
    def fetch_one(source):
        name, url = source
        started=time.monotonic()
        try:
            parsed = parse_feed(name, fetch(url))
            return name, parsed, {'ok': True, 'count': len(parsed), 'seconds': round(time.monotonic()-started,2), 'url': url}
        except Exception as e:
            return name, [], {'ok': False, 'count': 0, 'seconds': round(time.monotonic()-started,2), 'url': url, 'message': f'{type(e).__name__}: {e}'}

    live_sources = SOURCES + priority_stock_sources() + rotating_stock_sources()
    # Fetch in parallel so several dead feeds cost ~one timeout window, not N x timeout.
    with ThreadPoolExecutor(max_workers=min(8, len(live_sources))) as pool:
        futs=[pool.submit(fetch_one, src) for src in live_sources]
        for fut in as_completed(futs):
            name, parsed, stat = fut.result()
            status[name] = stat
            all_items.extend(parsed)
    by_fp = {}
    for item in all_items:
        fp = item['fingerprint']
        prev = by_fp.get(fp)
        if not prev or len(item.get('summary','')) > len(prev.get('summary','')):
            by_fp[fp] = item
    items = list(by_fp.values())
    items.sort(key=lambda x: (x.get('publishedAt',''), x.get('importance',0)), reverse=True)
    items = cluster_items(items[:3000])
    successful_sources=sum(1 for x in status.values() if x.get('ok'))
    fresh_items=sum(int(x.get('count',0)) for x in status.values() if x.get('ok'))
    # Never destroy a working cache with an empty file just because every upstream feed failed.
    if successful_sources == 0 and not items:
        raise RuntimeError('All news sources failed and there is no previous cache; refusing to write an empty stock-news.json')
    if successful_sources == 0 and OUT.exists():
        print('WARNING: all live news sources failed; preserving previous stock-news.json unchanged')
        for name, st in status.items():
            print(f'  - {name}: {st.get("message","failed")}')
        return

    payload = {
        'version': 5,
        'generatedAt': datetime.now(TZ).isoformat(timespec='seconds'),
        'count': len(items),
        'freshItemCount': fresh_items,
        'successfulSourceCount': successful_sources,
        'attemptedSourceCount': len(live_sources),
        'eventCount': len({x.get('clusterId') for x in items}),
        'sources': status,
        'items': items,
        'historyDays': 120,
        'radarStockMatches': sum(1 for x in items if x.get('matchedStocks')),
        'matchedStockCount': len({m.get('symbol') for x in items for m in x.get('matchedStocks',[]) if m.get('symbol')}),
        'notice': '新聞重要性、事件類別、情緒與影響面向為規則式整理，僅供篩選與閱讀排序；系統會累積最多約120天RSS歷史，請以公司公告、主管機關資訊及原文核對。',
    }
    OUT.write_text(json.dumps(payload, ensure_ascii=False, separators=(',',':')) + '\n', encoding='utf-8')
    print(f'wrote {len(items)} news items / {payload["eventCount"]} events; fresh={fresh_items}; sources={successful_sources}/{len(live_sources)}')

if __name__ == '__main__':
    main()
