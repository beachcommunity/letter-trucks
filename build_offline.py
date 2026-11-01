"""Build the offline, installable version for an iPad or phone: dist/letter-trucks.html -> docs/ (served by GitHub Pages).
It puts the fonts inside the page, adds a manifest and icons so it can go on the home screen, and a service worker
that keeps a copy on the device, so the game opens with no internet (on a plane).
Usage: python3 build.py && python3 build_offline.py   (add --icons to redraw the home-screen icons; needs Playwright)"""
import base64, hashlib, json, os, re, sys
R = os.path.dirname(os.path.abspath(__file__)); D = f'{R}/docs'; F = f'{R}/tests/fonts'
os.makedirs(D, exist_ok=True)
b64 = lambda p: base64.b64encode(open(p, 'rb').read()).decode()
SKY = '#a4dcf3'

def fonts():
    face = lambda fam, f, w: f'@font-face{{font-family:"{fam}";src:url(data:font/woff2;base64,{b64(f"{F}/{f}")}) format("woff2");font-weight:{w};font-display:block}}'
    return '\n'.join([face('Fraunces', 'fraunces-latin-full-normal.woff2', '100 900')] +
                     [face('Schibsted Grotesk', f'schibsted-grotesk-latin-{w}-normal.woff2', w) for w in (400, 600, 800)])

# the game, without the web-font links (the fonts are inside the page now)
game = open(f'{R}/dist/letter-trucks.html').read()
game = re.sub(r'<link rel="(preconnect|stylesheet)" href="https://fonts\.[^"]*"[^>]*>\n?', '', game)
assert 'fonts.googleapis' not in game and 'fonts.gstatic' not in game

head = f'''<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover,user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Letter Trucks">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="{SKY}">
<link rel="manifest" href="manifest.webmanifest">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" href="icon-192.png">
<style>
:root{{color-scheme:light;box-sizing:border-box;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
html,body{{height:100%;margin:0;background:{SKY}}}body{{font:14px system-ui,-apple-system,sans-serif}}[hidden]{{display:none!important}}
.offline-note{{font:600 14px/1.3 "Schibsted Grotesk",system-ui,sans-serif;background:rgba(255,255,255,.85);color:#2f7d5b;padding:.35em .9em;border-radius:999px}}
{fonts()}
</style>
</head><body>
'''
# keep a copy on the device, and say so on the start screen once it's saved
tail = '''
<script>
(() => {
  if (!("serviceWorker" in navigator) || location.protocol === "file:") return;
  const note = () => {
    const card = document.querySelector(".start-card"); if (!card || card.querySelector(".offline-note")) return;
    const n = document.createElement("div"); n.className = "offline-note"; n.textContent = "\\u2713 Saved for playing without internet"; card.appendChild(n);
  };
  try { navigator.storage && navigator.storage.persist && navigator.storage.persist(); } catch (e) {}
  navigator.serviceWorker.register("sw.js").then(() => navigator.serviceWorker.ready)
    .then(() => caches.match("./")).then(r => { if (r) note(); }).catch(() => {});
})();
</script>
</body></html>
'''
page = head + game + tail
open(f'{D}/index.html', 'w').write(page)

ver = hashlib.sha1(page.encode()).hexdigest()[:10]
open(f'{D}/sw.js', 'w').write(f'''// keeps Letter Trucks on the device so it opens with no internet. The name changes with every build,
// so a new version replaces the old copy the next time the game is opened online.
const CACHE = "letter-trucks-{ver}";
const FILES = ["./", "manifest.webmanifest", "icon-180.png", "icon-192.png", "icon-512.png"];
self.addEventListener("install", e => {{ e.waitUntil(caches.open(CACHE).then(c => c.addAll(FILES)).then(() => self.skipWaiting())); }});
self.addEventListener("activate", e => {{
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("letter-trucks-") && k !== CACHE).map(k => caches.delete(k)))).then(() => self.clients.claim()));
}});
self.addEventListener("fetch", e => {{
  if (e.request.method !== "GET") return;
  // the page itself always comes from the saved copy; anything else from the copy if it's there
  if (e.request.mode === "navigate") {{ e.respondWith(caches.match("./").then(r => r || fetch(e.request))); return; }}
  e.respondWith(caches.match(e.request, {{ ignoreSearch: true }}).then(r => r || fetch(e.request)));
}});
''')
json.dump({'name': 'Letter Trucks', 'short_name': 'Letter Trucks', 'start_url': './', 'scope': './', 'display': 'standalone',
           'display_override': ['fullscreen', 'standalone'], 'background_color': SKY, 'theme_color': SKY,
           'icons': [{'src': f'icon-{s}.png', 'sizes': f'{s}x{s}', 'type': 'image/png', 'purpose': 'any'} for s in (180, 192, 512)]},
          open(f'{D}/manifest.webmanifest', 'w'), indent=1)
open(f'{D}/.nojekyll', 'w').write('')

# home-screen icons: the game's own bear on the sky, drawn with the game's code
if '--icons' in sys.argv or not os.path.exists(f'{D}/icon-512.png'):
    import asyncio
    from playwright.async_api import async_playwright
    t = open(f'{R}/src/template.html').read()
    grab = lambda a, b: t[t.index(a):t.index(b, t.index(a))]
    code = (grab('// the look: a flat pastel world', 'function glyph(') + grab('function shade(', '\n}\n') + '\n}\n' +
            grab('/* bears: sticker style', 'function drawHouse('))
    html = f'''<!doctype html><html><body style="margin:0"><canvas id="c" width="1024" height="1024"></canvas><script>
let ctx = document.getElementById("c").getContext("2d"), tNow = 0; const RM = true, P = null, BACK = 0, groundY = () => 0;
const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
function bearFace() {{ return {{}}; }}
{code}
const g = ctx.createLinearGradient(0, 0, 0, 1024); g.addColorStop(0, "#c8ecfa"); g.addColorStop(1, "#9fdcf5");
ctx.fillStyle = g; ctx.fillRect(0, 0, 1024, 1024);
ctx.fillStyle = "#aee096"; ctx.fillRect(0, 800, 1024, 224);
drawBearHead(512, 500, 4.4, "#c98a4b", false, {{}});
</script></body></html>'''
    async def icons():
        async with async_playwright() as p:
            b = await p.chromium.launch(); pg = await b.new_page(viewport={'width': 1024, 'height': 1024})
            await pg.set_content(html); await pg.wait_for_timeout(300)
            for s in (180, 192, 512):
                await pg.set_viewport_size({'width': 1024, 'height': 1024})
                await pg.evaluate(f'''(() => {{ const c = document.getElementById("c"), o = document.createElement("canvas"); o.width = o.height = {s};
                  o.getContext("2d").drawImage(c, 0, 0, {s}, {s}); o.id = "o{s}"; document.body.appendChild(o); }})()''')
                await (await pg.query_selector(f'#o{s}')).screenshot(path=f'{D}/icon-{s}.png')
            await b.close()
    asyncio.run(icons())
print('built docs/:', round(len(page) / 1024), 'KB page, cache', ver)
