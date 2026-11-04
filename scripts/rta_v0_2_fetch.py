#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTA v0.2 — ЗАГРУЗЧИК РЕАЛЬНЫХ ДАННЫХ (World Bank API v2).
Задача v0.2 (Полимат): «взять реальные данные и прогнать через тот же граф
переходов, не меняя модель под полученный результат».

Кейсы = названные в «Красной Нити» и v0.1: GRC (Greece), ARG (Argentina),
ZMB (Zambia), LKA (Sri Lanka) + контроль DEU (Germany).
Индикаторы World Bank:
  NY.GDP.MKTP.KD.ZG  — рост реального ВВП, % (g)
  FR.INR.RINR        — реальная ставка, % (r; прокси: lending − inflation)
  GC.DOD.TOTL.GD.ZS  — долг центрального правительства, % ВВП (d факт)
  GC.NLD.TOTL.GD.ZS  — сальдо центрального правительства, % ВВП (overall)
  GC.XPN.INTP.GD.ZS  — процентные платежи, % ВВП (для pb = overall + interest)
Всё сохраняется сырым JSON в scripts/rta_v0_2_data/ для аудита.
"""
import json
import os
import subprocess
import time

OUT = '/home/z/my-project/scripts/rta_v0_2_data'
os.makedirs(OUT, exist_ok=True)

COUNTRIES = ['GRC', 'ARG', 'ZMB', 'LKA', 'DEU']
INDICATORS = ['NY.GDP.MKTP.KD.ZG', 'FR.INR.RINR', 'GC.DOD.TOTL.GD.ZS',
              'GC.NLD.TOTL.GD.ZS', 'GC.XPN.INTP.GD.ZS']
YEARS = '1995:2024'


def fetch(url, tries=3, timeout=25):
    for i in range(tries):
        try:
            r = subprocess.run(['curl', '-s', '-m', str(timeout), url],
                               capture_output=True, text=True, timeout=timeout + 5)
            return json.loads(r.stdout)
        except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            print(f'  retry {i+1}/{tries}: {type(e).__name__}')
            time.sleep(1 + i)
    return None


def main():
    store = {}
    for c in COUNTRIES:
        for ind in INDICATORS:
            url = (f'https://api.worldbank.org/v2/country/{c}/indicator/{ind}'
                   f'?date={YEARS}&format=json&per_page=100')
            print(f'fetch {c} {ind} ...')
            data = fetch(url)
            key = f'{c}_{ind}'
            if data is None or not isinstance(data, list) or len(data) < 2:
                print(f'  FAIL {key}')
                store[key] = {'error': True}
                continue
            rows = {x['date']: x['value'] for x in data[1] if x.get('value')
                    is not None}
            store[key] = {'total': data[0]['total'], 'rows': rows,
                          'lastupdated': data[0].get('lastupdated')}
            print(f'  ok: {data[0]["total"]} obs, '
                  f'years {min(rows) if rows else "-"}..{max(rows) if rows else "-"}')
    with open(f'{OUT}/raw_wb.json', 'w', encoding='utf-8') as f:
        json.dump(store, f, ensure_ascii=False, indent=1)
    print(f'saved {OUT}/raw_wb.json')


if __name__ == '__main__':
    main()
