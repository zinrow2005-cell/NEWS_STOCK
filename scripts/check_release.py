#!/usr/bin/env python3
"""Verify the self-contained GitHub Pages release without external services."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = [
    'index.html', '404.html', 'offline.html', '.nojekyll',
    'assets/app.js', 'assets/app-core.css', 'assets/app-overrides.css',
    'news-center.js', 'news-center.css',
    'portfolio-intelligence.js', 'portfolio-intelligence.css',
    'manifest.webmanifest', 'service-worker.js',
    'stock-directory.json', 'stock-news.json', 'market-close.json', 'market-history.json',
    'icon-192.png', 'icon-512.png', 'icon-maskable-512.png', 'apple-touch-icon.png',
    '.github/workflows/update-stock-news.yml', '.github/workflows/update-market-close.yml',
    'scripts/update_market_close.py', 'scripts/update_stock_news.py',
    'README.md', 'CHANGELOG.md', 'VERSION.txt', 'SHA256SUMS.txt',
    'tests/test_breakeven.cjs',
]

class Refs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.refs = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        key = 'src' if tag == 'script' else 'href' if tag == 'link' else None
        if key and a.get(key): self.refs.append(a[key])

errors = []
for name in REQUIRED:
    if not (ROOT / name).is_file(): errors.append('缺少檔案：' + name)

if not errors:
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    if html != (ROOT / '404.html').read_text(encoding='utf-8'):
        errors.append('入口頁與 404.html 不一致')
    parser = Refs(); parser.feed(html)
    for ref in parser.refs:
        if ref.startswith(('http:', 'https:', 'data:', '#', '/')): continue
        file = ROOT / ref.split('?', 1)[0].removeprefix('./')
        if not file.exists(): errors.append('網頁引用的檔案不存在：' + ref)
    expected_css = ['assets/app-core.css','news-center.css','portfolio-intelligence.css','assets/app-overrides.css']
    css_positions = [html.find(f'"./{f}"') for f in expected_css]
    if -1 in css_positions or css_positions != sorted(css_positions):
        errors.append('CSS 載入順序錯誤')
    expected_scripts = ['assets/app.js', 'news-center.js', 'portfolio-intelligence.js']
    positions = [html.find(f'"./{f}"') for f in expected_scripts]
    if -1 in positions or positions != sorted(positions):
        errors.append('JavaScript 載入順序錯誤')
    if '<script>var e=Object.create' in html:
        errors.append('HTML 還包含原始 2MB 重複 bundle')
    if any((ROOT / 'assets').glob('index-*.js')) or any((ROOT / 'assets').glob('index-*.css')):
        errors.append('assets 內仍含未使用的舊建置輸出')
    if 'v4.7.29' not in html or 'v4.7.29' not in (ROOT / 'VERSION.txt').read_text():
        errors.append('顯示版本未更新到 v4.7.29')
    worker = (ROOT / 'service-worker.js').read_text(encoding='utf-8')
    for name in expected_css + ['assets/app.js']:
        if f'appPath("{name}")' not in worker: errors.append('PWA 缺少資源：'+name)
    if 'news-v47.29' not in worker:errors.append('PWA 快取版本未更新')
    for name in ['stock-directory.json','stock-news.json','market-close.json','market-history.json','manifest.webmanifest']:
        try: json.loads((ROOT/name).read_text(encoding='utf-8'))
        except Exception as exc: errors.append(f'{name} JSON 解析失敗：{exc}')
    manifest=json.loads((ROOT/'manifest.webmanifest').read_text())
    for icon in manifest.get('icons',[]):
        if not (ROOT/icon.get('src','')).is_file():errors.append('圖示缺少：'+str(icon))
    if shutil.which('node'):
        for file in ['assets/app.js', 'news-center.js', 'portfolio-intelligence.js', 'service-worker.js','tests/test_breakeven.cjs']:
            cp=subprocess.run(['node','--check',str(ROOT/file)],capture_output=True,text=True)
            if cp.returncode:errors.append(f'JavaScript 語法：{file}: {cp.stderr.strip()[:250]}')
        cp=subprocess.run(['node',str(ROOT/'tests/test_breakeven.cjs')],capture_output=True,text=True)
        if cp.returncode:errors.append('持股運算測試失敗：'+cp.stderr.strip()[:400])
        else:print(cp.stdout.strip())
    else:print('提示：無 Node.js，略過 JS 語法及含息回本價測試')

if errors:
    print('FAIL — 檔案檢核發現問題')
    for e in errors:print(' -',e)
    sys.exit(1)
print(f'PASS — 靜態網站檢核成功，檢查 {len(REQUIRED)} 個必要檔案，HTML / CSS / PWA / JSON 相容。')
