from pathlib import Path
import hashlib, html, json, os, re, shutil
from urllib.parse import quote
import markdown

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'website' / 'dist'
BASE = 'https://tools.minmin11538.cn/notehelper/'
ZIP = '敏敏·收藏创作助手-v0.9.7.zip'
EXPECTED = '4cf4056e8aec0360617ac6a6a4a95a45c4e32ee453649c77e9bf73a9adabe3bc'
assert hashlib.sha256((ROOT / 'downloads' / ZIP).read_bytes()).hexdigest() == EXPECTED
OUT.mkdir(exist_ok=True)
for name in ['index.html', 'styles.css', 'shared-header.css']:
    if name == 'index.html':
        page = (ROOT / 'website' / name).read_text()
        page = re.sub(r'(<code class="digest">)[a-f0-9]{64}(</code>)', lambda m: m[1] + EXPECTED + m[2], page)
        (OUT / name).write_text(page)
    else:
        shutil.copyfile(ROOT / 'website' / name, OUT / name)
for name in ['downloads', 'minmin-collect-create', 'contact']:
    shutil.copytree(ROOT / name, OUT / name, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
shutil.copyfile(ROOT / '发给Agent的启动说明.md', OUT / '发给Agent的启动说明.md')

def rewrite(source, destination, text, html_links=True):
    def link(m):
        target = m.group(1)
        if '://' in target or target.startswith('#'):
            return m.group(0)
        raw, sep, anchor = target.partition('#')
        resolved = (source.parent / raw).resolve()
        if not resolved.is_relative_to(ROOT) or not resolved.exists():
            return m.group(0)
        copied = OUT / resolved.relative_to(ROOT)
        if html_links and copied.suffix == '.md':
            copied = copied.with_suffix('.html')
        relative = os.path.relpath(copied, destination.parent)
        return '](' + quote(relative, safe='/') + (sep + anchor if sep else '') + ')'
    return re.sub(r'\]\(([^)]+)\)', link, text)

def render(source, destination):
    source_text = source.read_text()
    source_text = re.sub(r'\A---\n.*?\n---\n', '', source_text, count=1, flags=re.S)
    body = markdown.markdown(rewrite(source, destination, source_text), extensions=['fenced_code', 'tables', 'sane_lists'])
    stylesheet = quote(os.path.relpath(OUT / 'styles.css', destination.parent), safe='/')
    home = quote(os.path.relpath(OUT / 'index.html', destination.parent), safe='/')
    title = next((line.lstrip('# ') for line in source_text.splitlines() if line.startswith('# ')), source.stem)
    page = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(title)}｜敏敏·收藏创作助手</title><link rel="stylesheet" href="{stylesheet}"></head><body><header class="site-header"><a class="brand" href="{home}">敏敏 <span>/ 收藏创作助手</span></a><a href="{home}">返回下载页</a></header><main class="guide">{body}</main></body></html>'''
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(page)

for source in (ROOT / 'minmin-collect-create').rglob('*.md'):
    render(source, (OUT / source.relative_to(ROOT)).with_suffix('.html'))
startup = ROOT / '发给Agent的启动说明.md'
render(startup, OUT / '发给Agent的启动说明.html')
manual = ROOT / 'minmin-collect-create/references/grouped-messages.md'
render(manual, OUT / 'guide.html')
render(ROOT / 'minmin-collect-create/references/sources.md', OUT / 'sources.html')
(OUT / 'guide.md').write_text(rewrite(manual, OUT / 'guide.md', manual.read_text(), html_links=False))
release = {'version': '0.9.7', 'download_url': BASE + 'downloads/' + quote(ZIP), 'bytes': (ROOT / 'downloads' / ZIP).stat().st_size, 'sha256': EXPECTED, 'archive_root': '敏敏·收藏创作助手', 'skill_entry': 'minmin-collect-create/SKILL.md', 'guide_url': BASE + 'guide.html', 'instructions_url': BASE + 'install.md', 'released_at': '2026-11-02'}
(OUT / 'release.json').write_text(json.dumps(release, ensure_ascii=False, indent=2) + '\n')
shutil.copyfile(ROOT / 'website' / 'install.md', OUT / 'install.md')
# Preserve previously shared documentation links.
shutil.copytree(OUT / 'minmin-collect-create', OUT / 'notebook-feishu-onboarding', dirs_exist_ok=True)
manifest = {str(p.relative_to(OUT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.rglob('*')) if p.is_file() and p.name != 'files.sha256.json'}
(OUT / 'files.sha256.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'directory': str(OUT), 'files': len(manifest)+1, 'zip_sha256': EXPECTED}, ensure_ascii=False))
