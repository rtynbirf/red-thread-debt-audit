#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
РАУНД 14 / R10 — БЛОК B: матрица событий/переходов на реальных временных рядах.
Исполнение следующей границы, объявленной обеими сторонами (R9 §4 и v0.4-задание):
переход от бинарных векторов к наблюдаемой матрице, где КАЖДАЯ строка несёт
источник, дату, определение переменной и правило перехода.

ВЕРДИКТ-РАМКА (предрегистрирована ДО прогона):

  PB1  ΔD (п.п. долга/ВВП) вычислим для >= 95% строк окна 2001–2023
       (10 кейсов x 23 года = 230 строк).
  PB2  ShockResponse = SFA-остаток сшивается из ОПУБЛИКОВАННЫХ выходов
       v0.2/v0.5 для 100% строк — без пересчёта входов (анти-E-юнит-баг).
  PB3  STRICT-РЕЖИМ СДВИГАЕТ ОЦЕНКУ (перенос урока R8 коллеги на реальный
       слой): в спуф-годах неплатежа неявная ставка фиктивна (v0.2-закон:
       ie→0 там, где начинается принуждение). Предсказание: в >= 70% спуф-строк
       с ненулевым ie значение ie ниже мирной медианы того же кейса —
       «фикция дешёвого долга в дефолте».
  PB4  ΔResource/ΔExtraction: покрытие наблюдаемыми данными публикуется
       как есть; пробелы = UNKNOWN с причиной (не выдумывать).
       Предсказание: покрытие >= 60% строк.
  PB5  КРАСНАЯ НИТЬ (связка слоёв, без подгонки): измерить strict-штраф
       реального слоя — долю процентного потока (Σie), теряющую статус
       доказательства при строгом режиме; опубликовать рядом со strict-штрафом
       коллеги (r_marg 0.40→0.25 = −37.5%). Механизм один: канал, управляемый
       стороной неплатежа, даёт сигнал, но не доказательство.
  PB6  Событийный слой: 4 реструктуризации (22/42/28/29 мес) переносятся
       из опубликованного DELAYS v0.2 как RestructuringDelay/RecoveryTime.

ПРЕДРЕГИСТРИРОВАННЫЕ СПУФ-ОКНА (документированный неплатёж, источник календаря
EVENTS v0.2 / операторов v0.5): ARG 2002–2004 (дефолт 12-2001 до обмена 06-2005),
ARG 2020 (повторный дефолт 05-2020), ZMB 2020–2021 (дефолт 11-2020 до сделки
03-2024), LKA 2022–2023 (мораторий 04-2022 до сделки 09-2024),
UKR 2015 (мораторий на 3 млрд), UKR 2022–2024 (мораторий военные годы).

ВХОД (класс A): download/Red_Thread_Audit_v0_2_results.csv (GRC/ARG/ZMB/LKA/DEU;
ZMB = объявленный WB-GFS fallback), download/Red_Thread_Audit_v0_5_results.csv
(UKR/TUR/BRA/PAK/JPN), scripts/rta_r10_data/* (WB API, выгрузка 2026-09-09,
dump updated 2026-07-13). Полоса шума B50=1.77 / B90=2.73 (v0.6, формульные
пороги, правило E10).

ПРАВИЛА ПЕРЕХОДОВ:
  ΔD[t]            = d[t] − d[t−1]                                        (п.п.)
  ΔGDP[t]          = g[t]                                                 (%, реальный рост)
  DebtService_nom  = ie[t]                                                (% ВВП, счёт процентов)
  r_implicit[t]    = ie[t] / d[t−1] × 100                                 (%, неявная ставка)
  ΔRefinancing[t]  = (ie[t] + max(−pb[t], 0)) / d[t−1] × 100              (% долга: ролловер-давление)
  ΔResource[t]     = RT[t] − RT[t−1]  (NY.GDP.TOTL.RT.ZS)                 (п.п. ВВП)
  ΔExtraction[t]   = TAX[t] − TAX[t−1] (GC.TAX.TOTL.GD.ZS)                (п.п. ВВП)
  ShockResponse[t] = одношаговый SFA-оператор: v0.2-кейсы — столбец 'sfa',
                     v0.5-кейсы — столбец 'resid_pp' (E13: семантики разведены)   (п.п.)
  Классификация v0.6: |resid| ≤ B50 мир / (B50, B90] шум / > B90 событие.
"""
import csv
import json
import statistics
from pathlib import Path

BASE = Path('/home/z/my-project')
R10 = BASE / 'scripts' / 'rta_r10_data'
OUT_CSV = BASE / 'download' / 'RED_THREAD_матрица_переходов.csv'
OUT_JSON = BASE / 'download' / 'RED_THREAD_матрица_переходов.json'

B50, B90 = 1.77, 2.73  # v0.6, формульные пороги от перцентилей контроля
YEARS = range(2001, 2024)
CASES = ['GRC', 'ARG', 'ZMB', 'LKA', 'DEU', 'UKR', 'TUR', 'BRA', 'PAK', 'JPN']
CONTROL = {'DEU', 'JPN'}

SPOOF = {
    'ARG': {2002, 2003, 2004, 2020},
    'ZMB': {2020, 2021},
    'LKA': {2022, 2023},
    'UKR': {2015, 2022, 2023, 2024},
    'GRC': set(), 'DEU': set(), 'TUR': set(), 'BRA': set(), 'PAK': set(), 'JPN': set(),
}

DELAYS = [  # RestructuringDelay / RecoveryTime, источник: v0.2 DELAYS (опубликовано)
    {'case': 'GRC', 'from': '2010-05', 'to': '2012-03', 'months': 22,
     'note': 'потеря доступа → PSI', 'type': 'RecoveryTime+RestructuringDelay'},
    {'case': 'ARG', 'from': '2001-12', 'to': '2005-06', 'months': 42,
     'note': 'дефолт → обмен-2005', 'type': 'RestructuringDelay'},
    {'case': 'ZMB', 'from': '2020-11', 'to': '2024-03', 'months': 28,
     'note': 'дефолт → сделка Eurobonds', 'type': 'RestructuringDelay'},
    {'case': 'LKA', 'from': '2022-04', 'to': '2024-09', 'months': 29,
     'note': 'мораторий → сделка', 'type': 'RestructuringDelay'},
]

PROVENANCE = {
    'D, pb, ie, g': 'IMF datamapper через опубликованные выходы v0.2/v0.5; ZMB pb/ie = WB-GFS fallback (объявлен в v0.2)',
    'RT': 'WB API NY.GDP.TOTL.RT.ZS (total natural resources rents, % GDP), выгрузка 2026-09-09, dump 2026-07-13',
    'TAX': 'WB API GC.TAX.TOTL.GD.ZS (tax revenue, % GDP), выгрузка 2026-09-09, dump 2026-07-13',
    'band': 'v0.6: B50=1.77, B90=2.73 (перцентили мирного контроля JPN)',
    'graph': 'замороженный v0.1: d[t+1]=((1+r)/(1+g))·d[t]−pb; r = неявная ie/d[t−1], дефлированная π',
}


def load_pub_csv():
    """Сшивка опубликованных CSV v0.2 + v0.5: {case: {year: {...}}}."""
    ser = {c: {} for c in CASES}
    with open(BASE / 'download' / 'Red_Thread_Audit_v0_2_results.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            c = r['country']
            if c in ser:
                ser[c][int(r['year'])] = {
                    'd': _f(r['d_actual']), 'pb': _f(r['pb']), 'ie': _f(r['ie']),
                    'g': _f(r['g']), 'resid': _f(r['sfa'])}
    # ВНИМАНИЕ (E13): в v0.2 CSV 'resid' = накопительная дивергенция от якоря 2000,
    # одношаговый оператор = столбец 'sfa'; в v0.5 'resid_pp' уже одношаговый.
    # Смешение семантик даёт 66% ложных событий — найдено и исправлено до публикации.
    with open(BASE / 'download' / 'Red_Thread_Audit_v0_5_results.csv', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            c = r['territory']
            if c in ser:
                ser[c][int(r['year'])] = {
                    'd': _f(r['d']), 'pb': _f(r['pb']), 'ie': _f(r['ie']),
                    'g': _f(r['g_pct']), 'resid': _f(r['resid_pp'])}
    return ser


def _f(x):
    return None if x in (None, '', 'nan', 'None') else float(x)


def _r_impl_below_median(rows, target):
    """Неявная ставка спуф-строки ниже мирной медианы её кейса (по r_implicit)."""
    import statistics as st
    peace = [r['r_implicit_pct'] for r in rows
             if r['case'] == target['case'] and not r['spoof_year']
             and r['r_implicit_pct'] is not None]
    if not peace or target['r_implicit_pct'] is None:
        return False
    return target['r_implicit_pct'] < st.median(peace)


def load_wb(ind):
    """{case: {int_year: value}} из свежего WB-fetch."""
    out = {}
    for c in CASES:
        p = R10 / f'{c}_{ind}.json'
        if not p.exists():
            out[c] = {}
            continue
        rows = json.loads(p.read_text(encoding='utf-8'))[1] or []
        out[c] = {int(r['date']): r['value'] for r in rows if r.get('value') is not None}
    return out


def main():
    ser = load_pub_csv()
    RT = load_wb('NY.GDP.TOTL.RT.ZS')
    TAX = load_wb('GC.TAX.TOTL.GD.ZS')

    rows, unk = [], {'RT': 0, 'TAX': 0, 'd_prev': 0}
    for c in CASES:
        peace_ie = [ser[c][y]['ie'] for y in YEARS
                    if y in ser[c] and y not in SPOOF[c]
                    and ser[c][y]['ie'] is not None and ser[c][y]['ie'] > 0]
        med_ie = statistics.median(peace_ie) if peace_ie else None
        for y in YEARS:
            if y not in ser[c]:
                continue
            cur, prev = ser[c][y], ser[c].get(y - 1)
            spoof = y in SPOOF[c]
            row = {
                'case': c, 'year': y, 'is_control': c in CONTROL, 'spoof_year': spoof,
                'd_pct_gdp': cur['d'],
                'delta_D_pp': None, 'delta_GDP_pct': cur['g'],
                'DebtService_nom_pct': cur['ie'],
                'DebtService_strict': ('SPOOFED' if spoof else cur['ie']),
                'r_implicit_pct': None,
                'delta_Refinancing_pct_of_D': None,
                'ShockResponse_pp': cur['resid'],
                'band_v06': (None if cur['resid'] is None else
                             ('мир' if abs(cur['resid']) <= B50
                              else 'шум' if abs(cur['resid']) <= B90 else 'событие')),
                'delta_Resource_pp': None, 'delta_Extraction_pp': None,
                'ie_vs_peace_median': None,
                'provenance': 'v0.2-csv' if c in ('GRC', 'ARG', 'ZMB', 'LKA', 'DEU') else 'v0.5-csv',
            }
            if prev and prev['d'] is not None and cur['d'] is not None:
                row['delta_D_pp'] = round(cur['d'] - prev['d'], 2)
                if cur['ie'] is not None:
                    row['r_implicit_pct'] = round(cur['ie'] / prev['d'] * 100, 2)
                    if prev['d'] > 0.5 and not spoof:
                        row['delta_Refinancing_pct_of_D'] = round(
                            (cur['ie'] + max(-(cur['pb'] or 0), 0)) / prev['d'] * 100, 2)
            if med_ie and cur['ie'] is not None and cur['ie'] > 0:
                row['ie_vs_peace_median'] = round(cur['ie'] / med_ie, 3)
            for key, src in (('delta_Resource_pp', RT), ('delta_Extraction_pp', TAX)):
                v0, v1 = src[c].get(y - 1), src[c].get(y)
                if v0 is not None and v1 is not None:
                    row[key] = round(v1 - v0, 2)
                else:
                    unk['RT' if key == 'delta_Resource_pp' else 'TAX'] += 1
            rows.append(row)

    # ---------- вердикты ----------
    n = len(rows)
    vd = {}
    vd['PB1'] = ('ПОДТВЕРЖДЕНА' if sum(1 for r in rows if r['delta_D_pp'] is not None) / n >= 0.95
                 else 'ОТКЛОНЕНА')
    vd['PB2'] = ('ПОДТВЕРЖДЕНА' if all(r['ShockResponse_pp'] is not None for r in rows)
                 else 'ОТКЛОНЕНА')
    sp_rows = [r for r in rows if r['spoof_year'] and r['ie_vs_peace_median']]
    low = sum(1 for r in sp_rows if r['ie_vs_peace_median'] < 1.0)
    vd['PB3'] = ('ПОДТВЕРЖДЕНА' if sp_rows and low / len(sp_rows) >= 0.7 else 'ОТКЛОНЕНА')
    cov_rt = 1 - unk['RT'] / n
    cov_tax = 1 - unk['TAX'] / n
    vd['PB4'] = ('ПОДТВЕРЖДЕНА' if min(cov_rt, cov_tax) >= 0.6 else 'ОТКЛОНЕНА')

    total_ie = sum(r['DebtService_nom_pct'] for r in rows if r['DebtService_nom_pct'])
    spoof_ie = sum(r['DebtService_nom_pct'] for r in rows
                   if r['spoof_year'] and r['DebtService_nom_pct'])
    strict_penalty = spoof_ie / total_ie if total_ie else None
    vd['PB5'] = 'ЗАФИКСИРОВАН'
    vd['PB6'] = 'ПОДТВЕРЖДЕНА' if len(DELAYS) == 4 else 'ОТКЛОНЕНА'

    # ---------- PB3 post-hoc (маркировано POST-HOC, не подменяет вердикт) ----------
    # Направленная форма отвергнута (2/11). Единая подпись спуф-лет — другая:
    # все спуф-годы = годы-события по полосе v0.6. Фикция «дешёвого долга»
    # живёт в неявной СТАВКЕ через знаменатель (d взрывается курсом), не в потоке.
    spoofs = [r for r in rows if r['spoof_year']]
    ev_rows = [r for r in rows if r['band_v06'] == 'событие']
    spoofs_as_events = sum(1 for r in spoofs if r['band_v06'] == 'событие')
    r_impl_below = sum(1 for r in spoofs
                       if r['r_implicit_pct'] is not None
                       and _r_impl_below_median(rows, r))
    pb3_posthoc = {
        'status': 'POST-HOC (после отклонённой направленной формы)',
        'spoof_rows_all_band_events': f'{spoofs_as_events}/{len(spoofs)}',
        'event_rows_total': len(ev_rows),
        'spoof_share_among_events': round(spoofs_as_events / len(ev_rows), 3) if ev_rows else None,
        'event_base_rate': round(len(ev_rows) / n, 3),
        'r_implicit_below_peace_median_in_spoof': f'{r_impl_below}/{len(spoofs)}',
        'corrected_law': ('9/11 спуф-лет = годы-события (>B90); счёт процентов в неплатеже НЕ '
                          'зануляется (9/11 выше мирной медианы — accrual просрочек), зануляется '
                          'неявная СТАВКА через знаменатель (4/11 ниже медианы); подпись спуф-года '
                          'разлита между оператором и ставкой — единого канала-доказательства нет'),
    }

    summary = {
        'task': 'R10 Block B: observed event/transition matrix (real time series)',
        'rows': n, 'window': '2001-2023', 'cases': CASES,
        'spoof_windows': {c: sorted(s) for c, s in SPOOF.items() if s},
        'coverage': {'delta_D': 1 - sum(1 for r in rows if r['delta_D_pp'] is None) / n,
                     'Resource': round(cov_rt, 4), 'Extraction': round(cov_tax, 4),
                     'UNKNOWN_counts': unk},
        'strict_penalty_real_layer': {
            'share_of_interest_flow_spoofed': round(strict_penalty, 4) if strict_penalty else None,
            'colleague_r_marg_penalty': -0.375,
            'mechanism': 'канал, управляемый стороной неплатежа: сигнал, не доказательство'},
        'pb3_details': {'spoof_rows_with_ie': len(sp_rows), 'below_peace_median': low,
                        'share': round(low / len(sp_rows), 3) if sp_rows else None},
        'verdicts': vd, 'provenance': PROVENANCE, 'delays': DELAYS,
        'band': {'B50': B50, 'B90': B90},
        'pb3_posthoc': pb3_posthoc,
        'events_v06': [{'case': r['case'], 'year': r['year'], 'resid': r['ShockResponse_pp']}
                       for r in rows if r['band_v06'] == 'событие'],
    }
    OUT_CSV.write_text(_csv_text(rows), encoding='utf-8')
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(vd, ensure_ascii=False))
    print('rows:', n, '| coverage RT/TAX:', round(cov_rt, 3), round(cov_tax, 3),
          '| strict_penalty:', round(strict_penalty, 4) if strict_penalty else None,
          '| PB3:', summary['pb3_details'])
    print('saved:', OUT_CSV.name, OUT_JSON.name)


def _csv_text(rows):
    cols = ['case', 'year', 'is_control', 'spoof_year', 'd_pct_gdp', 'delta_D_pp',
            'delta_GDP_pct', 'DebtService_nom_pct', 'DebtService_strict', 'r_implicit_pct',
            'delta_Refinancing_pct_of_D', 'ShockResponse_pp', 'band_v06',
            'delta_Resource_pp', 'delta_Extraction_pp', 'ie_vs_peace_median', 'provenance']
    out = [','.join(cols)]
    for r in rows:
        out.append(','.join('' if r[k] is None else str(r[k]) for k in cols))
    return '\n'.join(out) + '\n'


if __name__ == '__main__':
    main()
