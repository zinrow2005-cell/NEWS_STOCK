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

# v4.7.6 relevance + primary-subject diagnostics and hierarchy guard
for _sym in ('2330','2317','2454'):
    _counts={'high':0,'related':0,'mention':0}
    for _x in items:
        for _m in _x.get('matchedStocks',[]):
            if str(_m.get('symbol'))==_sym:
                _lvl=_m.get('relevanceLevel','mention')
                _counts[_lvl]=_counts.get(_lvl,0)+1
    _primary=sum(1 for _x in items for _m in (_x.get('matchedStocks') or []) if str(_m.get('symbol'))==_sym and _m.get('isPrimary') is True)
    _high=_counts.get('high',0)
    print(f'relevance {_sym}: primary={_primary}, high={_high}, related={_counts.get("related",0)}, mention={_counts.get("mention",0)}')
    if _primary > _high:
        print(f'ERROR: relevance hierarchy broken for {_sym}: primary={_primary} > high={_high}')
        sys.exit(5)

# Global invariant: every primary relation must also be high relevance.
_bad=[]
for _x in items:
    for _m in (_x.get('matchedStocks') or []):
        if _m.get('isPrimary') is True and _m.get('relevanceLevel') != 'high':
            _bad.append((_m.get('symbol'), _m.get('relevanceLevel'), _x.get('title','')[:100]))
            if len(_bad)>=10: break
    if len(_bad)>=10: break
if _bad:
    print('ERROR: primary relations that are not high relevance:')
    for _b in _bad: print('  ', _b)
    sys.exit(6)


# v4.7.7 content-sampling diagnostics: print real titles from the live 3,000-item pool.
# This turns GitHub Actions itself into a manual precision audit without exposing article bodies.
def _relation(item, sym):
    for mm in item.get('matchedStocks') or []:
        if str(mm.get('symbol')) == str(sym):
            return mm
    return None

for _sym in ('2330','2317','2454'):
    _primary=[]; _high_nonprimary=[]; _mentions=[]
    for _x in items:
        _m=_relation(_x,_sym)
        if not _m: continue
        row=(_x.get('title') or '').replace('\n',' ').strip()
        if not row: continue
        if _m.get('isPrimary') is True:
            _primary.append(row)
        elif _m.get('relevanceLevel') == 'high':
            _high_nonprimary.append(row)
        elif _m.get('relevanceLevel') == 'mention':
            _mentions.append(row)
    print(f'--- sample {_sym} primary ({len(_primary)}) ---')
    for t in _primary[:8]: print(' PRIMARY:', t[:160])
    print(f'--- sample {_sym} high-not-primary ({len(_high_nonprimary)}) ---')
    for t in _high_nonprimary[:5]: print(' HIGH_ONLY:', t[:160])
    print(f'--- sample {_sym} mention ({len(_mentions)}) ---')
    for t in _mentions[:3]: print(' MENTION:', t[:160])
