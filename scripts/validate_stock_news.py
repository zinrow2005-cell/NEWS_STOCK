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
    _core=sum(1 for _x in items for _m in (_x.get('matchedStocks') or []) if str(_m.get('symbol'))==_sym and _m.get('isCorePrimary') is True)
    _general=sum(1 for _x in items for _m in (_x.get('matchedStocks') or []) if str(_m.get('symbol'))==_sym and _m.get('primaryTier')=='general')
    _high=_counts.get('high',0)
    print(f'relevance {_sym}: core={_core}, general={_general}, primary={_primary}, high={_high}, related={_counts.get("related",0)}, mention={_counts.get("mention",0)}')
    if _core > _primary or _primary > _high:
        print(f'ERROR: relevance hierarchy broken for {_sym}: core={_core}, primary={_primary}, high={_high}')
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

# v4.7.8 invariant: core primary must be a core-tier primary and high relevance.
_core_bad=[]
for _x in items:
    for _m in (_x.get('matchedStocks') or []):
        if _m.get('isCorePrimary') is True and (not _m.get('isPrimary') or _m.get('primaryTier') != 'core' or _m.get('relevanceLevel') != 'high'):
            _core_bad.append((_m.get('symbol'), _m.get('primaryTier'), _m.get('relevanceLevel'), _x.get('title','')[:100]))
            if len(_core_bad)>=10: break
    if len(_core_bad)>=10: break
if _core_bad:
    print('ERROR: core-primary hierarchy broken:')
    for _b in _core_bad: print('  ', _b)
    sys.exit(7)



# v4.7.9: company-event vs price-action separation guard.
for _sym in ('2330','2317','2454'):
    _nature={}
    _bad_price=[]
    for _x in items:
        for _m in (_x.get('matchedStocks') or []):
            if str(_m.get('symbol')) != _sym: continue
            _n=_m.get('relationNature','related')
            _nature[_n]=_nature.get(_n,0)+1
            if _n in ('price_action','market_theme') and _m.get('isPrimary'):
                _bad_price.append((_x.get('title','')[:120],_n))
    print(f'nature {_sym}: core={_nature.get("company_core",0)}, general={_nature.get("company_general",0)}, price={_nature.get("price_action",0)}, market={_nature.get("market_theme",0)}, related={_nature.get("related",0)}')
    if _bad_price:
        print(f'ERROR: non-company stories marked primary for {_sym}:')
        for _b in _bad_price[:10]: print('  ',_b)
        sys.exit(8)

# v4.7.7 content-sampling diagnostics: print real titles from the live 3,000-item pool.
# This turns GitHub Actions itself into a manual precision audit without exposing article bodies.
def _relation(item, sym):
    for mm in item.get('matchedStocks') or []:
        if str(mm.get('symbol')) == str(sym):
            return mm
    return None

for _sym in ('2330','2317','2454'):
    _core=[]; _general=[]; _price=[]; _market=[]; _high_nonprimary=[]; _mentions=[]
    for _x in items:
        _m=_relation(_x,_sym)
        if not _m: continue
        row=(_x.get('title') or '').replace('\n',' ').strip()
        if not row: continue
        if _m.get('isCorePrimary') is True:
            _core.append(row)
        elif _m.get('isPrimary') is True:
            _general.append(row)
        elif _m.get('relationNature') == 'price_action':
            _price.append(row)
        elif _m.get('relationNature') == 'market_theme':
            _market.append(row)
        elif _m.get('relevanceLevel') == 'high':
            _high_nonprimary.append(row)
        elif _m.get('relevanceLevel') == 'mention':
            _mentions.append(row)
    print(f'--- sample {_sym} core-primary ({len(_core)}) ---')
    for t in _core[:6]: print(' CORE:', t[:160])
    print(f'--- sample {_sym} general-primary ({len(_general)}) ---')
    for t in _general[:4]: print(' GENERAL:', t[:160])
    print(f'--- sample {_sym} price-action ({len(_price)}) ---')
    for t in _price[:4]: print(' PRICE:', t[:160])
    print(f'--- sample {_sym} market-theme ({len(_market)}) ---')
    for t in _market[:3]: print(' MARKET:', t[:160])
    print(f'--- sample {_sym} high-not-primary ({len(_high_nonprimary)}) ---')
    for t in _high_nonprimary[:4]: print(' HIGH_ONLY:', t[:160])
    print(f'--- sample {_sym} mention ({len(_mentions)}) ---')
    for t in _mentions[:3]: print(' MENTION:', t[:160])
