import asyncio
from playwright.async_api import async_playwright
import test_v3 as T
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__)); _OUT = _os.path.join(_HERE, 'out')
_os.makedirs(_os.path.join(_OUT, 't'), exist_ok=True); _os.chdir(_OUT)
URL = 'file://' + _os.path.join(_HERE, 'index.html') + '#debug'
PAD = """
window.__pad = { buttons: Array.from({length: 17}, () => ({ pressed: false, value: 0 })), axes: [0, 0, 0, 0] };
navigator.getGamepads = () => [{ id: 'Fake pad', connected: true, index: 0, mapping: 'standard', buttons: window.__pad.buttons, axes: window.__pad.axes, timestamp: performance.now() }];
"""
async def press(pg, i, hold=120):
    await pg.evaluate(f'__pad.buttons[{i}].pressed = true'); await pg.wait_for_timeout(hold)
    await pg.evaluate(f'__pad.buttons[{i}].pressed = false'); await pg.wait_for_timeout(250)
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(args=['--autoplay-policy=no-user-gesture-required'])
        pg = await b.new_page(viewport={'width': 1280, 'height': 720}); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.add_init_script(PAD)
        await pg.goto(URL); await pg.wait_for_timeout(800)
        await press(pg, 0); await pg.wait_for_timeout(1200)      # start
        await press(pg, 0); await pg.wait_for_timeout(1400)      # deliver (first focused)
        print('picker visible', await pg.evaluate('!document.getElementById("ov-pick").hidden'))
        f0 = await pg.evaluate('document.activeElement.getAttribute("aria-label")')
        await press(pg, 15); await press(pg, 15)                  # dpad right twice
        f1 = await pg.evaluate('document.activeElement.getAttribute("aria-label")')
        col = await pg.evaluate('__lt.P.color')
        await pg.screenshot(path='t/60-pad-picker.png')
        await press(pg, 0); await pg.wait_for_timeout(2200)
        print('focus', f0, '->', f1, '| road truck colour while choosing', col, '| mode', await pg.evaluate('__lt.mode'), 'P', await pg.evaluate('[__lt.P.color, __lt.P.horn, __lt.P.type]'))
        print('errors', errs); await b.close()
asyncio.run(main())
