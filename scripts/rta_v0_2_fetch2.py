#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTA v0.2 — ЗАГРУЗКА ЧАСТЬ 2: IMF WEO (datamapper) + WB инфляция.
Серии (единообразно для всех кейсов, без подбора):
  GGXWDG_NGDP — госдолг, % ВВП (d факт)
  pb          — первичное сальдо, % ВВП
  ie          — проценты по госдолгу, % ВВП (процентный счёт = A_crit-сторона)
  NGDP_RPCH   — рост реального ВВП, %
  FP.CPI.TOTL.ZG (WB) — инфляция, % (для дефлятора ставки)
"""
import json
import subprocess
import time

OUT = '/home/z/my-project/scripts/rta_v0_2_data'
COUNTRIES = ['GRC', 'ARG', 'ZMB', 'LKA', 'DEU']
DM_SERIES = ['GGXWDG_NGDP', 'pb', 'ie', 'NGDP_RPCH']


def curl_json(url, tries=3, timeout=40):
    for i in range(tries):
        try:
            r = subprocess.run(['curl', '-s', '-m', str(timeout), url],
                               capture_output=True, text=True,
                               timeout=timeout + 10)
            return json.loads(r.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            print(f'  retry {i+1}/{tries}: {type(e).__name__}')
            time.sleep(1 + i)
    return None


def main():
    store = {}
    # --- IMF datamapper (без фильтра страны — фильтруем локально) ---
    for ser in DM_SERIES:
        url = f'https://www.imf.org/external/datamapper/api/v1/{ser}'
        print(f'fetch datamapper {ser} ...')
        d = curl_json(url)
        if d is None or 'values' not in d or ser not in d['values']:
            print(f'  FAIL {ser}')
            store[f'DM_{ser}'] = {'error': True}
            continue
        allc = d['values'][ser]
        rows = {c: {y: v for y, v in allc.get(c, {}).items()
                    if v is not None and 1995 <= int(y) <= 2026}
                for c in COUNTRIES}
        store[f'DM_{ser}'] = rows
        for c in COUNTRIES:
            yrs = sorted(rows[c])
            print(f'  {ser} {c}: {len(yrs)} obs {yrs[0] if yrs else "-"}..'
                  f'{yrs[-1] if yrs else "-"}')
    # --- WB inflation ---
    for c in COUNTRIES:
        url = (f'https://api.worldbank.org/v2/country/{c}/indicator/'
               f'FP.CPI.TOTL.ZG?date=1995:2024&format=json&per_page=100')
        print(f'fetch WB CPI {c} ...')
        d = curl_json(url)
        if d is None or not isinstance(d, list) or len(d) < 2:
            print(f'  FAIL CPI {c}')
            store[f'WB_FP.CPI.TOTL.ZG_{c}'] = {'error': True}
            continue
        rows = {x['date']: x['value'] for x in d[1] if x.get('value') is not None}
        store[f'WB_FP.CPI.TOTL.ZG_{c}'] = {'rows': rows}
        print(f'  ok: {len(rows)} obs')
    with open(f'{OUT}/raw_weo_cpi.json', 'w', encoding='utf-8') as f:
        json.dump(store, f, ensure_ascii=False, indent=1)
    print(f'saved {OUT}/raw_weo_cpi.json')


if __name__ == '__main__':
    main()
