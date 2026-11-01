"""The offline version (docs/, built by build_offline.py): open it once online, then with the network off it
still opens, has its fonts and plays."""
import asyncio, functools, http.server, os, threading
from playwright.async_api import async_playwright
_HERE = os.path.dirname(os.path.abspath(__file__)); DOCS = os.path.join(os.path.dirname(_HERE), 'docs')
os.makedirs(os.path.join(_HERE, 'out', 't'), exist_ok=True)
def serve():
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DOCS)
    h.log_message = lambda *a: None
    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv
async def wait_for(pg, expr, timeout=20000):
    for _ in range(timeout // 200):
        if await pg.evaluate(expr): return True
        await pg.wait_for_timeout(200)
    return False
async def main():
    srv = serve(); url = f'http://127.0.0.1:{srv.server_address[1]}/'
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        ctx = await b.new_context(viewport={'width': 1180, 'height': 820}, has_touch=True); errs = []
        pg = await ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(url)
        saved = await wait_for(pg, '!!document.querySelector(".offline-note")')
        print('online: saved for offline, note on the start screen:', saved)
        print('manifest and icons:', await pg.evaluate('''Promise.all(["manifest.webmanifest", "icon-180.png", "icon-512.png"].map(u => fetch(u).then(r => r.ok))).then(a => a.every(Boolean))'''))
        await ctx.set_offline(True); srv.shutdown()
        await pg.reload(); await pg.wait_for_timeout(1500)
        print('offline: page opens:', await pg.evaluate('!!document.querySelector("#ov-start") && !document.querySelector("#ov-start").hidden'))
        print('offline: fonts inside the page:', await pg.evaluate('document.fonts.check(\'900 40px "Fraunces"\') && document.fonts.check(\'800 20px "Schibsted Grotesk"\')'))
        print('offline: no web font links left:', await pg.evaluate('!document.querySelector("link[href*=googleapis]")'))
        await pg.screenshot(path=os.path.join(_HERE, 'out', 't', '80-offline-start.png'))
        await pg.tap('#ov-start'); await pg.wait_for_timeout(800); await pg.tap('#btn-deliver'); await pg.wait_for_timeout(1200)
        await pg.tap('#truck-choices .truck-btn >> nth=0'); await pg.wait_for_timeout(2500)
        # press and hold on the grass to drive for a second
        await pg.mouse.move(800, 760); await pg.mouse.down(); await pg.wait_for_timeout(1500); await pg.mouse.up(); await pg.wait_for_timeout(300)
        await pg.screenshot(path=os.path.join(_HERE, 'out', 't', '81-offline-playing.png'))
        print('offline: playing (a game is running):', await pg.evaluate('!document.getElementById("ov-pick").hidden === false && !document.getElementById("ov-home").hidden === false'))
        print('errors', errs); await b.close()
asyncio.run(main())
