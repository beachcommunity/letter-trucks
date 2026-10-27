import asyncio, io
from playwright.async_api import async_playwright
from PIL import Image
import test_v3 as T
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__)); _OUT = _os.path.join(_HERE, 'out')
_os.makedirs(_os.path.join(_OUT, 't'), exist_ok=True); _os.chdir(_OUT)
URL = 'file://' + _os.path.join(_HERE, 'index.html') + '#debug'

async def poke_all(pg, tag):
    out = {}
    t0 = await pg.evaluate('__lt.tNow()')
    # sun: find its colour in the top right of the screen
    im = Image.open(io.BytesIO(await pg.screenshot(path=f't/p-{tag}-0.png'))).convert('RGB'); px = im.load()
    xs = [(x, y) for x in range(im.width // 2, im.width, 2) for y in range(0, im.height // 2, 2) if px[x, y] == (255, 226, 122)]
    if xs:
        await pg.mouse.click(sum(a for a, _ in xs) / len(xs), sum(b for _, b in xs) / len(xs)); await pg.wait_for_timeout(250)
        out['sun'] = (await pg.evaluate('__lt.sunPoke')) >= t0
    else: out['sun'] = 'not found'
    c = await pg.evaluate('''(() => { const dpr = document.getElementById("world").width / innerWidth; for (let i = 0; i < 5; i++) { const p = __lt.cloudPos(i); if (p.x > 70 * dpr && p.x < (innerWidth - 70) * dpr) return { i, x: p.x / dpr, y: p.y / dpr }; } return null; })()''')
    if c:
        await pg.mouse.click(c['x'], c['y']); await pg.wait_for_timeout(700)
        out['cloud'] = await pg.evaluate(f'__lt.cloudRain[{c["i"]}] > __lt.tNow()')
    await pg.screenshot(path=f't/p-{tag}-1.png')
    for kind, yo, xo, key in (('tree', 112, 0, 'shake'), ('bush', 28, 8, 'shake'), ('flower', 44, 0, 'pop')):
        p = await pg.evaluate(f'''(() => {{ for (let i = 0; i < __lt.decor.length; i++) {{ const d = __lt.decor[i]; if (d.kind !== "{kind}") continue;
            const q = __lt.screenOf(d.x + {xo} * d.s, __lt.gy(d.x) - 112 - {yo} * d.s); if (q.x < 40 || q.x > innerWidth - 40 || q.y < 60) continue; if (document.elementFromPoint(q.x, q.y) !== document.getElementById('world')) continue; return {{ i, ...q }}; }} return null; }})()''')
        if not p: out[kind] = 'none on screen'; continue
        await pg.mouse.click(p['x'], p['y']); await pg.wait_for_timeout(200)
        out[kind] = await pg.evaluate(f'(__lt.decor[{p["i"]}].{key} || 0) >= {t0}')
        if not out[kind]: print('  miss', kind, p, await pg.evaluate(f'''({{hit: document.elementFromPoint({p["x"]}, {p["y"]}).id || document.elementFromPoint({p["x"]}, {p["y"]}).className, honk: __lt.P.honk, truck: __lt.screenOf(__lt.P.x, __lt.P.y), others: __lt.decor.map((d, i) => [i, d.kind, (d.shake||0) >= {t0} || (d.pop||0) >= {t0}]).filter(a => a[2])}})'''))
    await pg.wait_for_timeout(200)
    await pg.screenshot(path=f't/p-{tag}-2.png')
    return out

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        errs = []
        for tag, vp, mob in [('desk', {'width': 1280, 'height': 720}, False), ('phone', {'width': 390, 'height': 844}, True)]:
            pg = await b.new_page(viewport=vp, is_mobile=mob, has_touch=mob)
            pg.on('pageerror', lambda e: errs.append(f'PAGEERROR: {e}'))
            await pg.goto(URL); await pg.wait_for_timeout(700)
            await pg.mouse.click(vp['width'] / 2, vp['height'] / 2); await pg.wait_for_timeout(1200)
            print(tag, 'home pokes', await poke_all(pg, tag + '-home'))
            await pg.click('#btn-deliver'); await T.pick(pg, 3)
            print(tag, 'game pokes', await poke_all(pg, tag + '-game'))
            await pg.close()
        print('ERRORS', errs)
        await b.close()
asyncio.run(main())
