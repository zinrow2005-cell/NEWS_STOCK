#!/usr/bin/env python3
"""Create a reproducible ready-to-upload GitHub Pages ZIP from this folder."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
VERSION = re.search(r'v\d+\.\d+\.\d+', (ROOT/'VERSION.txt').read_text(encoding='utf-8'))
if not VERSION: raise SystemExit('VERSION.txt 找不到版本號')
OUTPUT = ROOT.parent / f'NEWS_STOCK-{VERSION.group(0)}-COMPLETE-GITHUB.zip'

subprocess.run([sys.executable, str(ROOT/'scripts/check_release.py')],check=False)  # First pass may have prior checksum manifest
SKIP_DIRS = {'.git', '__pycache__', '.pytest_cache', '.mypy_cache', 'node_modules'}
def ignored(path):
    rel=path.relative_to(ROOT)
    if any(part in SKIP_DIRS for part in rel.parts):return True
    if any(part=='__pycache__' for part in rel.parts):return True
    if path.suffix.lower() in ('.pyc','.pyo','.log','.zip'):return True
    if path.name in ('.DS_Store','Thumbs.db'):return True
    return False
files=sorted((f for f in ROOT.rglob('*') if f.is_file() and not ignored(f)),key=lambda f:f.relative_to(ROOT).as_posix())
checksums=[]
for f in files:
    if f.name=='SHA256SUMS.txt': continue
    checksums.append(f'{hashlib.sha256(f.read_bytes()).hexdigest()}  {f.relative_to(ROOT).as_posix()}')
(ROOT/'SHA256SUMS.txt').write_text('\n'.join(checksums)+'\n',encoding='utf-8')
# Revalidate after regenerating the manifest.
subprocess.run([sys.executable, str(ROOT/'scripts/check_release.py')],check=True)
with ZipFile(OUTPUT,'w',ZIP_DEFLATED,compresslevel=9) as z:
    for f in files:z.write(f,f.relative_to(ROOT).as_posix())
print(f'RELEASE: {OUTPUT}\nfiles={len(files)}  bytes={OUTPUT.stat().st_size:,}')
