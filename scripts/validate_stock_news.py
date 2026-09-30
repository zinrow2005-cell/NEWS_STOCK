#!/usr/bin/env python3
import json, sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'stock-news.json'
try:
    d=json.loads(p.read_text(encoding='utf-8'))
except Exception as e:
    print('ERROR invalid stock-news.json:',e); sys.exit(2)
items=d.get('items') or []
matched=sum(1 for x in items if x.get('matchedStocks'))
syms={m.get('symbol') for x in items for m in (x.get('matchedStocks') or []) if m.get('symbol')}
print(f'news count={len(items)}, matched_articles={matched}, matched_symbols={len(syms)}, sources={d.get("successfulSourceCount")}/{d.get("attemptedSourceCount")}')
for sym in ['2330','2317','2454']:
    n=sum(1 for x in items if any(m.get('symbol')==sym for m in (x.get('matchedStocks') or [])))
    print(f'smoke {sym}: {n} articles')
if len(items) <= 0:
    print('ERROR: zero news items; refusing deployment/commit'); sys.exit(3)
if matched <= 0:
    print('ERROR: no article matched any listed/OTC stock; pipeline is not useful'); sys.exit(4)
