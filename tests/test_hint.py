import asyncio, json
from playwright.async_api import async_playwright
import test_v3 as T
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__)); _OUT = _os.path.join(_HERE, 'out')
_os.makedirs(_os.path.join(_OUT, 't'), exist_ok=True); _os.chdir(_OUT)
URL = 'file://' + _os.path.join(_HERE, 'index.html') + '#debug'
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        pg = await b.new_page(viewport={'width': 1280, 'height': 720}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        prog = {l: {"lvl": 1, "streak": 0, "seen": 3, "first": 2} for l in "bksm"}
        await pg.add_init_script("try{localStorage.setItem('letter-trucks-v3', JSON.stringify({letters:'bksm', stops:3, boxes:3})); localStorage.setItem('letter-trucks-progress', JSON.stringify({deliver: %s, tow: {}}))}catch(e){}" % json.dumps(prog))
        await pg.goto(URL); await pg.wait_for_timeout(600)
        await pg.mouse.click(640, 360); await pg.wait_for_timeout(900)
        await pg.click('#btn-deliver'); await pg.wait_for_timeout(900); await T.pick(pg, 0)
        await T.play_station(pg, 0, '50', wrong_first=2)
        print('progress after', json.dumps(await pg.evaluate('__lt.progress.deliver')))
        print('errors', errs); await b.close()
asyncio.run(main())
