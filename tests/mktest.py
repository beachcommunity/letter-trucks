"""Wrap dist/letter-trucks.html with local fonts -> tests/index.html, so tests run offline with the real fonts."""
import os
H = os.path.dirname(os.path.abspath(__file__)); R = os.path.dirname(H); F = f'{H}/fonts'
head = f'''<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{{color-scheme:light}}body{{margin:0;font:14px system-ui}}[hidden]{{display:none!important}}
@font-face{{font-family:"Fraunces";src:url("file://{F}/fraunces-latin-full-normal.woff2") format("woff2");font-weight:100 900;font-display:block}}
@font-face{{font-family:"Schibsted Grotesk";src:url("file://{F}/schibsted-grotesk-latin-800-normal.woff2") format("woff2");font-weight:800}}
@font-face{{font-family:"Schibsted Grotesk";src:url("file://{F}/schibsted-grotesk-latin-600-normal.woff2") format("woff2");font-weight:600}}
@font-face{{font-family:"Schibsted Grotesk";src:url("file://{F}/schibsted-grotesk-latin-400-normal.woff2") format("woff2");font-weight:400}}
</style></head><body>'''
open(f'{H}/index.html', 'w').write(head + open(f'{R}/dist/letter-trucks.html').read() + '</body></html>')
print('wrote tests/index.html')
