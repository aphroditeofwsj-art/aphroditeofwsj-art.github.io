"""把 pygbag 产出的 index.html 改成移动端友好（构建后处理，可重复执行）。

用法: python tools/mobile_patch.py web/build/web/index.html
"""
import re
import sys
from pathlib import Path

MARK = 'data-dsh-mobile'

HEAD_EXTRA = '''    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no, viewport-fit=cover" %s>
    <style id="dsh-mobile-style">
        html, body {
            margin: 0; padding: 0; width: 100%%; height: 100%%;
            background: #05050f !important; overflow: hidden;
            overscroll-behavior: none; touch-action: none;
            -webkit-user-select: none; user-select: none;
            -webkit-tap-highlight-color: transparent;
            -webkit-touch-callout: none;
        }
        /* 保持 16:9，多出来的地方留黑边，不要把画面拉变形 */
        body {
            display: flex; align-items: center; justify-content: center;
            position: fixed; inset: 0;
        }
        canvas.emscripten {
            position: relative !important;
            top: auto !important; left: auto !important; right: auto !important; bottom: auto !important;
            width: min(100vw, calc(100vh * 16 / 9)) !important;
            height: min(100vh, calc(100vw * 9 / 16)) !important;
            max-width: 100vw !important;
            max-height: 100vh !important;
            touch-action: none;
        }
        #rotate-hint {
            display: none;
            position: fixed; inset: 0; z-index: 9999999;
            background: #05050f; color: #e8e8f0;
            font: 500 18px/1.7 system-ui, "Microsoft YaHei", sans-serif;
            align-items: center; justify-content: center; text-align: center;
            padding: 24px;
        }
        @media (orientation: portrait) and (max-width: 900px) {
            #rotate-hint { display: flex; }
        }
    </style>
'''


def patch(path):
    p = Path(path)
    html = p.read_text(encoding='utf-8')
    if MARK in html:
        print('already patched:', p)
        return False

    # 1) viewport：合并成一条适合移动端、禁止缩放
    html = re.sub(r'[ \t]*<meta name="viewport"[^>]*>\s*', '', html)
    html = html.replace('<meta name="mobile-web-app-capable" content="yes">',
                        (HEAD_EXTRA % MARK) + '    <meta name="mobile-web-app-capable" content="yes">', 1)
    if MARK not in html:
        raise SystemExit('anchor for head injection not found')

    # 2) 浏览器端不需要媒体手势门槛（手机上第一次点击自然会解锁音频）
    html = html.replace('ume_block : 1,', 'ume_block : 0,')

    # 3) browserfs 用仓库里的本地副本，避免再依赖 CDN
    html = html.replace('https://pygame-web.github.io/cdn/0.9.3//browserfs.min.js', 'browserfs.min.js')

    # 4) 竖屏提示
    hint = ('<div id="rotate-hint">请把手机横过来游玩<br>'
            '<span style="font-size:14px;opacity:.6">Rotate your phone to landscape</span></div>\n')
    html = html.replace('<body>', '<body>\n' + hint, 1)

    p.write_text(html, encoding='utf-8')
    print('patched:', p)
    return True


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'web/build/web/index.html'
    patch(target)
