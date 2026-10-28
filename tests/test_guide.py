import asyncio, json
from playwright.async_api import async_playwright
import test_v3 as T
from test_touch import SPOT, settle, URL
# fresh letters: the right box glows (fading over a few rounds) and guided picks don't level up
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        pg = await b.new_page(viewport={'width': 844, 'height': 390}, has_touch=True, is_mobile=True); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        prog = {'deliver': {'b': {'lvl': 0, 'streak': 0, 'seen': 2, 'first': 0, 'helped': 2}, 'k': {'lvl': 0, 'streak': 0, 'seen': 3, 'first': 0, 'helped': 3}}, 'tow': {}}
        await pg.add_init_script("try{localStorage.setItem('letter-trucks-v3', JSON.stringify({letters:'bksm', stops:4, boxes:3})); localStorage.setItem('letter-trucks-progress', '%s')}catch(e){}" % json.dumps(prog))
        await pg.goto(URL); await pg.wait_for_timeout(600)
        await pg.tap('#ov-start'); await pg.wait_for_timeout(800); await pg.tap('#btn-deliver'); await pg.wait_for_timeout(1200); await T.pick(pg, 0, tap=True)
        GUIDE = [1, 0.55, 0.25]
        for n in range(4):
            if not await T.wait_for(pg, '__lt.st && __lt.st.active', 30000): print('never reached stop', n); break
            await settle(pg)
            s = await pg.evaluate('({l: __lt.st.l, guide: __lt.st.guide, heard: !!__lt.st.heard})')
            before = await pg.evaluate(f'JSON.stringify(__lt.progress.deliver["{s["l"]}"] || {{}})')
            bp = json.loads(before); h = bp.get('helped', 0); want = (GUIDE[h] if h < 3 else 0) if bp.get('lvl', 0) == 0 else 0
            if n == 0: await pg.screenshot(path='t/70-guide.png')
            print(f'stop {n}: {s["l"]} guide {s["guide"]} (want {want}) heard {s["heard"]}', 'OK' if s['guide'] == want else 'WRONG')
            pos = await pg.evaluate(SPOT + f'("{s["l"]}")'); await pg.touchscreen.tap(pos['x'], pos['y'])
            await T.wait_for(pg, '!__lt.st || __lt.st.done', 30000)
            print('   progress', before, '->', await pg.evaluate(f'JSON.stringify(__lt.progress.deliver["{s["l"]}"])'))
        print('errors', errs); await b.close()
asyncio.run(main())
