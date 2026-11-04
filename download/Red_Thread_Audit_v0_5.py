#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
RED THREAD AUDIT v0.5 — EX-ANTE ОПЕРАТОРЫ НА НЕЗАВИСИМОМ НАБОРЕ. Раунд 12.
Исполнение задания (6) из v5.0 (висит с v0.2, Task 18: «ex-ante операторы
списания/переоценки на независимом наборе кейсов, иначе подгонка»).
Набор НЕ пересекается с v0.2 и v0.4: UKR / TUR / BRA / PAK + контроль JPN.
ЕГИПЕТ ИСКЛЮЧЁН ДО ПРОГОНА (процессный фикс, объявлен после загрузки ДО
оценки): FM-серии pb/ie не содержат EGY вообще (добор по-одиночке вернул
пустую страну) — у страны с крупным долгом нет процентного счёта в базе;
правило «никакой интерполяции» → кейс не исполняется, пробел публикуется.

ЗАМОРОЖЕННЫЙ ГРАФ (вербатим v0.1/v0.2, не менялся с Task 18):
    d[t+1] = ((1+r)/(1+g)) · d[t] − pb        (d, pb в % ВВП; r, g в долях)
    r_real[t] = ((1 + ie[t]/d[t−1]) / (1 + π[t]/100)) − 1     (неявная)
SFA-РАЗЛОЖЕНИЕ ФАКТА (вербатим v0.4):
    resid[t] = Δd[t] − ( ((r_real[t]−g[t])/(1+g[t]))·d[t−1] − pb[t] )
    resid < 0 — деньги покинули сток: класс L9 (сброс/списание/выкуп);
    resid > 0 — сток пополнен извне: класс L3 (переоценка курса) /
    L6 (социализация/гарантии/арреары).

ВЕРДИКТ-РАМКА (предрегистрация, объявлена ДО вычисления остатков):
  PB1 КЛАСС ОТКАЗА ВОСПРОИЗВОДИТСЯ ВНЕ ВЫБОРКИ: совокупная доля «мирных»
      лет (|resid| ≤ 2 п.п., 2001–2024, год 2020 исключён как немирный для
      всех) < 60% — замороженный граф не воспроизводит мирные годы новых
      кейсов (закон v0.2 подтверждается на независимом наборе).
  PB2 КАЛЕНДАРЬ ОПЕРАТОРОВ EX-ANTE: события |resid| ≥ 5 п.п. (топ-10 по
      |resid| на территорию) соответствуют документированным операторам
      долга (реструктуризация/списание, девальвационная переоценка,
      социализация/гарантии, выкуп) в ≥ 70% случаев. Верификация
      веб-поиском ПОСЛЕ вычисления остатков, нейтральными запросами
      «территория + год»; окно совпадения ±1 год (процессный прецедент
      v0.2-P3: фискальные годы/тайминг данных).
  PB3 КОНТРОЛЬ СПЕЦИФИЧНОСТИ (JPN, без реструктуризаций в окне):
      max|resid| в 2001–2019 < 5 п.п. (2020 исключён заранее). Нарушение —
      не молчание метода, а его точность: событие именуется отдельно.
  PB4 ТАКСОНОМИЧЕСКОЕ ЗАМЫКАНИЕ (красная нить): после веб-верификации
      каждый подтверждённый оператор ≥5 п.п. классифицируется в таксономию
      кольца {L9 сброс, L3 переоценка, L6 социализация, неизвестное};
      доля «неизвестного» ≤ 30% — реальность не выходит за девять звеньев.

ЮНИТ-ТЕСТ ДО ПРОГОНА (класс E5): тождественный ряд (d=100 const, g=2%,
π=0, ie=2, pb=0) даёт resid = 0 с точностью 1e-9.
СТАТУС: E — исполнение объявленного задания; граф не подгонялся; все
остатки публикуются как есть (включая провальные).
=============================================================================
"""
import json
import csv
import os
import statistics as st

DATA = '/home/z/my-project/scripts/rta_v0_5_data'
OUT = '/home/z/my-project/scripts/rta_v0_5_out'
os.makedirs(OUT, exist_ok=True)

TERR = ['UKR', 'TUR', 'BRA', 'PAK', 'JPN']
NAMES = {'UKR': 'Украина', 'TUR': 'Турция', 'BRA': 'Бразилия',
         'PAK': 'Пакистан', 'JPN': 'Япония (контроль)'}
Y0, Y1 = 2000, 2024
NONPEACEFUL = {2020}          # COVID — немирный для всех (объявлено заранее)
PEACE_LO, PEACE_HI = 2001, 2019


def jload(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def dm(code):
    j = jload(f'{DATA}/dm_{code}.json')
    vals = j['values'][code]
    out = {}
    for t in TERR:
        src = vals.get(t)
        if not src and os.path.exists(f'{DATA}/dm_{code}_{t}.json'):
            src = jload(f'{DATA}/dm_{code}_{t}.json')['values'][code].get(t)
        if src:
            out[t] = {int(y): float(v) for y, v in src.items()
                      if v is not None}
    return out


def main():
    debt = dm('GGXWDG_NGDP')
    grw = dm('NGDP_RPCH')
    cpi = dm('PCPIPCH')
    pb = dm('pb')
    ie = dm('ie')

    # ---------- юнит-тест E5 (до прогона) ----------
    d_u, g_u, pb_u, ie_u, pi_u = 100.0, 0.02, 0.0, 2.0, 0.0
    r_u = (1.0 + ie_u / d_u) / (1.0 + pi_u / 100.0) - 1.0
    d_pred_u = ((1.0 + r_u) / (1.0 + g_u)) * d_u - pb_u
    assert abs(d_pred_u - 100.0) < 1e-9, f'ЮНИТ-ТЕСТ ПРОВАЛЕН: {d_pred_u}'
    resid_u = 0.0 - (((r_u - g_u) / (1.0 + g_u)) * d_u - pb_u)
    assert abs(resid_u) < 1e-9, 'ЮНИТ-ТЕСТ SFA ПРОВАЛЕН'
    print('ЮНИТ-ТЕСТ E5: тождественный ряд → resid = 0  OK')

    # ---------- неявная реальная ставка (вербатим v0.2) ----------
    r_real = {t: {} for t in TERR}
    i_nom = {t: {} for t in TERR}
    for t in TERR:
        last_pi = None
        for y in range(Y0, Y1 + 1):
            if y in cpi[t]:
                last_pi = cpi[t][y]
            pi = last_pi if last_pi is not None else 0.0
            if y - 1 in debt[t] and debt[t][y - 1] > 0.5 and y in ie[t]:
                i_nom[t][y] = ie[t][y] / debt[t][y - 1]
                r_real[t][y] = (1.0 + i_nom[t][y]) / (1.0 + pi / 100.0) - 1.0

    # ---------- SFA-разложение факта ----------
    rows = []
    sfa = {t: {} for t in TERR}
    for t in TERR:
        for y in range(Y0 + 1, Y1 + 1):
            if (y - 1 not in debt[t] or y not in debt[t] or y not in pb[t]
                    or y not in grw[t] or y not in r_real[t]):
                continue
            g = grw[t][y] / 100.0
            pred_d = ((r_real[t][y] - g) / (1.0 + g)) * debt[t][y - 1] \
                - pb[t][y]
            resid = (debt[t][y] - debt[t][y - 1]) - pred_d
            sfa[t][y] = resid
            rows.append({
                'territory': t, 'year': y,
                'd_prev': round(debt[t][y - 1], 2),
                'd': round(debt[t][y], 2),
                'i_nom_pct': round(i_nom[t][y] * 100, 2),
                'r_real_pct': round(r_real[t][y] * 100, 2),
                'g_pct': round(grw[t][y], 2),
                'pi_pct': round(cpi[t].get(y, float('nan')), 2)
                if y in cpi[t] else '',
                'pb': round(pb[t][y], 2), 'ie': round(ie[t][y], 2),
                'resid_pp': round(resid, 2)})

    # ---------- PB1: мирные годы ----------
    peace_all, tot_all = 0, 0
    peace_by = {}
    print('\n=== PB1: мирные годы (|resid| ≤ 2 п.п.), 2020 исключён ===')
    for t in TERR:
        yrs = [y for y in sfa[t] if y not in NONPEACEFUL]
        n_ok = sum(1 for y in yrs if abs(sfa[t][y]) <= 2.0)
        peace_by[t] = (n_ok, len(yrs))
        peace_all += n_ok
        tot_all += len(yrs)
        print(f'  {t}: {n_ok}/{len(yrs)} = {n_ok/len(yrs)*100:.0f}%')
    agg = peace_all / tot_all
    print(f'  АГРЕГАТ: {peace_all}/{tot_all} = {agg*100:.1f}% '
          f"→ PB1 {'ПОДТВЕРЖДЕНА' if agg < 0.60 else 'ОТКЛОНЕНА'} "
          f'(порог < 60%)')

    # ---------- PB2: календарь ex-ante (топ-10 по |resid|) ----------
    print('\n=== PB2: КАЛЕНДАРЬ ОПЕРАТОРОВ (объявлен до веб-верификации) ===')
    calendar = {}
    for t in TERR:
        ev = sorted(sfa[t].items(), key=lambda kv: -abs(kv[1]))
        ev = [(y, v) for y, v in ev if abs(v) >= 5.0][:10]
        calendar[t] = []
        for y, v in ev:
            cls = ('L9-сброс' if v < 0 else
                   'L3-переоценка/L6-социализация')
            calendar[t].append({'year': y, 'resid_pp': round(v, 2),
                                'ring_class': cls})
        s = '; '.join(f"{y}:{v:+.1f}[{'−сброс' if v < 0 else '+вход'}]"
                      for y, v in ev)
        print(f'  {t}: {s if s else "— нет событий ≥5 п.п. —"}')
    n_ev = sum(len(c) for c in calendar.values())
    print(f'  всего событий ≥5 п.п.: {n_ev} — передача на веб-верификацию')

    # ---------- PB3: контроль JPN ----------
    jpn_peace = [abs(sfa['JPN'][y]) for y in range(PEACE_LO, PEACE_HI + 1)
                 if y in sfa['JPN'] and y not in NONPEACEFUL]
    jpn_max = max(jpn_peace) if jpn_peace else 0.0
    print(f"\n=== PB3: JPN мирные 2001–2019: max|resid| = {jpn_max:.2f} п.п. "
          f"→ PB3 {'ПОДТВЕРЖДЕНА' if jpn_max < 5.0 else 'ОТКЛОНЕНА'} "
          f'(порог < 5)')
    if jpn_max >= 5.0:
        bad = [(y, round(sfa['JPN'][y], 2))
               for y in range(PEACE_LO, PEACE_HI + 1)
               if y in sfa['JPN'] and abs(sfa['JPN'][y]) >= 5.0]
        print(f'  события контроля (требуют именования): {bad}')

    # ---------- CSV + JSON ----------
    with open(f'{OUT}/results.csv', 'w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    summary = {
        'prereg': {'PB1': agg < 0.60, 'PB2': None, 'PB3': jpn_max < 5.0,
                   'PB4': None},
        'peaceful_share': {t: round(peace_by[t][0] / peace_by[t][1], 3)
                           for t in TERR},
        'peaceful_share_agg': round(agg, 3),
        'calendar': calendar,
        'n_events': n_ev,
        'jpn_max_peaceful_pp': round(jpn_max, 2),
        'sfa_full': {t: {str(y): round(v, 2) for y, v in sorted(
            sfa[t].items())} for t in TERR},
        'meta': {'graph': 'd[t+1]=((1+r)/(1+g))·d[t]−pb, вербатим v0.1',
                 'egy_excluded': 'FM pb/ie не содержат EGY (нет в датамаппере)',
                 'fetch': 'IMF datamapper, rta_v0_5_data, 2026-09-08'},
    }
    with open(f'{OUT}/summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    import hashlib
    h = hashlib.sha256(
        open(f'{OUT}/summary.json', 'rb').read()).hexdigest()
    print(f'\nCSV: {OUT}/results.csv ({len(rows)} строк)')
    print(f'sha256(summary.json) = {h[:12]}…')
    print('КАЛЕНДАРЬ ГОТОВ — следующий шаг: веб-верификация событий '
          '(нейтральные запросы, вердикты публикуются целиком).')


if __name__ == '__main__':
    main()
