#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RED THREAD AUDIT v0.4 — ЗАГРУЗЩИК РЕАЛЬНЫХ ДАННЫХ (curl, инкрементально).
Территории R7: RUS / USA / CHN / EUR (еврозона).
Единая измерительная процедура для всех четырёх (требование R7):
  A-класс (живые API, дата записи фиксируется):
    GGXWDG_NGDP — валовой госдолг, % ВВП                (IMF datamapper, WEO)
    pb          — первичное сальдо, % ВВП               (IMF datamapper, FM)
    ie          — процентные расходы, % ВВП             (IMF datamapper, FM)
    NGDP_RPCH   — рост реального ВВП, %                 (IMF datamapper, WEO)
    PCPIPCH     — инфляция, среднегодовая, %            (IMF datamapper, WEO)
    FS.AST.PRVT.GD.ZS — внутренний кредит частному сектору, % ВВП (World Bank)
  C-якоря (цитаты Полимата, им же снабжены ссылками IMF; НЕ перевери равно
  мной здесь — статусы помечены C): augmented debt CN 2024=117.0, 2026=135.3,
  2031=153.7, 2034≈162.7; внешний долг госсектора РФ ≈1% ВВП (нач. 2026).
Правила пропусков (объявлены ДО загрузки): при отсутствии страны/года в
источнике серия просто не заполняется; никакой ручной интерполяции.
"""
import subprocess
import os
import json
import time

DATA = '/home/z/my-project/scripts/rta_v0_4_data'
os.makedirs(DATA, exist_ok=True)

TERR = ['RUS', 'USA', 'CHN', 'EUR']
DM = ['GGXWDG_NGDP', 'pb', 'ie', 'NGDP_RPCH', 'PCPIPCH']


def curl(url, path, timeout=90):
    try:
        r = subprocess.run(['curl', '-sL', '--max-time', str(timeout), url],
                           capture_output=True, text=True, timeout=timeout + 20)
        body = r.stdout
        if not body or body.strip() in ('', '404', 'null'):
            return False
        # datamapper для отсутствующих кодов возвращает {"errors":{...}}
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
    stamp = []
    # --- IMF datamapper: 5 индикаторов × 4 территории ---
    for code in DM:
        path = f'{DATA}/dm_{code}.json'
        if os.path.exists(path):          # инкрементально
            print(f'[skip] {code}')
        else:
            url = f'https://www.imf.org/external/datamapper/api/v1/{code}'
            ok = curl(url, path)
            print(f'[{"OK" if ok else "FAIL"}] datamapper {code}')
            if not ok and os.path.exists(path):
                os.remove(path)
            time.sleep(1)
        if os.path.exists(path):
            stamp.append({'src': 'IMF datamapper', 'code': code, 'file': path})
    # по-территориально, если общий URL не отдал код
    for code in DM:
        path = f'{DATA}/dm_{code}.json'
        if not os.path.exists(path):
            continue
        with open(path, encoding='utf-8') as f:
            j = json.load(f)
        vals = j.get('values', {}).get(code, {})
        missing = [t for t in TERR if t not in vals]
        if not missing:
            continue
        print(f'  общий вызов не содержит: {code}: {missing} — добираем по-одному')
        for t in missing:
            p2 = f'{DATA}/dm_{code}_{t}.json'
            url = f'https://www.imf.org/external/datamapper/api/v1/{code}/{t}'
            ok = curl(url, p2)
            print(f'  [{"OK" if ok else "FAIL"}] {code}/{t}')
            time.sleep(1)
    # --- World Bank: частный кредит ---
    ind = 'FS.AST.PRVT.GD.ZS'
    for t in TERR:
        path = f'{DATA}/wb_priv_{t}.json'
        if os.path.exists(path):
            print(f'[skip] WB {t}')
            continue
        url = (f'https://api.worldbank.org/v2/country/{t}/indicator/{ind}'
               f'?format=json&per_page=100')
        ok = curl(url, path, timeout=120)
        print(f'[{"OK" if ok else "FAIL"}] WB {ind} {t}')
        time.sleep(1)
        if not ok and os.path.exists(path):
            os.remove(path)
    with open(f'{DATA}/fetch_log.json', 'w', encoding='utf-8') as f:
        json.dump({'stamp': str(stamp), 'note': 'см. mtime файлов'}, f,
                  ensure_ascii=False, indent=1)
    print('\n--- итог ---')
    for fn in sorted(os.listdir(DATA)):
        print(f'  {fn} ({os.path.getsize(f"{DATA}/{fn}")} B)')


if __name__ == '__main__':
    main()
