import asyncio
from playwright.async_api import async_playwright
import test_v3 as T
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__)); _OUT = _os.path.join(_HERE, 'out')
_os.makedirs(_os.path.join(_OUT, 't'), exist_ok=True); _os.chdir(_OUT)
URL = 'file://' + _os.path.join(_HERE, 'index.html') + '#debug'
VIS = "['t-left','t-right','t-jump','t-honk','t-grab'].filter(id => !document.getElementById(id).classList.contains('gone')).map(id => id.slice(2)).join(',') || '(none)'"
async def wait_for(pg, expr, timeout=20000):
    t = 0
    while t < timeout:
        if await pg.evaluate(expr): return True
        await pg.wait_for_timeout(100); t += 100
    return False
async def tap(pg, id):
    await pg.evaluate(f"(() => {{ const el = document.getElementById('{id}'); el.dispatchEvent(new PointerEvent('pointerdown', {{bubbles:true, pointerType:'touch'}})); el.dispatchEvent(new PointerEvent('pointerup', {{bubbles:true, pointerType:'touch'}})); }})()")
async def hold(pg, id, on):
    await pg.evaluate(f"document.getElementById('{id}').dispatchEvent(new PointerEvent('{'pointerdown' if on else 'pointerup'}', {{bubbles:true, pointerType:'touch'}}))")
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        pg = await b.new_page(viewport={'width': 1180, 'height': 820}, has_touch=True, is_mobile=True); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(600)
        await pg.tap('#ov-start'); await pg.wait_for_timeout(800); await pg.tap('#btn-deliver'); await pg.wait_for_timeout(1200); await T.pick(pg, 0, tap=True)
        print('driving:', await pg.evaluate(VIS)); await pg.screenshot(path='t/60-drive.png')
        await hold(pg, 't-right', True)
        await wait_for(pg, '__lt.st && __lt.st.active'); await pg.wait_for_timeout(300)
        print('rolling up to the stop:', await pg.evaluate(VIS))
        await hold(pg, 't-right', False)
        await wait_for(pg, '__lt.speaking', 8000); await pg.wait_for_timeout(500)
        print('bear asking (speaking=%s):' % await pg.evaluate('__lt.speaking'), await pg.evaluate(VIS)); await pg.screenshot(path='t/61-bear-asking.png')
        await wait_for(pg, '!__lt.speaking'); await pg.wait_for_timeout(300)
        print('stop, not under a box:', await pg.evaluate(VIS), '| selected:', await pg.evaluate('__lt.sel() && __lt.sel().l'))
        # drive under the first box
        await hold(pg, 't-right', True)
        await wait_for(pg, '!!__lt.sel()', 10000); await hold(pg, 't-right', False); await pg.wait_for_timeout(500)
        print('under a box (%s):' % await pg.evaluate('__lt.sel() && __lt.sel().l'), await pg.evaluate(VIS)); await pg.screenshot(path='t/62-under-box.png')
        right = await pg.evaluate('__lt.sel().l === __lt.st.l')
        await tap(pg, 't-grab'); await pg.wait_for_timeout(500)
        print('after pick (%s):' % ('right' if right else 'wrong'), await pg.evaluate(VIS)); await pg.screenshot(path='t/63-after-pick.png')
        await wait_for(pg, '!__lt.st || __lt.st.done || (!__lt.st.busy && !__lt.speaking)', 30000); await pg.wait_for_timeout(300)
        print('after that settles:', await pg.evaluate(VIS))
        print('errors', errs); await b.close()
asyncio.run(main())
