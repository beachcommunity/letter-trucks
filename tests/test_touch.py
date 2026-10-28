import asyncio
from playwright.async_api import async_playwright
import test_v3 as T
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__)); _OUT = _os.path.join(_HERE, 'out')
_os.makedirs(_os.path.join(_OUT, 't'), exist_ok=True); _os.chdir(_OUT)
URL = 'file://' + _os.path.join(_HERE, 'index.html') + '#debug'
# a box's spot on screen (deliver boxes sit on the dock, trailers on the road)
SPOT = '''(l => { const s = __lt.st, it = s.items.find(i => i.l === l);
  return __lt.screenOf(it.x, s.m === "deliver" ? __lt.dockY(s) - 62 : 770 - 110); })'''
async def settle(pg):
    for _ in range(80):
        q = 0
        for _ in range(6):
            if await pg.evaluate('__lt.st && !__lt.st.busy && !__lt.speaking && __lt.locked <= 0 && !__lt.P.auto'): q += 1
            await pg.wait_for_timeout(120)
        if q == 6: return True
    return False
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        pg = await b.new_page(viewport={'width': 844, 'height': 390}, has_touch=True, is_mobile=True); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script("try{localStorage.setItem('letter-trucks-v3', JSON.stringify({letters:'bksm', stops:3, boxes:3}))}catch(e){}")
        await pg.goto(URL); await pg.wait_for_timeout(600)
        await pg.tap('#ov-start'); await pg.wait_for_timeout(800); await pg.tap('#btn-deliver'); await pg.wait_for_timeout(1200); await T.pick(pg, 0, tap=True)
        print('touch buttons in page:', await pg.evaluate("document.querySelectorAll('#touch, .tbtn').length"))
        await T.wait_for(pg, '!__lt.speaking', 10000)
        x0 = await pg.evaluate('__lt.P.x'); await pg.wait_for_timeout(1200); x1 = await pg.evaluate('__lt.P.x')
        print('drives by itself (no input):', x1 > x0 + 200, round(x0), '->', round(x1))
        await pg.screenshot(path='t/60-drive.png')
        for n in range(3):
            if not await T.wait_for(pg, '__lt.st && __lt.st.active', 30000): print('never reached stop', n); break
            ok = await settle(pg)
            px = await pg.evaluate('__lt.P.x'); await pg.wait_for_timeout(800)
            print(f'stop {n}: settled {ok}, truck holds still at the stop:', abs(await pg.evaluate('__lt.P.x') - px) < 1)
            s = await pg.evaluate('({l: __lt.st.l, items: __lt.st.items.map(i => i.l)})')
            wrong = [x for x in s['items'] if x != s['l']][0]
            if n == 0: await pg.screenshot(path='t/61-stop.png')
            pos = await pg.evaluate(SPOT + f'("{wrong}")'); await pg.touchscreen.tap(pos['x'], pos['y'])
            await T.wait_for(pg, '__lt.st.misses >= 1', 8000); await pg.wait_for_timeout(200)
            if n == 0: await pg.screenshot(path='t/62-wrong.png')
            st = await pg.evaluate(f'__lt.st.items.find(i => i.l === "{wrong}").state')
            print(f'stop {n}: wrong tap {wrong} -> box stays put ({st})')
            await settle(pg)
            pos = await pg.evaluate(SPOT + f'("{s["l"]}")'); await pg.touchscreen.tap(pos['x'], pos['y'])
            done = await T.wait_for(pg, '!__lt.st || __lt.st.done', 30000)
            print(f'stop {n}: right tap {s["l"]} -> done {done}')
        print('run ended:', await T.wait_for(pg, '__lt.mode === "end"', 30000))
        print('errors', errs); await b.close()
if __name__ == '__main__':
    asyncio.run(main())
