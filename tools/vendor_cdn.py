"""把 pygbag 运行时依赖从 pygame-web.github.io 下载到本地构建产物里（离线自包含）。

用法: python tools/vendor_cdn.py web/build/web
"""
import sys
import urllib.request
from pathlib import Path

BASE = 'https://pygame-web.github.io/cdn/'

FILES = [
    '0.9.3/pythons.js',
    '0.9.3/empty.html',
    '0.9.3/cpythonrc.py',
    '0.9.3/cpython312/main.js',
    '0.9.3/cpython312/main.data',
    '0.9.3/cpython312/main.wasm',
    'index-0.9.3-cp312.json',
    'cp312/pygame_ce-2.5.7-cp312-cp312-wasm32_bi_emscripten.whl',
    'vtx.js',
    'vt/xterm.css',
    'vt/xterm.js',
    'vt/xterm-addon-image.js',
]


def fetch(url, dest):
    if dest.exists() and dest.stat().st_size > 0:
        return 'cached'
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'dsh-vendor/1.0'})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    dest.write_bytes(data)
    return f'{len(data)/1024:.0f} KB'


TEXT_FILES = {'vtx.js', 'index-0.9.3-cp312.json'}
CDN_ABS = 'https://pygame-web.github.io/cdn/'


def rewrite_local_refs(dest):
    """把文件内部残留的 CDN 绝对地址改成站点根路径 /cdn/。

    - index-*.json 里的 "-CDN-" 会被运行库当作包前缀拼接
    - vtx.js 里的兜底地址同理
    站点部署在域名根目录，所以用 /cdn/ 这种绝对路径最稳。
    """
    if dest.name not in TEXT_FILES:
        return
    text = dest.read_text(encoding='utf-8')
    if CDN_ABS not in text:
        return
    dest.write_text(text.replace(CDN_ABS, '/cdn/'), encoding='utf-8')
    print(f'  rewrote CDN refs in cdn/{dest.name}')


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else 'web/build/web')
    cdn_dir = root / 'cdn'
    total = 0
    for rel in FILES:
        url = BASE + rel
        dest = cdn_dir / rel
        try:
            result = fetch(url, dest)
            if dest.exists():
                total += dest.stat().st_size
            print(f'  {result:>10}  cdn/{rel}')
            rewrite_local_refs(dest)
        except Exception as e:
            print(f'  FAILED     cdn/{rel}  ({e})')
    print(f'\nvendored into {cdn_dir}  ({total/1024/1024:.2f} MB)')


if __name__ == '__main__':
    main()
