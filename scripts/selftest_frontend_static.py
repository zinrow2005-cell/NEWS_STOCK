#!/usr/bin/env python3
from pathlib import Path
import re, sys, json
ROOT=Path(__file__).resolve().parents[1]
errors=[]
def check(cond,msg):
    if not cond: errors.append(msg)

def text(name):
    return (ROOT/name).read_text(encoding='utf-8')

js=text('news-center.js')
css=text('news-center.css')
pi=text('portfolio-intelligence.js')
sw=text('service-worker.js')
version='4.7.28'
check(version in js,'news-center.js version mismatch')
check(version in css,'news-center.css version mismatch')
check(version in pi,'portfolio-intelligence.js version mismatch')
check(version in sw and 'news-v47.28' in sw,'service-worker.js version/cache mismatch')

critical=[
 'bindDomRefs','reportUiError','runUiAction','sanitizeState','buildOptions','updateReadModes',
 'dateMatch','queryMatch','stockMatch','modeBaseItems','modeStatsFor','stockOverviewItems',
 'withinDays','stockDailyHighlights','eventGroupMeta','eventMergedSummary','eventSourceDetails',
 'mergeHealthHtml','researchStocks','renderDaily','renderResearchDashboard','renderTracking',
 'renderDashboard','renderOverview','renderDatabase','renderCross','renderRadar','render'
]
for fn in critical:
    check(re.search(r'function\s+'+re.escape(fn)+r'\s*\(',js) is not None,f'missing function: {fn}')

# Fixed shell elements must have explicit DOM references, not implicit window[id] globals.
for ident in ['newsDrawer','newsClose','newsRefresh','newsClear','newsDailyTab','newsResearchDashboardTab',
              'newsTrackTab','newsDashboardTab','newsFeedTab','newsOverviewTab','newsDatabaseTab',
              'newsCrossTab','newsRadarTab','newsOverviewWindow','newsSummary','newsStatus','newsList']:
    check(re.search(r'\blet\b[^;]*\b'+re.escape(ident)+r'\b',js) is not None,f'missing explicit DOM ref: {ident}')

# All view renderers must clear the nine tab states so stale active tabs cannot remain.
tabs=['newsDailyTab','newsResearchDashboardTab','newsTrackTab','newsDashboardTab','newsFeedTab','newsOverviewTab','newsDatabaseTab','newsCrossTab','newsRadarTab']
for fn in ['renderDaily','renderResearchDashboard','renderTracking','renderDashboard','renderOverview','renderDatabase','renderCross','renderRadar']:
    m=re.search(r'function\s+'+fn+r'\s*\([^)]*\)\s*\{',js)
    if not m: continue
    starts=[x for x in (js.find('\n  function ',m.end()),js.find('\nfunction ',m.end())) if x!=-1]
    body=js[m.start():min(starts or [len(js)])]
    for tab in tabs:
        check(tab in body,f'{fn} does not reset/reference {tab}')

for win in ['1d','3d','7d','30d','90d']:
    check(f'data-window="{win}"' in js,f'missing period button: {win}')
check("closest('button[data-window]')" in js or 'closest("button[data-window]")' in js,'period buttons lack delegated click handler')
check("state.view==='daily'" in js and 'state.overviewWindow=win' in js,'daily/overview period routing missing')
check('matchedStock(x,stock)' in js,'overview period stock matching is not strict')
check(re.search(r'loadPrefs\(\);sanitizeState\(\)',js) is not None,'saved state is not sanitized before startup')
check('selfCheck:' in js,'StockNewsCenter selfCheck is missing')
check("addEventListener('input'" in js or 'addEventListener("input"' in js,'input handlers missing')
check('state.crossStocks=[]' not in js,'database reset unexpectedly mutates old crossStocks state')
check('newsFavorites.forEach(add)' in js,'research stock picker does not include news favorites')

# Core dynamic controls / handlers.
for marker in ['data-news-track','data-news-read','data-track-open','data-radar-open','data-open-stock','data-db-symbol','data-build-reload']:
    check(marker in js,f'missing dynamic control/handler marker: {marker}')

# Portfolio intelligence safety/freshness.
check('loadedAt:0' in pi,'portfolio intelligence has no freshness timestamp')
check('15*60*1000' in pi,'portfolio intelligence does not refresh stale news')
check('type="button" data-pi-sort' in pi,'portfolio sort buttons lack explicit type=button')
check('moneyFromText' in pi and "m[1]==='-'" in pi,'portfolio negative money parsing regression')
check('rawUnits*1000' in pi,'portfolio lot-to-share conversion regression')

# SW must keep live data/network-sensitive code network-first.
for asset in ['stock-news.json','market-close.json','market-history.json','news-center.js','news-center.css','portfolio-intelligence.js']:
    check(asset in sw,f'service worker does not reference {asset}')

# JSON files must remain valid even if they are seed/empty data.
for name in ['stock-news.json','market-close.json','market-history.json','stock-directory.json','manifest.webmanifest']:
    try: json.loads(text(name))
    except Exception as e: errors.append(f'{name} invalid JSON: {e}')

if errors:
    print('frontend static selftest FAILED')
    for e in errors: print(' -',e)
    sys.exit(1)
print('frontend static selftest OK')
print(f'checked version {version}; critical functions={len(critical)}; tabs={len(tabs)}; periods=5')
