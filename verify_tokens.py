import asyncio, aiohttp

tokens = [
    '8698062387:AAF6O45NoQAk3hdoRTpYxMecTWBstF5FM7c',
    '8659197905:AAHCtrVIwADNpJA3vottu8KrSS0bJGlg5Vg',
    '8415397198:AAFf3Br-Y7hEmghjPTwhVJQur-mMCnWRcfI',
    '8603982216:AAGJY0RCRn0ayixuF417_R4jBOo9RjFTPAA',
    '8768495139:AAGbHMjA6B-skrQTQ9tTu2mClDc1P0teku0',
    '8736863493:AAENJmTrWd8HtrZa_Rwp1pkW5HHO4xx3H_c',
    '8544201838:AAEkPJe3_LXW6U_PovIiolxUyGTEopmrD9k',
    '8722630071:AAEjRnyAKdhWT2SMXgCLMYqx6GonQvBX2VU',
    '8658573219:AAHcx5k8rir_1fF3qMROeTLBijN2FSPTipI',
]

async def check(session, t):
    bid = t.split(':')[0]
    try:
        async with session.get(f'https://api.telegram.org/bot{t}/getMe', timeout=aiohttp.ClientTimeout(total=10)) as r:
            d = await r.json()
            if d.get('ok'):
                uname = d['result']['username']
                return f'{bid} -> @{uname} (OK)'
            else:
                desc = d.get('description', '?')
                return f'{bid} -> INVALID ({desc})'
    except Exception as e:
        return f'{bid} -> ERROR ({e})'

async def main():
    async with aiohttp.ClientSession() as session:
        results = await asyncio.gather(*[check(session, t) for t in tokens])
        for r in results:
            print(r)

asyncio.run(main())
