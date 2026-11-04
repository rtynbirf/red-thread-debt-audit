#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RED THREAD AUDIT v0.5 — ЗАГРУЗЩИК НЕЗАВИСИМЫХ КЕЙСОВ (curl, инкрементально).
Раунд 12, задание (6) из v5.0: ex-ante операторы на независимом наборе —
висит с v0.2 («иначе подгонка»). Выборка НЕ пересекается с v0.2
(GRC/ARG/ZMB/LKA/DEU) и v0.4 (RUS/USA/CHN/EUR):
  UKR — реструктуризация 2015 (~20% haircut), стендстилл 2022+;
  TUR — девальвации 2018/2021–2023;
  BRA — кризис 2002, рецессия 2014–2016, без реструктуризаций (полуконтроль);
  EGY — либерализация курса 2016, девальвации 2022–2024;
  PAK — Парижский клуб 2001, программы МВФ 2008/2013/2019/2023;
  JPN — контроль специфичности: без реструктуризаций в окне 2000–2024.
Единая процедура (требование независимости: тот же рецепт, что v0.2/v0.4):
  A-класс (живые API): GGXWDG_NGDP, pb, ie, NGDP_RPCH, PCPIPCH (IMF
  datamapper). Правила пропусков: серия просто не заполняется, никакой
  интерполяции; пробелы публикуются как есть.
"""
import subprocess
import os
import json
import time

DATA = '/home/z/my-project/scripts/rta_v0_5_data'
os.makedirs(DATA, exist_ok=True)

TERR = ['UKR', 'TUR', 'BRA', 'EGY', 'PAK', 'JPN']
DM = ['GGXWDG_NGDP', 'pb', 'ie', 'NGDP_RPCH', 'PCPIPCH']


def curl(url, path, timeout=90):
    try:
        r = subprocess.run(['curl', '-sL', '--max-time', str(timeout), url],
                           capture_output=True, text=True, timeout=timeout + 20)
        body = r.stdout
        if not body or body.strip() in ('', '404', 'null'):
            return False
        j = json.loads(body)
        if isinstance(j, dict) and j.get('errors'):
            return False
        with open(path, 'w', encoding='utf-8') as f:
            f.write(body)
        return True
    except Exception as e:
        print(f'  ERR {url}: {e}')
        return False


def main():
    for code in DM:
        path = f'{DATA}/dm_{code}.json'
        if os.path.exists(path):
            print(f'[skip] {code}')
        else:
            url = f'https://www.imf.org/external/datamapper/api/v1/{code}'
            ok = curl(url, path)
            print(f'[{"OK" if ok else "FAIL"}] datamapper {code}')
            time.sleep(1)
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            j = json.load(f)
        vals = j.get('values', {}).get(code, {})
        missing = [t for t in TERR if t not in vals]
        if not missing:
            continue
        print(f'  общий вызов не содержит {code}: {missing} — добираем')
        for t in missing:
            p2 = f'{DATA}/dm_{code}_{t}.json'
            url = f'https://www.imf.org/external/datamapper/api/v1/{code}/{t}'
            ok = curl(url, p2)
            print(f'  [{"OK" if ok else "FAIL"}] {code}/{t}')
            time.sleep(1)
    print('\n--- покрытие (годы, факт ≤2024) ---')
    for code in DM:
        path = f'{DATA}/dm_{code}.json'
        if not os.path.exists(path):
            print(f'{code}: ФАЙЛА НЕТ')
            continue
        with open(path, encoding='utf-8') as f:
            j = json.load(f)
        vals = j.get('values', {}).get(code, {})
        for t in TERR:
            key = t
            src = vals.get(key) or {}
            if not src and os.path.exists(f'{DATA}/dm_{code}_{t}.json'):
                with open(f'{DATA}/dm_{code}_{t}.json', encoding='utf-8') as f:
                    src = json.load(f).get('values', {}).get(code, {}).get(t, {})
            yrs = sorted(int(y) for y in src if src.get(y) is not None)
            yr = [y for y in yrs if 2000 <= y <= 2024]
            print(f'  {code:<12} {t}: {len(yr)} лет '
                  f'({yr[0] if yr else "-"}–{yr[-1] if yr else "-"})')
    with open(f'{DATA}/fetch_log.json', 'w', encoding='utf-8') as f:
        json.dump({'stamp': str(os.listdir(DATA)),
                   'note': 'см. mtime файлов'}, f,
                  ensure_ascii=False, indent=1)
    print('\n--- файлы ---')
    for fn in sorted(os.listdir(DATA)):
        print(f'  {fn} ({os.path.getsize(f"{DATA}/{fn}")} B)')


if __name__ == '__main__':
    main()
