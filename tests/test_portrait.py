import asyncio, json
from playwright.async_api import async_playwright
import test_v3 as T
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__)); _OUT = _os.path.join(_HERE, 'out')
_os.makedirs(_os.path.join(_OUT, 't'), exist_ok=True); _os.chdir(_OUT)
URL = 'file://' + _os.path.join(_HERE, 'index.html') + '#debug'

GEOM = '''(() => { const s = __lt.st; if (!s) return null;
  const pts = s.items.map(it => ({ l: it.l, ...__lt.screenOf(it.x, 770 - 64 - 110) }));
  const bear = s.m === "deliver" ? __lt.screenOf(s.bear.x, 770 - 64 - 250) : (s.big ? __lt.screenOf(s.big.x, 770 - 150) : null);
  const road = __lt.screenOf(0, 770);
  return { m: s.m, items: pts, bear, roadY: road.y, W: innerWidth, H: innerHeight };
})()'''

async def run(b, mode, vp, tag):
    pg = await b.new_page(viewport=vp, is_mobile=True, has_touch=True); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    await pg.add_init_script("try{localStorage.setItem('letter-trucks-v3', JSON.stringify({letters:'bdtp', stops:3, boxes:3, truck: 1}))}catch(e){}")
    await pg.goto(URL); await pg.wait_for_timeout(700)
    await pg.tap('#ov-start'); await pg.wait_for_timeout(900)
    await pg.tap(f'#btn-{mode}'); await T.pick(pg, 1, tap=True)
    # no controls on touch: the truck drives itself to the stop
    await T.wait_for(pg, '__lt.st && __lt.st.active', 20000)
    await T.wait_for(pg, '!__lt.P.auto', 15000); await pg.wait_for_timeout(600)
    await T.wait_for(pg, '!__lt.speaking', 15000); await pg.wait_for_timeout(900)
    g = await pg.evaluate(GEOM)
    await pg.screenshot(path=f't/{tag}-a.png')
    off = [i for i in g['items'] if i['x'] < 20 or i['x'] > g['W'] - 20]
    print(tag, 'items', [(i['l'], round(i['x']), round(i['y'])) for i in g['items']], 'bear/big', g['bear'] and (round(g['bear']['x']), round(g['bear']['y'])), 'road y', round(g['roadY']), 'H', g['H'])
    print(tag, 'offscreen items:', off, '| road below screen:', g['roadY'] > g['H'])
    # wrong pick by tapping it
    s = await pg.evaluate('({l: __lt.st.l, items: __lt.st.items.map(i => i.l)})')
    wrong = [x for x in s['items'] if x != s['l']][0]
    pos = [i for i in g['items'] if i['l'] == wrong][0]
    await pg.touchscreen.tap(pos['x'], pos['y'])
    await T.wait_for(pg, '__lt.st.misses >= 1', 8000); await pg.wait_for_timeout(700)
    await pg.screenshot(path=f't/{tag}-b-wrong.png')
    for _ in range(60):
        q = 0
        for _ in range(8):
            if await pg.evaluate('!__lt.st.busy && !__lt.speaking && __lt.locked <= 0'): q += 1
            await pg.wait_for_timeout(150)
        if q == 8: break
    g = await pg.evaluate(GEOM)
    pos = [i for i in g['items'] if i['l'] == s['l']][0]
    await pg.touchscreen.tap(pos['x'], pos['y'])
    await T.wait_for(pg, '__lt.st && __lt.st.payoff', 8000); await pg.wait_for_timeout(2600)
    await pg.screenshot(path=f't/{tag}-c-right.png')
    await pg.wait_for_timeout(1800)
    await pg.screenshot(path=f't/{tag}-d-right.png')
    ok = await T.wait_for(pg, '!__lt.st || __lt.st.done', 20000)
    print(tag, 'station done:', ok, 'errors', errs)
    await pg.close()

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        await run(b, 'tow', {'width': 390, 'height': 844}, 'pt-tow')
        await run(b, 'deliver', {'width': 390, 'height': 844}, 'pt-del')
        await run(b, 'tow', {'width': 844, 'height': 390}, 'ls-tow')
        await b.close()
asyncio.run(main())
