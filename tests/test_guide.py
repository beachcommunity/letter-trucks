import asyncio, json
from playwright.async_api import async_playwright
import test_v3 as T
from test_touch import SPOT, settle, URL, drive_until, tap
# a new letter's box glows only after a wait that grows (1.5 s, 3.5 s, 6 s, then never). A pick made
# while it glows doesn't count toward leveling up; a pick before the glow does
DELAY = [1.5, 3.5, 6]
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        pg = await b.new_page(viewport={'width': 844, 'height': 390}, has_touch=True, is_mobile=True); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        prog = {'deliver': {'b': {'lvl': 0, 'streak': 0, 'seen': 2, 'first': 0, 'helped': 2}, 'k': {'lvl': 0, 'streak': 0, 'seen': 3, 'first': 0, 'helped': 3}}, 'tow': {}}
        await pg.add_init_script("try{localStorage.setItem('letter-trucks-v3', JSON.stringify({letters:'bksm', stops:4, boxes:3, sets:2})); localStorage.setItem('letter-trucks-progress', '%s')}catch(e){}" % json.dumps(prog))
        await pg.goto(URL); await pg.wait_for_timeout(600)
        await pg.tap('#ov-start'); await pg.wait_for_timeout(800); await pg.tap('#btn-deliver'); await pg.wait_for_timeout(1200); await T.pick(pg, 0, tap=True)
        for n in range(4):
            if not await drive_until(pg, '__lt.st && __lt.st.phase === "pick"'): print('never reached stop', n); break
            await T.wait_for(pg, '__lt.st.heard', 15000)
            s = await pg.evaluate('({l: __lt.st.l, guide: __lt.st.guide})')
            before = json.loads(await pg.evaluate(f'JSON.stringify(__lt.progress.deliver["{s["l"]}"] || {{}})'))
            h = before.get('helped', 0); want = (DELAY[h] if h < 3 else None) if before.get('lvl', 0) == 0 else None
            early = await pg.evaluate('__lt.glowing()')
            # stop 0 picks right away (before any glow); the others wait for the glow if there is one
            if n > 0 and want is not None:
                await pg.wait_for_timeout(int(want * 1000) + 500)
            glow = await pg.evaluate('__lt.glowing()')
            if n == 1: await pg.screenshot(path='t/70-guide.png')
            print(f'stop {n}: {s["l"]} wait {s["guide"]} (want {want}) glowing right away {early} glowing at pick {glow}', 'OK' if s['guide'] == want and not early and glow == (n > 0 and want is not None) else 'WRONG')
            await settle(pg)
            await tap(pg, await pg.evaluate(SPOT + f'("{s["l"]}")'))
            await T.wait_for(pg, '__lt.st.phase === "carry"', 12000)
            await drive_until(pg, '__lt.st.phase === "give"')
            await tap(pg, await pg.evaluate('__lt.screenOf(__lt.P.x, __lt.P.y - 90)'))
            await T.wait_for(pg, '!__lt.st || __lt.st.done', 30000)
            after = json.loads(await pg.evaluate(f'JSON.stringify(__lt.progress.deliver["{s["l"]}"])'))
            guided = glow
            ok = (after.get('helped', 0) == h + 1 and after['first'] == before.get('first', 0)) if guided else (after['first'] == before.get('first', 0) + 1 and after.get('helped', 0) == h)
            print('   progress', before, '->', after, 'OK' if ok else 'WRONG')
        print('errors', errs); await b.close()
asyncio.run(main())
