import asyncio, json, sys
from playwright.async_api import async_playwright
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__)); _OUT = _os.path.join(_HERE, 'out')
_os.makedirs(_os.path.join(_OUT, 't'), exist_ok=True); _os.chdir(_OUT)
URL = 'file://' + _os.path.join(_HERE, 'index.html') + '#debug'
async def st(pg, e): return await pg.evaluate(e)
async def wait_for(pg, expr, timeout=30000, step=200):
    t = 0
    while t < timeout:
        if await pg.evaluate(expr): return True
        await pg.wait_for_timeout(step); t += step
    return False
async def play_station(pg, idx, shots, wrong_first=0, use_tap=False):
    # drive right until the station is active
    await pg.keyboard.down('ArrowRight')
    ok = await wait_for(pg, '__lt.st && __lt.st.active && !__lt.st.done', 20000)
    await pg.keyboard.up('ArrowRight')
    if not ok: print('station', idx, 'never activated'); return False
    s = await st(pg, '({l: __lt.st.l, lvl: __lt.st.lvl, items: __lt.st.items.map(i => i.l), m: __lt.st.m})')
    await pg.wait_for_timeout(800)
    if shots: await pg.screenshot(path=f't/{shots}-a-arrive.png')
    wrongs = [x for x in s['items'] if x != s['l']]
    for w in range(min(wrong_first, len(wrongs))):
        await wait_for(pg, '!__lt.st.busy', 8000)
        if use_tap and w == 0:
            pos = await st(pg, f'(() => {{ const s = __lt.st, it = s.items.find(i => i.l === "{wrongs[0]}"); const y = s.m === "deliver" ? __lt.dockY(s) - 62 : 770 - 64 - 110; return __lt.screenOf(it.x, y); }})()')
            await pg.mouse.click(pos['x'], pos['y'])
        else:
            await st(pg, f'__lt.pick("{wrongs[w % len(wrongs)]}")')
        await wait_for(pg, f'__lt.st.misses >= {w + 1}', 10000)
        await pg.wait_for_timeout(300)
        if shots and w == 0: await pg.screenshot(path=f't/{shots}-b-wrong.png')
        await wait_for(pg, '!__lt.st.busy', 8000); await pg.wait_for_timeout(2500)
    await pg.wait_for_timeout(800)
    hint = await st(pg, '__lt.st.hint')
    if shots and wrong_first >= 2: await pg.screenshot(path=f't/{shots}-c-hint.png')
    # now the right one, by driving there and pressing the action key
    target_x = await st(pg, f'__lt.st.items.find(i => i.l === "{s["l"]}").x')
    for _ in range(6):
        px = await st(pg, '__lt.P.x')
        if abs(px - target_x) < 80: break
        key = 'ArrowRight' if target_x > px else 'ArrowLeft'
        await pg.keyboard.down(key)
        for _ in range(100):
            await pg.wait_for_timeout(25)
            px = await st(pg, '__lt.P.x')
            if abs(px - target_x) < 110: break
        await pg.keyboard.up(key); await pg.wait_for_timeout(500)
    await wait_for(pg, '!__lt.speaking', 15000)
    sel = await st(pg, '__lt.sel() && __lt.sel().l')
    await pg.keyboard.press('Space')
    await pg.wait_for_timeout(1800)
    if shots: await pg.screenshot(path=f't/{shots}-d-right.png')
    done = await wait_for(pg, '!__lt.st || __lt.st.done', 30000)
    if not done:
        print('STUCK:', await st(pg, '({busy: __lt.st.busy, locked: __lt.locked, speaking: __lt.speaking, items: __lt.st.items.map(i => i.l + ":" + i.state), px: Math.round(__lt.P.x), sel: __lt.sel() && __lt.sel().l, misses: __lt.st.misses})'))
    print(f'station {idx}: mode {s["m"]} target {s["l"]} lvl {s["lvl"]} items {s["items"]} selected-before-press {sel} hint {hint} done {done}')
    return done
async def pick(pg, i=0, shot=None, tap=False):
    ok = await wait_for(pg, '!document.getElementById("ov-pick").hidden', 5000)
    await pg.wait_for_timeout(500)
    if shot: await pg.screenshot(path=f't/{shot}.png')
    sel = f'#truck-choices .truck-btn >> nth={i}'
    if tap: await pg.tap(sel)
    else: await pg.click(sel)
    await wait_for(pg, '__lt.mode === "deliver" || __lt.mode === "tow"', 5000)
    await pg.wait_for_timeout(1200)
    return ok
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        errs = []
        pg = await b.new_page(viewport={'width': 1280, 'height': 720})
        pg.on('console', lambda m: errs.append(f'{m.type}: {m.text}') if m.type in ('error','warning') else None)
        pg.on('pageerror', lambda e: errs.append(f'PAGEERROR: {e}'))
        await pg.add_init_script("try{localStorage.setItem('letter-trucks-v3', JSON.stringify({letters:'bksmtjvl', stops:3, boxes:3}))}catch(e){}")
        await pg.goto(URL); await pg.wait_for_timeout(700)
        await pg.mouse.click(640, 360); await pg.wait_for_timeout(1200)
        await pg.screenshot(path='t/01-home.png')
        await pg.click('#btn-deliver'); await pg.wait_for_timeout(1000)
        print('picker shown:', await pick(pg, 2, '02a-picker'), 'horn', await st(pg, '__lt.P && __lt.P.horn'))
        await pg.screenshot(path='t/02-deliver-start.png')
        for i in range(3):
            await play_station(pg, i, f'1{i}' if i < 2 else None, wrong_first=2 if i == 0 else (1 if i == 1 else 0), use_tap=(i == 1))
        ok = await wait_for(pg, '__lt.mode === "end"', 20000)
        await pg.wait_for_timeout(600); await pg.screenshot(path='t/19-deliver-end.png')
        print('deliver end:', ok, 'progress', json.dumps(await st(pg, '__lt.progress.deliver')))
        await pg.click('#ov-end [data-home]'); await pg.wait_for_timeout(900)
        await pg.click('#btn-tow'); await pg.wait_for_timeout(1000)
        await pick(pg, 1, '02b-picker-tow')
        for i in range(3):
            await play_station(pg, i, f'2{i}' if i < 1 else None, wrong_first=1 if i == 0 else 0)
        ok = await wait_for(pg, '__lt.mode === "end"', 20000)
        await pg.wait_for_timeout(600); await pg.screenshot(path='t/29-tow-end.png')
        print('tow end:', ok)
        await pg.close()
        ph = await b.new_page(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True)
        ph.on('pageerror', lambda e: errs.append(f'PAGEERROR phone: {e}'))
        await ph.goto(URL); await ph.wait_for_timeout(700)
        await ph.tap('#ov-start'); await ph.wait_for_timeout(800)
        await ph.screenshot(path='t/31-phone-home.png')
        await ph.tap('#btn-tow'); await ph.wait_for_timeout(1200)
        await pick(ph, 3, '31b-phone-picker', tap=True)
        # on touch the truck drives itself to the stop
        await wait_for(ph, '__lt.st && __lt.st.active', 20000)
        await ph.wait_for_timeout(1500)
        await ph.screenshot(path='t/32-phone-tow-station.png')
        await ph.evaluate('document.getElementById("parent-home").click()'); await ph.wait_for_timeout(1200); await ph.tap('#btn-deliver'); await ph.wait_for_timeout(1000); await pick(ph, 0, None, tap=True)
        await wait_for(ph, '__lt.st && __lt.st.active', 20000)
        await ph.wait_for_timeout(1500)
        await ph.screenshot(path='t/33-phone-deliver-station.png')
        print('phone scrollWidth', await ph.evaluate('[document.documentElement.scrollWidth, innerWidth]'))
        print('ERRORS', errs[:10])
        await b.close()
if __name__ == '__main__':
    asyncio.run(main())
