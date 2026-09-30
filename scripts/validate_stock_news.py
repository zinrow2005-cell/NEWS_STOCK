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

# v4.7.5 relevance + primary-subject diagnostics for smoke stocks
for _sym in ('2330','2317','2454'):
    _counts={'high':0,'related':0,'mention':0}
    for _x in items:
        for _m in _x.get('matchedStocks',[]):
            if str(_m.get('symbol'))==_sym:
                _lvl=_m.get('relevanceLevel','mention')
                _counts[_lvl]=_counts.get(_lvl,0)+1
    _primary=sum(1 for _x in items for _m in (_x.get('matchedStocks') or []) if str(_m.get('symbol'))==_sym and _m.get('isPrimary') is True)
    print(f'relevance {_sym}: primary={_primary}, high={_counts.get("high",0)}, related={_counts.get("related",0)}, mention={_counts.get("mention",0)}')
