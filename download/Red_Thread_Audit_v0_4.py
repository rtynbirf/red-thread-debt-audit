#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
RED THREAD AUDIT v0.4 — РАСКРЫТИЕ ПЕРИМЕТРА + ПАРАМЕТРИЧЕСКАЯ ИДЕНТИФИКАЦИЯ
+ R7 INVARIANCE TEST + WALK-FORWARD BACKTEST.
Исполнение объявленных и НЕисполненных задач ПОЛИМАТА (три документа
раунда: «ЗАДАЧА ПОЛИМАТА», «Первый удар…порог 77%», «ОТЧЁТ v0.2»):
  (α) REDTHREAD v0.4 PARAMETER IDENTIFICATION — θ-вектор на территорию,
      замороженный граф → 2031, DIFF против официального пути и против
      ЛИНЕЙНОГО КОНТРОЛЯ Полимата (его v0.3 вербатим: тренд 2024→2026).
  (β) AUDIT v0.4 «РАСКРЫТИЕ ПЕРИМЕТРА» — слоёный долг: ядро (API, A) +
      частный слой (WB API, A) + расширенный периметр КНР (C-якоря Полимата
      с IMF-ссылками); прогон ТОГО ЖЕ графа на расширенном периметре.
  (γ) R7 INVARIANCE TEST — единая матрица признаков для RUS/USA/CHN/EUR,
      попарные Δ между четырьмя реальными графами, кластеризация,
      карта «измерено / не измерено» по 12 Δ-контролям.
  (δ) WALK-FORWARD BACKTEST 2005–2025 (требование Полимата из «ОТЧЁТ v0.2»
      §«следующий правильный шаг») — один шаг вперёд только на данных,
      доступных к предыдущему году; RMSE против наивного.
=============================================================================
ЗАМОРОЖЕННЫЙ ГРАФ (вербатим v0.1/v0.2, НЕ меняется ни при каком результате):
    d[t+1] = ((1+r)/(1+g)) · d[t] − pb
    r_real[t] = ((1 + ie[t]/d_act[t−1]) / (1 + π[t]/100)) − 1   (неявная)
РЕЦЕПТЫ (объявлены единообразно для всех четырёх территорий):
    факт = годы ≤ 2025; 2026+ = официальный путь IMF (та же серия API).
    ПРОЦЕССНЫЙ ФИКС (объявлен после загрузки, ДО прогона, единообразно):
    FM-серии pb/ie в датамаппере заканчиваются 2024 годом → окно θ =
    последние 3 доступных года ВСЕХ серий: 2022–2024 (основное);
    чувствительность: 2021–2024 (публикуется целиком).
    g в долях (NGDP_RPCH/100); pb — % ВВП, вербатим v0.1 (соглашение
    зафиксировано в v0.2 Task 18 и не пересматривается).
    EUR: d/g/π = агрегат EURO = еврозона (WEO, A; скоуп-ключ верифицирован
    по совпадению с опубликованными Полиматом цифрами 87.1→89.7;
    ключ EUQ отвергнут как не-еврозона — процессный фикс ДО прогона);
    pb/ie = взвешенное среднее 20 членов еврозоны по NGDPD-2025 (правило
    объявлено ДО загрузки; веса фикс).
    КНР расширенный периметр (C-якоря Полимата): 2024=117.0, 2026=135.3,
    2031=153.7, 2034≈162.7 (IMF augmented debt; статус C, не переверно мной).
    РФ маржинальная ставка (C-якорь Полимата из ЦБ): средняя ключевая
    2026 = 14.5–14.6%.
ПРЕДИСТОРИЯ (объявлена ДО прогона, статусы проставляет машина):
  P1  Операторный прогон (окно θ 2022–2024, процессный фикс объявлен)
      ближе к официальному 2031, чем линейный контроль Полимата,
      минимум для 2 из 4 территорий.
  P1b Для RUS и EUR |DIFF_op| ≤ 8 п.п.
  P2  (а) r_imp − g для CHN < 0; (б) для РФ маржинально-неявной разрыв
      r_marg_nom − r_imp_nom ≥ 5 п.п. (репрайсинг — недостающий член
      оператора); (в) репрайсинг США виден в потоке: ie(последний
      доступный год ≤2024) > 1.3·ie(2021).
  P3  Перенос того же θ_КНР на расширенный периметр НЕ воспроизводит
      официальный augmented-путь: |d_aug_op(2031) − 153.7| ≥ 5 п.п.
  P4  Отношение частный-кредит/публичное-ядро (процессный фикс,
      объявлен после загрузки ДО оценки: WB-серия частного кредита по
      РФ оборвана в 2021 → отношение считается на последнем общем
      доступном году каждой территории, год публикуется): РФ
      максимальна из четырёх и ≥ 3 (нагрузка РФ живёт не на государстве).
  P5  Walk-forward: RMSE_оператора < RMSE_наивного для RUS (2005–2025).
  P6  R7: в нормированном признаковом пространстве ближайшие пары —
      (USA,CHN) и (RUS,EUR).
СТАТУС: E — исполнение объявленных задач; граф не подгонялся; все DIFF
и остатки публикуются как есть (включая провальные).
=============================================================================
"""
import json
import csv
import os
import statistics as st

DATA = '/home/z/my-project/scripts/rta_v0_4_data'
OUT = '/home/z/my-project/scripts/rta_v0_4_out'
os.makedirs(OUT, exist_ok=True)

TERR = ['RUS', 'USA', 'CHN', 'EUR']
NAMES = {'RUS': 'Россия', 'USA': 'США', 'CHN': 'Китай', 'EUR': 'Еврозона'}
EA_MEMBERS = ['AUT', 'BEL', 'CYP', 'EST', 'FIN', 'FRA', 'DEU', 'GRC', 'IRL',
              'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 'PRT', 'SVK', 'SVN',
              'ESP', 'HRV']
Y0, Y1_ACT = 2000, 2025          # факт ≤ 2025
Y_F1, Y_F2 = 2026, 2031          # официальный путь
AUG_CN = {2024: 117.0, 2026: 135.3, 2031: 153.7, 2034: 162.7}  # C-якорь
RUS_R_MARG = 14.55               # C-якорь Полимата (ЦБ, средняя ключевая 2026)


def jload(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def dm(code, per_country=False):
    """datamapper: {territory: {year:int: value}}"""
    fn = f'{DATA}/dm_{code}_{TERR[3]}.json' if False else f'{DATA}/dm_{code}.json'
    j = jload(fn)
    vals = j['values'][code]
    out = {}
    for t in TERR:
        key = 'EURO' if t == 'EUR' else t
        if key in vals:
            out[t] = {int(y): v for y, v in vals[key].items()
                      if v is not None}
    return out


def fm_euro_weighted(code, weights):
    """FM-серии не содержат агрегата еврозоны: фиксированные веса NGDPD-2025,
    перенормировка на доступные члены каждого года (правило объявлено)."""
    j = jload(f'{DATA}/dm_{code}.json')
    vals = j['values'][code]
    years = set()
    for m in EA_MEMBERS:
        years |= {int(y) for y in vals.get(m, {}) if vals[m].get(y) is not None}
    out = {}
    for y in sorted(years):
        num = den = 0.0
        for m in EA_MEMBERS:
            v = vals.get(m, {}).get(str(y))
            if v is None:
                continue
            num += weights.get(m, 0.0) * float(v)
            den += weights.get(m, 0.0)
        if den > 0:
            out[y] = num / den
    return out


def wb_priv(t):
    fn = f'{DATA}/wb_priv_{"EUR" if t == "EUR" else t}.json'
    d = jload(fn)
    rows = d[1] if isinstance(d, list) and len(d) > 1 else []
    return {int(x['date']): float(x['value']) for x in rows
            if x.get('value') is not None}


def main():
    # ---------- данные ----------
    debt = dm('GGXWDG_NGDP')
    grw = dm('NGDP_RPCH')
    cpi = dm('PCPIPCH')
    gdp_w = jload(f'{DATA}/dm_NGDPD.json')['values']['NGDPD']
    w = {m: float(gdp_w.get(m, {}).get('2025') or 0.0) for m in EA_MEMBERS}
    pb = dm('pb')
    pb['EUR'] = fm_euro_weighted('pb', w)
    ie = dm('ie')
    ie['EUR'] = fm_euro_weighted('ie', w)
    priv = {t: wb_priv(t) for t in TERR}

    # неявная реальная ставка (вербатим v0.2 Task 18)
    r_real = {t: {} for t in TERR}
    i_nom = {t: {} for t in TERR}
    for t in TERR:
        last_pi = None
        for y in range(Y0, Y1_ACT + 1):
            if y in cpi[t]:
                last_pi = cpi[t][y]
            pi = last_pi if last_pi is not None else 0.0
            if y - 1 in debt[t] and debt[t][y - 1] > 0.5 and y in ie[t]:
                i_nom[t][y] = ie[t][y] / debt[t][y - 1]
                r_real[t][y] = (1.0 + i_nom[t][y]) / (1.0 + pi / 100.0) - 1.0

    # ---------- ПРЕДИСТОРИЯ: печать объявлений ДО вычисления результатов ----
    print('=' * 74)
    print('ПРЕДИСТОРИЯ P1–P6 объявлена ДО прогона (см. докстринг); граф')
    print('d[t+1]=((1+r)/(1+g))·d[t]−pb не меняется. Статусы проставит машина.')
    print('=' * 74)

    # ---------- (α) θ и операторный прогон ----------
    def theta(t, lo, hi):
        rr = [r_real[t][y] for y in range(lo, hi + 1) if y in r_real[t]]
        gg = [grw[t][y] / 100.0 for y in range(lo, hi + 1)
              if y in grw[t] and grw[t][y] > -99.0]
        pp = [pb[t][y] for y in range(lo, hi + 1) if y in pb[t]]
        return (st.median(rr), st.median(gg), st.median(pp))

    def run_frozen(t, r, g, p, y_start=2025):
        d = debt[t][y_start]
        path = {y_start: d}
        for y in range(y_start + 1, Y_F2 + 1):
            d = ((1.0 + r) / (1.0 + g)) * d - p
            path[y] = d
        return path

    res = {}
    print('\n=== (α) PARAMETER IDENTIFICATION: θ и DIFF 2031 ===')
    print('терр | r_imp%  g%     pb%   | d2025 | оп2031 | лин2031 | IMF2031'
          ' | DIFFоп | DIFFлин')
    for t in TERR:
        r3, g3, p3 = theta(t, 2022, 2024)   # процессный фикс окна (объявлен)
        r5, g5, p5 = theta(t, 2021, 2024)   # чувствительность
        op3 = run_frozen(t, r3, g3, p3)
        op5 = run_frozen(t, r5, g5, p5)
        # линейный контроль Полимата (v0.3 вербатим): тренд 2024→2026 → 2031
        trend = (debt[t][2026] - debt[t][2024]) / 2.0
        lin31 = debt[t][2026] + 5.0 * trend
        imf31 = debt[t][Y_F2]
        res[t] = dict(r3=r3, g3=g3, p3=p3, r5=r5, g5=g5, p5=p5,
                      op3=op3, op5=op5, lin31=lin31, imf31=imf31,
                      diff_op=op3[2031] - imf31, diff_lin=lin31 - imf31)
        print(f'{t} | {r3*100:5.2f}  {g3*100:5.2f} {p3:6.2f} | '
              f'{debt[t][2025]:5.1f} | {op3[2031]:6.1f} | {lin31:7.1f} | '
              f'{imf31:7.1f} | {res[t]["diff_op"]:+6.1f} | '
              f'{res[t]["diff_lin"]:+6.1f}')
    beats = sum(1 for t in TERR
                if abs(res[t]['diff_op']) < abs(res[t]['diff_lin']))
    ok1 = beats >= 2
    ok1b = all(abs(res[t]['diff_op']) <= 8.0 for t in ('RUS', 'EUR'))
    print(f'P1  оператор бьёт линейный контроль: {beats}/4 '
          f"→ {'ПОДТВЕРЖДЕНА' if ok1 else 'ОТКЛОНЕНА'}")
    print(f'P1b |DIFF_op|≤8пп RUS/EUR: RUS {res["RUS"]["diff_op"]:+.1f}, '
          f'EUR {res["EUR"]["diff_op"]:+.1f} '
          f"→ {'ПОДТВЕРЖДЕНА' if ok1b else 'ОТКЛОНЕНА'}")

    # P2: знаки, репрайсинг-разрыв, поток процентов
    rg = {t: res[t]['r3'] - res[t]['g3'] for t in TERR}
    r_imp_nom_rus = st.median([i_nom['RUS'][y] for y in (2022, 2023, 2024)
                               if y in i_nom['RUS']]) * 100
    r_gap = RUS_R_MARG - r_imp_nom_rus
    y_last_ie = max(y for y in ie['USA'] if y <= 2024)
    ie_usa = {'2021': ie['USA'].get(2021), 'last': ie['USA'][y_last_ie],
              'y_last': y_last_ie}
    p2a = rg['CHN'] < 0
    p2b = r_gap >= 5.0
    p2c = ie_usa['2021'] is not None and ie_usa['last'] is not None \
        and ie_usa['last'] > 1.3 * ie_usa['2021']
    print(f'P2a r−g CHN = {rg["CHN"]*100:+.2f} п.п. '
          f"→ {'OK' if p2a else 'ПРОВАЛ'}")
    print(f'P2b РФ: r_marg_nom {RUS_R_MARG:.2f}% − r_imp_nom '
          f'{r_imp_nom_rus:.2f}% = {r_gap:+.2f} п.п. → {"OK" if p2b else "ПРОВАЛ"}')
    print(f'P2c USA ie 2021→{y_last_ie}: {ie_usa["2021"]:.2f}→'
          f'{ie_usa["last"]:.2f} '
          f'({ie_usa["last"]/ie_usa["2021"]:.2f}×) → {"OK" if p2c else "ПРОВАЛ"}')

    # ---------- (β) ПЕРИМЕТР ----------
    print('\n=== (β) РАСКРЫТИЕ ПЕРИМЕТРА ===')
    peri = {}
    for t in TERR:
        # процессный фикс P4 (объявлен): последний общий доступный год
        y_last = min(max(y for y in priv[t] if y <= Y1_ACT),
                     max(y for y in debt[t] if y <= Y1_ACT))
        pv = priv[t].get(y_last)
        peri[t] = dict(core=debt[t][y_last], priv=pv, y_last=y_last,
                       ratio=(pv / debt[t][y_last]) if pv else None)
    for t in TERR:
        p = peri[t]
        pp = f'{p["priv"]:.1f}' if p['priv'] else 'н/д'
        rt = f'{p["ratio"]:.2f}' if p['ratio'] else 'н/д'
        print(f'{t} (год {p["y_last"]}): ядро {p["core"]:.1f}%  '
              f'частный {pp}%  частное/ядро {rt}')
    ratios = {t: peri[t]['ratio'] for t in TERR if peri[t]['ratio']}
    rus_max = ratios and max(ratios, key=ratios.get) == 'RUS' \
        and ratios['RUS'] >= 3.0
    print(f"P4 РФ максимум и ≥3: ratio {ratios.get('RUS')} "
          f"→ {'ПОДТВЕРЖДЕНА' if rus_max else 'ОТКЛОНЕНА'}")

    # КНР: тот же θ на расширенный периметр
    r_cn, g_cn, p_cn = res['CHN']['r3'], res['CHN']['g3'], res['CHN']['p3']
    d_aug = {2024: AUG_CN[2024]}
    for y in range(2025, Y_F2 + 1):
        d_aug[y] = ((1.0 + r_cn) / (1.0 + g_cn)) * d_aug[y - 1] - p_cn
    diff_aug = d_aug[2031] - AUG_CN[2031]
    # узкий периметр тем же прогоном — для пропорции переноса
    d_nar = run_frozen('CHN', r_cn, g_cn, p_cn, y_start=2024)
    carry_nar = d_nar[2031] / debt['CHN'][2024]
    carry_aug_if_same = AUG_CN[2024] * carry_nar
    p3 = abs(diff_aug) >= 5.0
    print(f'КНР узкий ядро 2024 {debt["CHN"][2024]:.1f} → оператор 2031 '
          f'{d_nar[2031]:.1f} (IMF {res["CHN"]["imf31"]:.1f})')
    print(f'КНР augmented 2024 {AUG_CN[2024]:.1f} → тот же θ → 2031 '
          f'{d_aug[2031]:.1f} vs IMF-augmented {AUG_CN[2031]:.1f} '
          f'(DIFF {diff_aug:+.1f})')
    print(f'   перенос пропорцией узкого: {carry_aug_if_same:.1f} vs 153.7')
    print(f"P3 |DIFF_aug|≥5пп → {'ПОДТВЕРЖДЕНА (периметр — свой параметр)' if p3 else 'ОТКЛОНЕНА (переносится)'}")

    # ---------- (δ) WALK-FORWARD ----------
    print('\n=== (δ) WALK-FORWARD BACKTEST 2005–2025 (θ из окон t−5..t−1) ===')
    wf = {}
    for t in TERR:
        errs_op, errs_na = [], []
        for y in range(2005, Y1_ACT + 1):
            if y - 1 not in debt[t]:
                continue
            rr = [r_real[t][k] for k in range(y - 5, y) if k in r_real[t]]
            gg = [grw[t][k] / 100.0 for k in range(y - 5, y)
                  if k in grw[t] and grw[t][k] > -99.0]
            pp = [pb[t][k] for k in range(y - 5, y) if k in pb[t]]
            if not (rr and gg and pp):
                continue
            d_pred = ((1.0 + st.median(rr)) / (1.0 + st.median(gg))) \
                * debt[t][y - 1] - st.median(pp)
            if y in debt[t]:
                errs_op.append(debt[t][y] - d_pred)
                errs_na.append(debt[t][y] - debt[t][y - 1])
        rmse_op = (sum(e * e for e in errs_op) / len(errs_op)) ** 0.5
        rmse_na = (sum(e * e for e in errs_na) / len(errs_na)) ** 0.5
        wf[t] = dict(n=len(errs_op), rmse_op=rmse_op, rmse_na=rmse_na)
        print(f'{t}: n={len(errs_op)}  RMSE_оп {rmse_op:.2f} п.п.  '
              f'RMSE_наив {rmse_na:.2f} п.п.  '
              f'{"оператор лучше" if rmse_op < rmse_na else "наивный лучше"}')
    ok5 = wf['RUS']['rmse_op'] < wf['RUS']['rmse_na']
    print(f"P5 walk-forward РФ → {'ПОДТВЕРЖДЕНА' if ok5 else 'ОТКЛОНЕНА'}")

    # ---------- (γ) R7 INVARIANCE MATRIX ----------
    print('\n=== (γ) R7 INVARIANCE MATRIX ===')
    feat_names = ['d_2025', 'Δd/d 21-25', 'r_imp%', 'g%', 'pb%',
                  '(r−g)·d_2025', 'частное/ядро']
    F = {}
    for t in TERR:
        dd = [debt[t][y] for y in range(2021, 2026) if y in debt[t]]
        dmean = (dd[-1] / dd[0]) ** (1 / (len(dd) - 1)) - 1 if len(dd) > 1 else 0
        rgd = rg[t] * debt[t][2025]
        F[t] = [debt[t][2025], dmean * 100, res[t]['r3'] * 100,
                res[t]['g3'] * 100, res[t]['p3'], rgd,
                peri[t]['ratio'] if peri[t]['ratio'] else float('nan')]
    # нормировка min-max по каждой фиче (пропуски → среднее по остальным)
    import math
    Fv = {}
    for j, name in enumerate(feat_names):
        col = [F[t][j] for t in TERR if not math.isnan(F[t][j])]
        lo, hi = min(col), max(col)
        for t in TERR:
            v = F[t][j]
            Fv.setdefault(t, []).append(
                0.5 if math.isnan(v) or hi == lo else (v - lo) / (hi - lo))
    dist = {}
    for a in TERR:
        for b in TERR:
            if a < b:
                d2 = sum((x - y) ** 2 for x, y in zip(Fv[a], Fv[b])) ** 0.5
                dist[(a, b)] = d2
    for (a, b), d2 in sorted(dist.items(), key=lambda x: x[1]):
        print(f'  Δ({a},{b}) = {d2:.3f}')
    pairs = sorted(dist.items(), key=lambda x: x[1])[:2]
    got = {frozenset(p) for p, _ in pairs}
    p6 = frozenset(('USA', 'CHN')) in got and frozenset(('RUS', 'EUR')) in got
    print(f'   ближайшие пары: {[f"{a}-{b}" for (a,b),_ in pairs]}')
    print(f"P6 пары (USA,CHN)+(RUS,EUR) → {'ПОДТВЕРЖДЕНА' if p6 else 'ОТКЛОНЕНА'}")
    print('   признаки (нормированные 0..1):')
    for t in TERR:
        print(f'   {t}: ' + ' '.join(f'{v:.2f}' for v in Fv[t]))
    print('   карта Δ1–Δ12: измерено = Δ1 (d, ядро A), Δ2 (рост A), '
          'Δ4 (ie A), Δ5 (ie A), Δ8 (22–42 мес E, Task 18), Δ11 частично '
          '(частный кредит A); НЕ измерено: Δ3, Δ6 (структура держателей), '
          'Δ7, Δ9, Δ10 — задание коллеге с вебом.')

    # ---------- SFA по факту (топ-годы разрыва графа) ----------
    print('\n=== SFA (где граф ломается на факте), топ-3 |SFA| на территорию ===')
    sfa_all = {}
    for t in TERR:
        sfa_t = {}
        for y in range(2001, Y1_ACT + 1):
            if y - 1 not in debt[t] or y not in debt[t] \
                    or y not in pb[t] or y not in grw[t] or y not in r_real[t]:
                continue
            g = grw[t][y] / 100.0
            pred_d = ((r_real[t][y] - g) / (1.0 + g)) * debt[t][y - 1] \
                - pb[t][y]
            sfa_t[y] = (debt[t][y] - debt[t][y - 1]) - pred_d
        sfa_all[t] = sfa_t
        top = sorted(sfa_t.items(), key=lambda kv: abs(kv[1]),
                     reverse=True)[:3]
        print(f'  {t}: ' + '; '.join(f'{y}: {v:+.1f}' for y, v in top))

    # ---------- CSV ----------
    rows = []
    for t in TERR:
        for y in range(Y0, Y_F2 + 1):
            rows.append({
                'territory': t, 'year': y,
                'd_actual': round(debt[t][y], 2) if y in debt[t] and y <= Y1_ACT else '',
                'd_imf_path': round(debt[t][y], 2) if y in debt[t] and y >= 2025 else '',
                'd_op3y': round(res[t]['op3'][y], 2) if y in res[t]['op3'] else '',
                'd_op5y': round(res[t]['op5'][y], 2) if y in res[t]['op5'] else '',
                'd_linear31': round(res[t]['lin31'], 2) if y == Y_F2 else '',
                'r_real_pct': round(r_real[t][y] * 100, 2) if y in r_real[t] else '',
                'i_nom_pct': round(i_nom[t][y] * 100, 2) if y in i_nom[t] else '',
                'g_pct': round(grw[t][y], 2) if y in grw[t] else '',
                'pi_pct': round(cpi[t][y], 2) if y in cpi[t] else '',
                'pb': round(pb[t][y], 2) if y in pb[t] else '',
                'ie': round(ie[t][y], 2) if y in ie[t] else '',
                'priv_credit': round(priv[t][y], 2) if y in priv[t] else '',
                'sfa': round(sfa_all[t][y], 2) if y in sfa_all[t] else '',
            })
    with open(f'{OUT}/results.csv', 'w', newline='', encoding='utf-8') as f:
        wcsv = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        wcsv.writeheader()
        wcsv.writerows(rows)

    # ---------- JSON ----------
    summary = {
        'prereg': {'P1': ok1, 'P1b': ok1b, 'P2a': p2a, 'P2b': p2b,
                   'P2c': p2c, 'P3': p3, 'P4': rus_max, 'P5': ok5, 'P6': p6},
        'theta': {t: {k: round(v * (100 if k in ('r3', 'r5') else 1), 3)
                      for k, v in res[t].items()
                      if k in ('r3', 'g3', 'p3', 'r5', 'g5', 'p5')}
                  for t in TERR},
        'diff2031': {t: {'op3y': round(res[t]['diff_op'], 2),
                         'lin': round(res[t]['diff_lin'], 2),
                         'imf31': round(res[t]['imf31'], 2),
                         'op31': round(res[t]['op3'][2031], 2),
                         'lin31': round(res[t]['lin31'], 2)} for t in TERR},
        'repricing': {'rus_r_marg_nom': RUS_R_MARG,
                      'rus_r_imp_nom': round(r_imp_nom_rus, 2),
                      'rus_r_gap_pp': round(r_gap, 2),
                      'usa_ie_2021': ie_usa['2021'],
                      'usa_ie_last': ie_usa['last'],
                      'usa_ie_last_year': ie_usa['y_last']},
        'perimeter': {t: {'year': peri[t]['y_last'],
                          'core': round(peri[t]['core'], 2),
                          'priv': round(peri[t]['priv'], 2)
                          if peri[t]['priv'] else None,
                          'ratio': round(peri[t]['ratio'], 3)
                          if peri[t]['ratio'] else None} for t in TERR},
        'cn_augmented': {'anchors_C': AUG_CN, 'op31': round(d_aug[2031], 2),
                         'diff': round(diff_aug, 2),
                         'carry_if_same_theta': round(carry_aug_if_same, 2)},
        'walkforward': {t: {k: round(v, 3) if isinstance(v, float) else v
                            for k, v in wf[t].items()} for t in TERR},
        'r7_features_norm': {t: [round(v, 3) for v in Fv[t]] for t in TERR},
        'r7_distances': {f'{a}-{b}': round(d2, 3) for (a, b), d2 in dist.items()},
        'sfa_top': {t: {y: round(v, 2) for y, v in sorted(
            sfa_all[t].items(), key=lambda kv: abs(kv[1]), reverse=True)[:3]}
            for t in TERR},
    }
    with open(f'{OUT}/summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)

    import hashlib
    h = hashlib.sha256(open(f'{OUT}/summary.json', 'rb').read()).hexdigest()
    print(f'\nCSV: {OUT}/results.csv ({len(rows)} строк)')
    print(f'sha256(summary.json) = {h[:12]}…')
    print('ПРЕДИСТОРИЯ:', summary['prereg'])


if __name__ == '__main__':
    main()
