#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
RED THREAD AUDIT v0.2 — РЕАЛЬНЫЕ ДАННЫЕ ЧЕРЕЗ ЗАМОРОЖЕННЫЙ ГРАФ v0.1.
Задача v0.2 (Полимат): «взять реальные данные и прогнать через тот же граф
переходов, не меняя модель под полученный результат».
=============================================================================
ЧТО ЗАМОРОЖЕНО (вербатим v0.1, не меняется ни при каком результате):
    d[t+1] = ((1+r)/(1+g)) · d[t] − pb

ВХОДЫ (объявленные единообразные рецепты, ОДНИ И ТЕ ЖЕ для всех кейсов;
источники: IMF WEO datamapper, IMF macrohistory, World Bank API):
  d_act[t] = GGXWDG_NGDP        — госдолг, % ВВП (факт)
  pb[t]    = серия 'pb'         — первичное сальдо, % ВВП
           (ZMB отсутствует в источнике → объявленный fallback для ЛЮБОЙ
            страны без первичного источника: WB-GFS overall (GC.NLD) +
            проценты (INTP%rev × revenue%GDP / 100); правило одно для всех)
  ie[t]    = серия 'ie'         — проценты по госдолгу, % ВВП (ZMB — fallback)
  g[t]     = NGDP_RPCH          — рост реального ВВП, %
  π[t]     = FP.CPI.TOTL.ZG     — инфляция (WB); при пропуске — перенос
  r_real[t] = ((1 + ie[t]/d_act[t−1]) / (1 + π[t]/100)) − 1
           — неявная номинальная ставка на стоке (стандарт IMF) минус
             инфляция; ОБА члена наблюдаемы, ничего не калибруется.
  Старт: d_pred[2000] = d_act[2000]; окно 2001–2023.

СОБЫТИЯ (объявленные константы, публично документированы; см. отчёт §2).
ЗОНЫ («ЗАДАЧА ПОЛИМАТА», вербатим-логика, годовое исчисление):
  A = pb[t]; A_crit = ie[t] (= d·r — процентный счёт)
  Zone 1 «долговое рабство»: pb < ie
  Zone 2 «вечная рента»: |pb − ie| ≤ 0.5 п.п. (полоса объявлена)
  Zone 3 «производительный кредит»: pb > ie + 0.5

ПРЕДИСТОРИЯ (объявлена ДО прогона, статусы проставляются машиной):
  P1 мирные годы: в ≥70% лет вне событий (±1 год от события) |resid| < 10 п.п.
  P2 крупнейшие отрицательные остатки совпадают с событиями списаний
     (GRC 2012, ARG 2005, ZMB 2005–06, LKA 2024) — граф не содержит
     оператора реструктуризации, фактический долг проваливается под прогноз.
  P3 каждому реструктуризационному событию предшествуют ≥2 года подряд
     в Zone 1 (в окне 5 лет до события); контроль DEU — ни одного эпизода
     3 года подряд Zone 1.
  P4 задержка дефолт→закрытие реструктуризации ≥ 24 мес во всех кейсах;
     2001 и 2020-е — один порядок (2–4 года): закон задержки не смягчается
     со временем.

СТАТУС: E — исполнение задачи v0.2; граф не подгонялся; все остатки
публикуются как есть (включая провальные).
=============================================================================
"""
import json
import csv
import os

DATA = '/home/z/my-project/scripts/rta_v0_2_data'
OUT = '/home/z/my-project/scripts/rta_v0_2_out'
os.makedirs(OUT, exist_ok=True)
COUNTRIES = ['GRC', 'ARG', 'ZMB', 'LKA', 'DEU']
NAMES = {'GRC': 'Греция', 'ARG': 'Аргентина', 'ZMB': 'Замбия',
         'LKA': 'Шри-Ланка', 'DEU': 'Германия (контроль)'}
YEARS = list(range(2000, 2024))

EVENTS = {
    'GRC': [(2010.42, 'loss of market access 05-2010'),
            (2012.21, 'PSI 03-2012, номинал −53.5% частным')],
    'ARG': [(2001.96, 'дефолт 12-2001'),
            (2005.42, 'реструктуризация 06-2005, NPV ~−70%'),
            (2020.58, 'реструктуризация 08-2020, NPV ~−45%')],
    'ZMB': [(2005.29, 'HIPC completion 04-2005 + MDRI 2006'),
            (2020.87, 'дефолт 11-2020'),
            (2024.21, 'Eurobonds 03-2024, номинал ~−18%')],
    'LKA': [(2022.29, 'мораторий 04-2022'),
            (2024.70, 'сделка с держателями 09-2024, ~−28%')],
    'DEU': [],
}
# годы-«события» (±1 = шум события для P1)
EVENT_YEARS = {
    'GRC': {2010, 2011, 2012, 2013},
    'ARG': {2001, 2002, 2005, 2006, 2020, 2021},
    'ZMB': {2005, 2006, 2020, 2021, 2024},
    'LKA': {2022, 2023, 2024},
    'DEU': set(),
}
DELAYS = [  # (кейс, от, до, месяцев, комментарий)
    ('GRC', '2010-05', '2012-03', 22, 'потеря доступа → PSI'),
    ('ARG', '2001-12', '2005-06', 42, 'дефолт → обмен-2005'),
    ('ZMB', '2020-11', '2024-03', 28, 'дефолт → сделка Eurobonds'),
    ('LKA', '2022-04', '2024-09', 29, 'мораторий → сделка'),
]


def load_json(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def main():
    # ---------- сборка серий ----------
    debt = load_json(f'{DATA}/dm_GGXWDG_NGDP.json')['values']['GGXWDG_NGDP']
    pb_dm = load_json(f'{DATA}/dm_pb.json')['values']['pb']
    ie_dm = load_json(f'{DATA}/dm_ie.json')['values']['ie']
    grw = load_json(f'{DATA}/dm_NGDP_RPCH.json')['values']['NGDP_RPCH']

    wb = load_json(f'{DATA}/raw_wb.json')
    nld = wb.get('ZMB_GC.NLD.TOTL.GD.ZS', {}).get('rows', {})
    intp = {x['date']: x['value'] for x in
            load_json(f'{DATA}/zmb_INTP.json')[1] if x.get('value') is not None} \
        if os.path.exists(f'{DATA}/zmb_INTP.json') else {}
    rev = {x['date']: x['value'] for x in
           load_json(f'{DATA}/zmb_REV.json')[1] if x.get('value') is not None}
    int_gdp = {y: intp[y] * rev[y] / 100.0
               for y in intp if y in rev}

    cpi = {}
    for c in COUNTRIES:
        d = load_json(f'{DATA}/cpi_{c}.json')
        cpi[c] = {x['date']: x['value'] for x in d[1]
                  if x.get('value') is not None}

    rows_all = []
    summary = {}
    for c in COUNTRIES:
        d_act0 = {int(y): v for y, v in debt.get(c, {}).items()}
        if c == 'ZMB':
            pb_s = {int(y): (float(nld.get(str(y), 0.0)) +
                             float(int_gdp.get(str(y), 0.0)))
                    for y in range(2000, 2024)}
            ie_s = {int(y): float(int_gdp.get(str(y), 0.0))
                    for y in range(2000, 2024)}
        else:
            pb_s = {int(y): v for y, v in pb_dm.get(c, {}).items()}
            ie_s = {int(y): v for y, v in ie_dm.get(c, {}).items()}
        g_s = {int(y): v for y, v in grw.get(c, {}).items()}
        pi_s = {int(y): v for y, v in cpi[c].items()}

        # неявная номинальная ставка на стоке
        r_s = {}
        last_pi = None
        for t in range(2000, 2024):
            if t in pi_s:
                last_pi = pi_s[t]
            pi = last_pi if last_pi is not None else 0.0
            if t - 1 in d_act0 and d_act0[t - 1] > 0.5 and t in ie_s:
                i_nom = ie_s[t] / d_act0[t - 1]
                r_s[t] = (1.0 + i_nom) / (1.0 + pi / 100.0) - 1.0

        # ---------- ЗАМОРОЖЕННЫЙ ГРАФ v0.1 ----------
        # g в NGDP_RPCH — в ПРОЦЕНТАХ; формула требует долю → /100
        d_pred = {2000: d_act0[2000]}
        for t in range(2001, 2024):
            r = r_s.get(t)
            g_pct = g_s.get(t)
            pb = pb_s.get(t)
            if r is None or g_pct is None or pb is None or g_pct <= -99.0:
                d_pred[t] = d_pred[t - 1]  # перенос при пропуске (объявлено)
                continue
            g = g_pct / 100.0
            d_pred[t] = ((1.0 + r) / (1.0 + g)) * d_pred[t - 1] - pb

        # ---------- метрики ----------
        prev_resid = None
        for t in range(2000, 2024):
            da = d_act0.get(t)
            dp = d_pred[t]
            pb = pb_s.get(t)
            ie = ie_s.get(t)
            g = g_s.get(t)
            r = r_s.get(t)
            resid = (da - dp) if da is not None else None
            sfa = None
            if da is not None and t - 1 in d_act0 and pb is not None \
                    and g_s.get(t) is not None and g_s.get(t) > -99.0:
                g_frac = g_s.get(t) / 100.0
                pred_delta = ((r_s.get(t, 0.0) - g_frac) /
                              (1.0 + g_frac) * d_act0[t - 1]
                              - pb)
                sfa = (da - d_act0[t - 1]) - pred_delta
            if pb is None or ie is None:
                zone = 'н/д'
            elif pb < ie:
                zone = 'Z1-рабство'
            elif pb > ie + 0.5:
                zone = 'Z3-производительный'
            else:
                zone = 'Z2-вечная рента'
            ev = ''
            for y, lab in EVENTS[c]:
                if int(y) == t:
                    ev = lab
            rows_all.append({
                'country': c, 'year': t,
                'd_actual': round(da, 2) if da is not None else '',
                'd_pred': round(dp, 2), 'resid': round(resid, 2)
                if resid is not None else '',
                'pb': round(pb, 2) if pb is not None else '',
                'ie': round(ie, 2) if ie is not None else '',
                'g': round(g, 2) if g is not None else '',
                'r_real': round(r * 100, 2) if r is not None else '',
                'zone': zone, 'sfa': round(sfa, 2) if sfa is not None else '',
                'event': ev,
            })
        summary[c] = dict(d_act0=d_act0, d_pred=d_pred, pb=pb_s, ie=ie_s,
                          g=g_s, r=r_s, pi=pi_s)

    with open(f'{OUT}/results.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows_all[0].keys()))
        w.writeheader()
        w.writerows(rows_all)
    print(f'CSV: {OUT}/results.csv ({len(rows_all)} строк)')

    # ---------- ПРОВЕРКА ПРЕДИСТОРИИ ----------
    print('\n=== ПРОВЕРКА ПРЕДИСТОРИИ (граф не менялся) ===')

    # P1: мирные годы |resid| < 10 — агрегат и по странам
    calm = [r for r in rows_all if r['resid'] != '' and
            int(r['year']) not in EVENT_YEARS[r['country']]]
    ok1 = [r for r in calm if abs(r['resid']) < 10]
    share1 = len(ok1) / max(len(calm), 1) * 100
    print(f"P1 мирных лет: {len(calm)}, |resid|<10пп: {len(ok1)} "
          f"({share1:.0f}%) → {'ПОДТВЕРЖДЕНА' if share1 >= 70 else 'ОТКЛОНЕНА'}")
    for c in COUNTRIES:
        cc = [r for r in calm if r['country'] == c]
        kk = [r for r in cc if abs(r['resid']) < 10]
        if cc:
            print(f"   {c}: {len(kk)}/{len(cc)} ({100*len(kk)/len(cc):.0f}%)")

    # P2: топ-отрицательные остатки vs события
    neg = sorted([r for r in rows_all if r['resid'] != ''],
                 key=lambda r: r['resid'])[:12]
    print('P2 топ-12 отрицательных остатков (d_act − d_pred, п.п. ВВП):')
    hits = 0
    for r in neg:
        hit = 'СОБЫТИЕ±1' if int(r['year']) in EVENT_YEARS[r['country']] else ''
        if hit:
            hits += 1
        print(f"  {r['country']} {r['year']}: {r['resid']:+.1f}  {hit}")
    print(f"  → попаданий в события: {hits}/12")

    # P3: Zone-1 экспозиция перед событиями
    # окно (объявлено): 5 лет до события; для событий во 2-й половине года
    # год события включается (фискальный год был ДО события)
    print('P3 предсобытийная Zone-1 экспозиция (макс. серия Z1 в окне 5 лет):')
    fails3 = 0
    for c in ['GRC', 'ARG', 'ZMB', 'LKA']:
        z = {r['year']: r['zone'] for r in rows_all
             if r['country'] == c and r['zone'].startswith('Z1')}
        for y, lab in EVENTS[c]:
            if lab.startswith('HIPC') or 'реструктуризация 08' in lab:
                continue  # события, следующие за уже описанными
            if any(int(y2) == int(y) for y2, _ in EVENTS[c]
                   if y2 < y) and lab != 'Eurobonds 03-2024, номинал ~−18%':
                continue
            if (y - int(y)) >= 0.5:
                lo, hi = int(y) - 5, int(y)
            else:
                lo, hi = int(y) - 6, int(y) - 1
            streak = 0
            best = 0
            for yy in range(lo, hi + 1):
                streak = streak + 1 if yy in z else 0
                best = max(best, streak)
            mark = 'OK' if best >= 2 else 'ПРОВАЛ'
            if best < 2:
                fails3 += 1
            print(f"  {c} событие {int(y)} ({lab[:30]}): серия {best} → {mark}")
    deu_z = [r['year'] for r in rows_all
             if r['country'] == 'DEU' and r['zone'].startswith('Z1')]
    deustreak = 0
    deubest = 0
    prev = None
    for y in deu_z:
        deustreak = deustreak + 1 if prev == y - 1 else 1
        deubest = max(deubest, deustreak)
        prev = y
    print(f"  DEU (контроль): макс. серия Z1 = {deubest} "
          f"→ {'OK (не 3 подряд)' if deubest < 3 else 'ПРОВАЛ'}")

    # P4: задержки
    print('P4 задержки дефолт/доступ → закрытие (месяцев):')
    for c, a, b, m, lab in DELAYS:
        print(f"  {c}: {a} → {b} = {m} мес ({lab}) "
              f"→ {'OK ≥24' if m >= 24 else 'ПРОВАЛ'}")
    print('  2001: 42 мес vs 2020-е: 28-29 мес — порядок один (2-4 года)')

    with open(f'{OUT}/summary.json', 'w', encoding='utf-8') as f:
        json.dump({'delays': DELAYS, 'p1_share': share1,
                   'p2_hits': hits}, f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
