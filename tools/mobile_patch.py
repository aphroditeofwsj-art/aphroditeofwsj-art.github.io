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
            font: 500 17px/1.7 system-ui, "PingFang SC", "Microsoft YaHei", sans-serif;
            padding: 28px; box-sizing: border-box;
        }
        #rotate-hint[data-dismissed="1"] { display: none !important; }
        #rotate-hint .rh-inner {
            position: absolute; top: 50%%; left: 50%%; transform: translate(-50%%, -50%%);
            width: 100%%; max-width: 420px; text-align: center;
        }
        #rotate-hint .rh-title { font-size: 22px; font-weight: 700; margin-bottom: 6px; }
        #rotate-hint .rh-sub { font-size: 13px; opacity: .55; margin-bottom: 22px; }
        #rotate-hint .rh-wx {
            display: none; font-size: 15px; line-height: 1.9;
            background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.14);
            border-radius: 12px; padding: 14px 16px; margin-bottom: 20px; text-align: left;
        }
        #rotate-hint .rh-wx b { color: #ffd75e; }
        #rotate-hint .rh-btn {
            font: 15px system-ui, "PingFang SC", "Microsoft YaHei", sans-serif;
            color: #d8d8e4; background: transparent; cursor: pointer;
            border: 1px solid rgba(255,255,255,.25); border-radius: 999px;
            padding: 9px 20px;
        }
        @media (orientation: portrait) and (max-width: 999px) {
            #rotate-hint { display: block; }
        }
        /* 加载页：pygbag 默认是绿底蓝字，太扎眼，改成和游戏一致的暗色 */
        #infobox {
            background: transparent !important;
            color: #c9cde0 !important;
            font: 500 15px/1.7 system-ui, "PingFang SC", "Microsoft YaHei", sans-serif !important;
            text-align: center !important;
        }
        #status {
            color: #7f8499 !important;
            font: 400 13px system-ui, "PingFang SC", "Microsoft YaHei", sans-serif !important;
            margin-left: 0 !important;
        }
        #progress {
            height: 4px !important;
            width: 240px !important;
            margin: 10px auto 0 !important;
            display: block;
            accent-color: #ffd75e;
            border-radius: 2px;
        }
    </style>
'''

HINT_HTML = '''<div id="rotate-hint">
    <div class="rh-inner">
        <div class="rh-title">请把手机横过来游玩</div>
        <div class="rh-sub">Rotate your phone to landscape</div>
        <div class="rh-wx" id="rh-wx">
            微信里不会跟着重力感应转屏：<br>
            点右上角 <b>···</b> → <b>在浏览器打开</b><br>
            用系统浏览器打开后横屏即可。
        </div>
        <button class="rh-btn" id="rh-skip">仍然竖屏玩（画面会很小）</button>
    </div>
</div>
'''

HINT_JS = '''<script id="dsh-mobile-script">
(function () {
    var hint = document.getElementById('rotate-hint');
    if (!hint) return;
    var ua = (navigator.userAgent || '').toLowerCase();
    var wx = document.getElementById('rh-wx');
    if (wx && (ua.indexOf('micromessenger') !== -1 || ua.indexOf('weibo') !== -1)) {
        wx.style.display = 'block';
    }
    var skip = document.getElementById('rh-skip');
    if (skip) {
        skip.addEventListener('click', function (e) {
            e.preventDefault();
            hint.setAttribute('data-dismissed', '1');
        });
    }
})();
</script>
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

    # 4) 竖屏提示 + 微信引导
    html = html.replace('<body>', '<body>\n' + HINT_HTML, 1)
    html = html.replace('</body>', HINT_JS + '</body>', 1)

    p.write_text(html, encoding='utf-8')
    print('patched:', p)
    return True


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else 'web/build/web/index.html'
    patch(target)
