#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R10 fetch: реальные ряды для ΔResource / ΔExtraction (класс A, с логом).
Ряды:
  NY.GDP.TOTL.RT.ZS — total natural resources rents (% of GDP)  -> ΔResource
  GC.TAX.TOTL.GD.ZS — tax revenue (% of GDP)                    -> ΔExtraction
Кейсы = объединение v0.2 + v0.5 + v0.4 (10 суверенов + 1 контроль).
Каждый файл: источник WB API v2, дата выгрузки, обновление дампа в метаданных.
"""
import json
import subprocess
import time
from pathlib import Path

DATA = Path('/home/z/my-project/scripts/rta_r10_data')
DATA.mkdir(parents=True, exist_ok=True)
CASES = ['GRC', 'ARG', 'ZMB', 'LKA', 'DEU', 'UKR', 'TUR', 'BRA', 'PAK', 'JPN']
INDS = ['NY.GDP.TOTL.RT.ZS', 'GC.TAX.TOTL.GD.ZS']
log = {}

for ind in INDS:
    for c in CASES:
        fn = DATA / f'{c}_{ind}.json'
        if fn.exists() and fn.stat().st_size > 200:
            log[f'{c}_{ind}'] = 'cached'
            continue
        url = (f'https://api.worldbank.org/v2/country/{c}/indicator/{ind}'
               f'?format=json&date=2000:2024&per_page=100')
        for attempt in range(3):
            try:
                r = subprocess.run(['curl', '-s', '--max-time', '25', url],
                                   capture_output=True, text=True, timeout=30)
                body = json.loads(r.stdout)
                if isinstance(body, list) and len(body) >= 2 and body[1] is not None:
                    fn.write_text(r.stdout, encoding='utf-8')
                    log[f'{c}_{ind}'] = f"ok updated={body[0].get('lastupdated')}"
                    break
                log[f'{c}_{ind}'] = f'empty:{r.stdout[:80]}'
            except Exception as e:
                log[f'{c}_{ind}'] = f'err:{e}'
            time.sleep(1)
        else:
            log[f'{c}_{ind}'] = 'FAILED'
        time.sleep(0.3)

(DATA / 'fetch_log.json').write_text(json.dumps(log, ensure_ascii=False, indent=2),
                                     encoding='utf-8')
ok = sum(1 for v in log.values() if str(v).startswith(('ok', 'cached')))
print(f'ok/cached: {ok}/{len(log)}')
for k, v in log.items():
    if not str(v).startswith(('ok', 'cached')):
        print('FAIL', k, v)
