#!/usr/bin/env python3
import importlib.util, tempfile, json
from pathlib import Path

MOD=Path(__file__).with_name('update_stock_news.py')
spec=importlib.util.spec_from_file_location('newsmod', MOD)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

# Matching regression tests
cases={
    '台積電（2330）8月營收創高，AI需求強勁':['2330'],
    '鴻海（2317）法說會公布最新展望':['2317'],
    '聯發科（2454）新品發表，聯發不應被誤抓':['2454'],
    '分析｜鴻海、廣達及聯發科掀千億籌資潮':['2317','2382','2454'],
}
for title, expected in cases.items():
    got=sorted(x['symbol'] for x in m.match_stocks(title,''))
    if got != sorted(expected):
        raise SystemExit(f'match failed: {title} => {got}, expected {expected}')

rss='''<?xml version="1.0" encoding="UTF-8"?>
<rss><channel>
<item><title>台積電（2330）8月營收創高</title><link>https://example.com/2330</link><description>AI需求增加，營收創高。</description><pubDate>Wed, 30 Sep 2026 08:00:00 +0800</pubDate><source>測試媒體A</source></item>
<item><title>鴻海（2317）法說釋出展望</title><link>https://example.com/2317</link><description>鴻海法說會說明營運。</description><pubDate>Wed, 30 Sep 2026 09:00:00 +0800</pubDate><source>測試媒體B</source></item>
<item><title>聯發科（2454）發布新品</title><link>https://example.com/2454</link><description>聯發科新晶片與客戶需求。</description><pubDate>Wed, 30 Sep 2026 10:00:00 +0800</pubDate><source>測試媒體C</source></item>
</channel></rss>'''.encode()
items=m.parse_feed('Google新聞・自我測試', rss)
syms={z['symbol'] for x in items for z in x.get('matchedStocks',[])}
for sym in ('2330','2317','2454'):
    if sym not in syms:
        raise SystemExit(f'parse/match selftest missing {sym}')
if len(items)!=3:
    raise SystemExit(f'expected 3 parsed items, got {len(items)}')
print('selftest OK:', len(items), 'items, symbols=', sorted(syms))
