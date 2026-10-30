import asyncio, sys
from playwright.async_api import async_playwright
import test_v3 as T
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__)); _OUT = _os.path.join(_HERE, 'out')
_os.makedirs(_os.path.join(_OUT, 't'), exist_ok=True); _os.chdir(_OUT)
URL = 'file://' + _os.path.join(_HERE, 'index.html') + '#debug'
# a box's or trailer's spot on screen (deliver boxes sit on the dock, trailers behind the road)
SPOT = '''(l => { const s = __lt.st, it = s.items.find(i => i.l === l);
  return __lt.screenOf(it.x, s.m === "deliver" ? __lt.dockY(s) - 62 : __lt.gy(it.x) - 64 - 110); })'''
# an empty patch of road ahead of the truck, to press and hold on
ROAD = '(() => { const x = __lt.P.x + 300; const q = __lt.screenOf(x, __lt.gy(x) + 120); q.x = Math.min(q.x, innerWidth - 20); return q; })()'
TRUCK = '__lt.screenOf(__lt.P.x, __lt.P.y - 90)'
async def settle(pg):
    for _ in range(80):
        q = 0
        for _ in range(6):
            if await pg.evaluate('__lt.st && !__lt.st.busy && !__lt.speaking && __lt.locked <= 0 && !__lt.P.auto'): q += 1
            await pg.wait_for_timeout(120)
        if q == 6: return True
    return False
async def drive_until(pg, cond, timeout=25000):
    # press and hold on the road; lift and press again now and then, like a kid would
    t = 0
    while t < timeout:
        if await pg.evaluate(cond): return True
        pos = await pg.evaluate(ROAD)
        await pg.mouse.move(pos['x'], pos['y']); await pg.mouse.down()
        for _ in range(10):
            await pg.wait_for_timeout(100); t += 100
            if await pg.evaluate(cond): break
        await pg.mouse.up()
    return await pg.evaluate(cond)
async def tap(pg, pos): await pg.mouse.click(pos['x'], pos['y'])
async def play(pg, mode, n, shots):
    for i in range(n):
        if not await drive_until(pg, '__lt.st && __lt.st.active && __lt.st.phase === "pick"'): print(mode, i, 'never got to the loading spot', await pg.evaluate('({x: __lt.P.x, st: __lt.st && __lt.st.phase})')); return False
        await settle(pg)
        s = await pg.evaluate('({l: __lt.st.l, items: __lt.st.items.map(i => i.l)})')
        if shots and i == 0: await pg.screenshot(path=f't/{shots}-1-pick.png')
        held = await pg.evaluate('__lt.P.x'); await pg.mouse.move(*(lambda p: (p['x'], p['y']))(await pg.evaluate(ROAD))); await pg.mouse.down(); await pg.wait_for_timeout(700); await pg.mouse.up()
        print(f'{mode} {i}: parked at the loading spot, holding does not drive past it:', abs(await pg.evaluate('__lt.P.x') - held) < 6)
        wrong = [x for x in s['items'] if x != s['l']][0]
        await tap(pg, await pg.evaluate(SPOT + f'("{wrong}")'))
        await T.wait_for(pg, '__lt.st.misses >= 1', 8000)
        print(f'{mode} {i}: wrong tap {wrong} -> still picking:', await pg.evaluate('__lt.st.phase'))
        await settle(pg)
        await tap(pg, await pg.evaluate(SPOT + f'("{s["l"]}")'))
        if shots and i == 0: await pg.wait_for_timeout(900 if mode == 'deliver' else 300); await pg.screenshot(path=f't/{shots}-2-load.png')
        ok = await T.wait_for(pg, '__lt.st.phase === "carry"', 12000)
        print(f'{mode} {i}: right tap {s["l"]} -> loaded:', ok)
        if not await drive_until(pg, '__lt.st.phase === "give"'): print(mode, i, 'never got to the customer'); return False
        await pg.wait_for_timeout(400)
        if shots and i == 0: await pg.screenshot(path=f't/{shots}-3-give.png')
        await tap(pg, await pg.evaluate(TRUCK))
        await pg.wait_for_timeout(900)
        if shots and i == 0: await pg.screenshot(path=f't/{shots}-4-payoff.png')
        done = await T.wait_for(pg, '!__lt.st || __lt.st.done', 30000)
        print(f'{mode} {i}: handed over -> done:', done)
    return True
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        for mode, vp, tag in [('deliver', {'width': 844, 'height': 390}, '60'), ('tow', {'width': 844, 'height': 390}, '65')]:
            pg = await b.new_page(viewport=vp, has_touch=True, is_mobile=True); errs = []
            pg.on('pageerror', lambda e: errs.append(str(e)))
            await pg.add_init_script("try{localStorage.setItem('letter-trucks-v3', JSON.stringify({letters:'bksm', stops:2, boxes:3, sets:2}))}catch(e){}")
            await pg.goto(URL); await pg.wait_for_timeout(600)
            await pg.tap('#ov-start'); await pg.wait_for_timeout(800); await pg.tap(f'#btn-{mode}'); await pg.wait_for_timeout(1200); await T.pick(pg, 0, tap=True)
            print(mode, 'touch buttons in page:', await pg.evaluate("document.querySelectorAll('#touch, .tbtn').length"))
            await T.wait_for(pg, '!__lt.speaking', 10000)
            x0 = await pg.evaluate('__lt.P.x'); await pg.wait_for_timeout(1500); x1 = await pg.evaluate('__lt.P.x')
            print(mode, 'stays put until he drives:', abs(x1 - x0) < 2)
            await pg.wait_for_timeout(2000); print(mode, 'hint hand after a while (screenshot)'); await pg.screenshot(path=f't/{tag}-0-hint.png')
            # real touch events (like a phone): a quick tap scoots a little and stops; holding drives and
            # lifting the finger stops the truck
            cdp = await pg.context.new_cdp_session(pg)
            async def touch(kind, pos=None): await cdp.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': [{'x': pos['x'], 'y': pos['y']}] if pos else []})
            pos = await pg.evaluate(ROAD); x0 = await pg.evaluate('__lt.P.x')
            await touch('touchStart', pos); await pg.wait_for_timeout(80); await touch('touchEnd')
            await pg.wait_for_timeout(1800); x1 = await pg.evaluate('__lt.P.x'); v1 = await pg.evaluate('__lt.P.vx')
            print(mode, f'quick tap scoots a little and stops: moved {round(x1 - x0)}, still moving {round(v1)}', 'OK' if 100 < x1 - x0 < 600 and v1 == 0 else 'WRONG')
            pos = await pg.evaluate(ROAD)
            await touch('touchStart', pos); await pg.wait_for_timeout(1200); v2 = await pg.evaluate('__lt.P.vx'); await touch('touchEnd')
            await pg.wait_for_timeout(1000); v3 = await pg.evaluate('__lt.P.vx')
            print(mode, f'holding drives ({round(v2)}), letting go stops it ({round(v3)})', 'OK' if v2 > 200 and v3 == 0 else 'WRONG')
            await play(pg, mode, 2, tag)
            print(mode, 'run ended:', await T.wait_for(pg, '__lt.mode === "end"', 30000))
            print('errors', errs); await pg.close()
        await b.close()
if __name__ == '__main__':
    asyncio.run(main())
