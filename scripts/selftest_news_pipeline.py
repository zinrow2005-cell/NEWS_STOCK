#!/usr/bin/env python3
import importlib.util
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

# Relevance regression tests
high=m.match_stocks('台積電（2330）8月營收創高，AI需求強勁','AI需求增加。')
r2330=next(x for x in high if x['symbol']=='2330')
if r2330['relevanceLevel']!='high' or r2330['relevanceScore']<78:
    raise SystemExit(f'expected high relevance for 2330 headline, got {r2330}')

related=m.match_stocks('半導體供應鏈展望','市場焦點之一為台積電，後續觀察先進製程。')
r2330=next(x for x in related if x['symbol']=='2330')
if r2330['relevanceLevel'] not in ('related','mention'):
    raise SystemExit(f'unexpected relevance for summary mention: {r2330}')

multi=m.match_stocks('鴻海、廣達、聯發科供應鏈動態','三家公司同步受到市場關注。')
if not all('relevanceScore' in x and 'relevanceLevel' in x for x in multi):
    raise SystemExit('multi-company relevance metadata missing')

# Precision regression tests: broad roundup/listicle mentions should not outrank focused company news.
focused=m.match_stocks('台積電法說會聚焦2奈米與AI需求','公司說明先進製程與資本支出。')
f2330=next(x for x in focused if x['symbol']=='2330')
if f2330['relevanceLevel']!='high':
    raise SystemExit(f'focused 2330 article should be high: {f2330}')

roundup=m.match_stocks('AI供應鏈焦點股：台積電、鴻海、廣達、聯發科同步受矚目','多檔大型權值股受到市場關注。')
for z in roundup:
    if z['relevanceLevel']=='high':
        raise SystemExit(f'roundup article should not be high for {z}')

summary_only=m.match_stocks('半導體族群盤勢整理','市場同時關注台積電、聯發科、日月光投控等多家公司。')
for z in summary_only:
    if z['relevanceLevel']!='mention':
        raise SystemExit(f'summary-only multi-company mention should be mention: {z}')


# v4.7.5 primary-subject regression tests.
focused_primary=m.match_stocks('台積電法說會聚焦2奈米與AI需求','公司說明先進製程與資本支出。')
fp=next(x for x in focused_primary if x['symbol']=='2330')
if not fp.get('isPrimary'):
    raise SystemExit(f'focused single-company headline should be primary: {fp}')

roundup_primary=m.match_stocks('AI供應鏈焦點股：台積電、鴻海、廣達、聯發科同步受矚目','多檔大型權值股受到市場關注。')
if any(x.get('isPrimary') for x in roundup_primary):
    raise SystemExit(f'roundup must not have a primary stock: {roundup_primary}')

lead_with_peers=m.match_stocks('台積電法說上修AI展望','供應鏈也提到鴻海與廣達後續需求。')
lead2330=next(x for x in lead_with_peers if x['symbol']=='2330')
if not lead2330.get('isPrimary'):
    raise SystemExit(f'headline-only lead company should remain primary even if peers appear in summary: {lead_with_peers}')
if any(x.get('isPrimary') for x in lead_with_peers if x['symbol']!='2330'):
    raise SystemExit(f'summary peers must not become primary: {lead_with_peers}')

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
for x in items:
    for z in x.get('matchedStocks',[]):
        if 'relevanceScore' not in z or 'relevanceLevel' not in z:
            raise SystemExit('parse_feed relevance metadata missing')
if len(items)!=3:
    raise SystemExit(f'expected 3 parsed items, got {len(items)}')
print('selftest OK:', len(items), 'items, symbols=', sorted(syms), 'relevance metadata OK')
