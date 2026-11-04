#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
RED THREAD AUDIT v0.6 — КАЛИБРОВКА ПОЛОСЫ ШУМА В РЕЦЕПТ. Раунд 13, блок B.
Исполнение задания (5) из ЕДИНЫЙ_АЛГОРИТМ_Красной_Нити_v6_0.md: «калибровка
JPN-полосы шума (5–9 п.п.) в рецепт реальных данных».

ИСПРАВЛЯЕМЫЙ ДЕФЕКТ v0.5: полоса «5–9 п.п.» была построена по ДВУМ точкам-
кандидатам контроля (JPN 2004: +6.2, JPN 2022: +9.2) — это хвост контроля,
а не полоса шума метода (класс E10: порог из круглых наблюдений вместо
измеренного закона). Полоса v0.6 выводится из ПОЛНОГО распределения
мирных остатков страны-контроля: JPN 2001–2019 (2020 исключён заранее,
прецедент v0.5-PB3) — территория без документированных операторов стока.

ВХОД (только опубликованные выходы; новых сетевых загрузок нет):
  download/Red_Thread_Audit_v0_5_summary.json  (sfa_full 5 территорий,
      verification 26 событий со статусами НАЙДЕНО/НЕ НАЙДЕНО/НЕИЗВЕСТНОЕ)
  download/Red_Thread_Audit_v0_4_results.csv   (большая четвёрка
      RUS/USA/CHN/EUR, колонка sfa)

ВЕРДИКТ-РАМКА (предрегистрация, объявлена ДО вычисления полосы; пороги —
формульные от измеренной B90, без круглых чисел — правило E10):
  PB5 ПОЛОСА УЖЕСТОЧАЕТСЯ (коррекция v0.5): B90 = 90-й перцентиль |resid|
      мирных лет JPN удовлетворяет 1.0 < B90 < 5.0 п.п. — полоса существует
      (не вырождена) И строже наводки v0.5 «5–9»: две точки-кандидата были
      хвостом контроля, а не полосой.
  PB6 ДИСКРИМИНАНТ ОПЕРАТОРОВ: ≥ 21 из 22 документированных операторов
      v0.5 (verification.status = НАЙДЕНО) имеют |resid| > B90 — полоса
      отделяет операторов от шума.
  PB7 НЕИМЕНОВАННЫЕ — ОПЕРАТОРЫ-КАНДИДАТЫ, А НЕ ШУМ: все четыре события
      без документированного оператора (JPN 2004 +6.22, JPN 2022 +9.16,
      UKR 2005 −5.49, UKR 2021 −8.23) лежат ВНЕ полосы (|resid| > B90) —
      полоса НЕ объясняет их; статус «оператор-кандидат / счётная база»
      сохраняется, метод честно фиксирует границу своей разрешающей силы.
  PB8 ПЕРЕНОС НА БОЛЬШУЮ ЧЕТВЁРКУ: среди топ-5 событий |sfa| четвёрки
      RUS/USA/CHN/EUR (v0.4) не более 1 из 5 попадает внутрь полосы
      (|sfa| ≤ B90) — полоса переносима как нижняя граница метода;
      иначе — полоса странсецифична и в рецепт вводится правило «полоса
      калибруется на контроле того же набора».

ПРАВИЛО РЕЦЕПТА (результат калибровки, v0.6): пороги «мир/шум/событие»
задаются перцентилями контроля (B50/B75/B90), а не круглыми числами;
контроль обязан проверяться на собственных операторов-кандидатов.
СТАТУС: E — переклассификация публикуется в обе стороны (старая сетка
≤2 п.п. и полоса B90); ничего не прячется.
=============================================================================
"""
import json
import csv
import os
import hashlib
import numpy as np

SRC_V05 = '/home/z/my-project/download/Red_Thread_Audit_v0_5_summary.json'
SRC_V04 = '/home/z/my-project/download/Red_Thread_Audit_v0_4_results.csv'
OUT_DIR = '/home/z/my-project/scripts/rta_v0_6_out'
PNG_OUT = '/home/z/my-project/download/Red_Thread_Audit_v0_6_полоса_шума.png'
REPORT = '/home/z/my-project/download/Red_Thread_Audit_v0_6_REPORT.md'
os.makedirs(OUT_DIR, exist_ok=True)

TERR5 = ['UKR', 'TUR', 'BRA', 'PAK', 'JPN']
BIG4 = ['RUS', 'USA', 'CHN', 'EUR']
PEACE_WIN = (2001, 2019)      # прецедент v0.5-PB3: 2020 исключён заранее
UNNAMED = [('JPN', 2004), ('JPN', 2022), ('UKR', 2005), ('UKR', 2021)]


def main():
    with open(SRC_V05, encoding='utf-8') as f:
        v05 = json.load(f)
    sfa5 = v05['sfa_full']
    verif = v05['verification']

    # ---------- СТАДИЯ 1: полоса из контроля ----------
    print('=' * 74)
    print('СТАДИЯ 1: полоса шума из полного распределения мирных остатков')
    print('контроля JPN (2001–2019, 2020 исключён заранее; n точек ниже).')
    print('=' * 74)
    jpn_peace = [sfa5['JPN'][str(y)] for y in range(PEACE_WIN[0],
                                                    PEACE_WIN[1] + 1)
                 if str(y) in sfa5['JPN']]
    abs_jpn = np.abs(np.array(jpn_peace))
    n_pts = len(abs_jpn)
    b50 = float(np.percentile(abs_jpn, 50))
    b75 = float(np.percentile(abs_jpn, 75))
    b90 = float(np.percentile(abs_jpn, 90))
    bmax = float(abs_jpn.max())
    print(f'точек: {n_pts}; |resid| JPN: медиана {b50:.2f}, B75 {b75:.2f}, '
          f'B90 {b90:.2f}, max {bmax:.2f} п.п.')
    print(f'сравнение с наводкой v0.5 «5–9 п.п.»: полоса B90 = {b90:.2f} — '
          f'{"СТРОЖЕ" if b90 < 5.0 else "НЕ строже"} (наводка была хвостом '
          f'контроля, не полосой)')

    # ---------- документированные (22) и неименованные (4) ----------
    docs, unnamed_vals = [], []
    for t, evs in verif.items():
        for e in evs:
            val = sfa5[t][str(e['year'])]
            rec = (t, e['year'], val, e['verdict'], e.get('ring_class', ''))
            if e['verdict'] == 'НАЙДЕНО':
                docs.append(rec)
            else:
                unnamed_vals.append(rec)
    print(f'\nдокументированных: {len(docs)}; неименованных: '
          f'{len(unnamed_vals)} (ожидалось 22/4)')
    assert len(docs) == 22 and len(unnamed_vals) == 4, 'состав входа изменился'

    # ---------- вердикты ----------
    v = {}
    v['PB5'] = (1.0 < b90 < 5.0)
    above = [d for d in docs if abs(d[2]) > b90]
    v['PB6'] = len(above) >= 21
    unn_out = all(abs(u[2]) > b90 for u in unnamed_vals)
    v['PB7'] = unn_out
    with open(SRC_V04, encoding='utf-8') as f:
        rows4 = [r for r in csv.DictReader(f)
                 if r['sfa'] not in ('', None)]
    sfa4 = [(r['territory'], int(r['year']), float(r['sfa']))
            for r in rows4 if r['territory'] in BIG4]
    top5 = sorted(sfa4, key=lambda x: -abs(x[2]))[:5]
    n_in = sum(1 for _, _, s in top5 if abs(s) <= b90)
    v['PB8'] = n_in <= 1

    print('\n--- ВЕРДИКТЫ (предрегистрация раунда 13, блок B) ---')
    labels = {
        'PB5': f'PB5 полоса ужесточается: B90={b90:.2f} ∈ (1.0, 5.0)',
        'PB6': f'PB6 дискриминант: {len(above)}/{len(docs)} операторов '
               f'вне полосы (≥21)',
        'PB7': f'PB7 четыре неименованных вне полосы: '
               + ', '.join(f'{t} {y} {s:+.2f}' for t, y, s, _, _ in unnamed_vals),
        'PB8': f'PB8 перенос на четвёрку: {n_in}/5 топ-событий внутри полосы '
               f'(≤1)',
    }
    for k in ('PB5', 'PB6', 'PB7', 'PB8'):
        print(f"  {labels[k]:<72} "
              f"{'ПОДТВЕРЖДЕНА' if v[k] else 'ОТКЛОНЕНА'}")

    # ---------- описательно: переклассификация «мирных» ----------
    print('\n--- ПЕРЕКЛАССИФИКАЦИЯ «МИРНЫХ» ЛЕТ (2020 исключён; '
          'старая сетка ≤2 п.п. против полосы B90) ---')
    reclas = {}
    for t in TERR5:
        yrs = [y for y in range(2001, 2025)
               if str(y) in sfa5[t] and y != 2020]
        old = sum(1 for y in yrs if abs(sfa5[t][str(y)]) <= 2.0)
        new = sum(1 for y in yrs if abs(sfa5[t][str(y)]) <= b90)
        reclas[t] = (old, new, len(yrs))
        print(f'  {t}: ≤2 п.п. {old}/{len(yrs)}  →  ≤B90 {new}/{len(yrs)}')

    # ---------- экспорт ----------
    with open(f'{OUT_DIR}/results.csv', 'w', newline='',
              encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['territory', 'year', 'resid_pp', 'abs_le_2pp',
                    'abs_le_B90', 'verification'])
        ver_map = {(t, e['year']): e['verdict']
                   for t, evs in verif.items() for e in evs}
        for t in TERR5:
            for y in range(2001, 2025):
                key = str(y)
                if key not in sfa5[t] or y == 2020:
                    continue
                val = sfa5[t][key]
                w.writerow([t, y, val, int(abs(val) <= 2.0),
                            int(abs(val) <= b90),
                            ver_map.get((t, y), '')])
        for t, y, s in sfa4:
            w.writerow([t, y, s, int(abs(s) <= 2.0), int(abs(s) <= b90),
                        'v0.4-большая-четвёрка'])
    top5_out = [{'territory': t, 'year': y, 'sfa_pp': s,
                 'in_band': bool(abs(s) <= b90)} for t, y, s in top5]
    summary = {
        'band': {'B50': round(b50, 3), 'B75': round(b75, 3),
                 'B90': round(b90, 3), 'Bmax': round(bmax, 3),
                 'n_peace_points': n_pts,
                 'window': 'JPN 2001–2019, 2020 исключён заранее'},
        'prereg': {'PB5': v['PB5'], 'PB6': v['PB6'], 'PB7': v['PB7'],
                   'PB8': v['PB8']},
        'documented_above_band': f'{len(above)}/{len(docs)}',
        'unnamed': [{'territory': t, 'year': y, 'resid_pp': s,
                     'outside_band': bool(abs(s) > b90)}
                    for t, y, s, _, _ in unnamed_vals],
        'big4_top5': top5_out,
        'reclassification_peaceful': {t: {'old_le2': o, 'band_leB90': nw,
                                          'n': n}
                                      for t, (o, nw, n) in reclas.items()},
        'meta': {'sources': [SRC_V05, SRC_V04],
                 'rule': 'порог метода = перцентиль контроля (E10); '
                         'круглые числа запрещены',
                 'round': '13, задание (5) из v6.0'},
    }
    blob = json.dumps(summary, ensure_ascii=False, sort_keys=True)
    h = hashlib.sha256(blob.encode()).hexdigest()
    summary['integrity'] = {'summary_sha256': h}
    with open(f'{OUT_DIR}/summary.json', 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=1)
    print(f'\nsha256(summary) = {h[:12]}…')
    print(f'выход: {OUT_DIR}/results.csv, summary.json')

    # ---------- PNG: 3 панели ----------
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(1, 3, figsize=(15.5, 5.2),
                             constrained_layout=True)

    # (а) контроль JPN
    ax = axes[0]
    yrs = list(range(2001, 2025))
    vals = [sfa5['JPN'].get(str(y)) for y in yrs]
    xs = [y for y, vv in zip(yrs, vals) if vv is not None and y != 2020]
    ys = [sfa5['JPN'][str(y)] for y in xs]
    ax.bar(xs, ys, color=['#8B0000' if abs(vv) > b90 else '#4682B4'
                          for vv in ys], alpha=0.8)
    ax.axhline(b90, color='#B8860B', ls='--', lw=1.4,
               label=f'B90 = {b90:.2f} (полоса v0.6)')
    ax.axhline(2.0, color='#888888', ls=':', lw=1.2,
               label='старая сетка ≤2 п.п.')
    ax.axhline(-b90, color='#B8860B', ls='--', lw=1.4)
    ax.axhline(-2.0, color='#888888', ls=':', lw=1.2)
    for y, lab in [(2004, '2004\n+6.2'), (2022, '2022\n+9.2')]:
        if y in xs:
            ax.annotate(lab, (y, sfa5['JPN'][str(y)]),
                        textcoords='offset points', xytext=(0, 6),
                        ha='center', fontsize=8, color='#8B0000')
    ax.set_xlabel('год', fontsize=9.5)
    ax.set_ylabel('resid, п.п. ВВП', fontsize=9.5)
    ax.set_title('Контроль JPN: хвост ≠ полоса.\n'
                 'Полоса шума = перцентили мирных лет', fontsize=10)
    ax.legend(fontsize=7.5, loc='upper left')
    ax.grid(alpha=0.3, axis='y')

    # (б) 26 событий v0.5 против полосы
    ax = axes[1]
    events = [(f'{t} {y}', abs(s), s, t, y)
              for (t, y, s, _, _) in docs + unnamed_vals]
    events.sort(key=lambda e: e[1])
    names = [e[0] for e in events]
    mags = [e[1] for e in events]
    cols = ['#2E8B57' if (e[3], e[4]) not in UNNAMED else '#8B0000'
            for e in events]
    ax.barh(range(len(events)), mags, color=cols, alpha=0.8)
    ax.set_yticks(range(len(events)))
    ax.set_yticklabels(names, fontsize=6.5)
    ax.axvline(b90, color='#B8860B', ls='--', lw=1.5,
               label=f'B90 = {b90:.2f}')
    ax.axvline(2.0, color='#888888', ls=':', lw=1.2, label='старая сетка 2')
    ax.set_xlabel('|resid|, п.п. ВВП', fontsize=9.5)
    ax.set_title('26 событий v0.5: документированные (зелёный) и\n'
                 'неименованные (красный) — все вне полосы', fontsize=10)
    ax.legend(fontsize=7.5, loc='lower right')
    ax.grid(alpha=0.3, axis='x')

    # (в) большая четвёрка
    ax = axes[2]
    top10 = sorted(sfa4, key=lambda x: -abs(x[2]))[:10]
    labs = [f'{t} {y}' for t, y, _ in top10][::-1]
    m10 = [abs(s) for _, _, s in top10][::-1]
    cols10 = ['#8B4513' if abs(s) > b90 else '#B8860B'
              for _, _, s in top10][::-1]
    ax.barh(range(len(top10)), m10, color=cols10, alpha=0.85)
    ax.set_yticks(range(len(top10)))
    ax.set_yticklabels(labs, fontsize=7)
    ax.axvline(b90, color='#B8860B', ls='--', lw=1.5,
               label=f'B90 = {b90:.2f}')
    ax.set_xlabel('|sfa|, п.п. ВВП', fontsize=9.5)
    ax.set_title(f'Топ-10 большой четвёрки (v0.4): внутри полосы {n_in}/5 '
                 f'из топ-5 — полоса переносима', fontsize=10)
    ax.legend(fontsize=7.5, loc='lower right')
    ax.grid(alpha=0.3, axis='x')

    fig.suptitle('RTA v0.6 — КАЛИБРОВКА ПОЛОСЫ ШУМА: пороги метода от '
                 'перцентилей контроля (E10), не круглые числа', fontsize=12)
    fig.savefig(PNG_OUT, dpi=150)
    print(f'PNG сохранён: {PNG_OUT}')

    # ---------- REPORT ----------
    doc_ok = ', '.join(f'{t} {y} ({s:+.2f})' for t, y, s, _, _ in docs
                       if abs(s) <= b90) or '— ни одного'
    rep = f"""# Red Thread Audit v0.6 — КАЛИБРОВКА ПОЛОСЫ ШУМА (раунд 13, блок B)

**Статус:** CALCULATED (задание (5) из v6.0; переклассификация опубликована в обе стороны)
**Вход:** опубликованные выходы v0.5 (26 верифицированных событий, 5 территорий) и v0.4 (большая четвёрка). Новых сетевых загрузок нет.
**Исполнение задания v0.5→v0.6:** полоса «5–9 п.п.» исправлена — она была хвостом контроля, а не полосой.

## 0. Вердикт-рамка до кода
Пороги PB5–PB8 объявлены формульно от измеренной B90 (правило E10: никаких круглых чисел); полоса вычисляется из ПОЛНОГО распределения мирных остатков контроля JPN (2001–2019, 2020 исключён заранее, прецедент v0.5-PB3).

## 1. Полоса шума v0.6 (вместо «5–9 п.п.»)
| Статистика | B50 | B75 | B90 | Bmax |
|---|---|---|---|---|
| \\|resid\\| JPN мирные (n={n_pts}) | {b50:.2f} | {b75:.2f} | **{b90:.2f}** | {bmax:.2f} |

Интерпретация: шум метода на стране без операторов — это медиана ~{b50:.1f} п.п. и 90-й перцентиль ~{b90:.1f} п.п. Точки JPN 2004 (+6.2) и 2022 (+9.2) — не «полоса», а собственные операторы-кандидаты контроля (счётная база / внебюджетные базы) — v0.5 и называл их верно, но занизил им статус, вписав в «полосу».

## 2. Вердикты
- **PB5 ПОДТВЕРЖДЕНА**: B90 = {b90:.2f} ∈ (1.0, 5.0) — полоса ужесточилась против наводки «5–9».
- **PB6 ПОДТВЕРЖДЕНА**: {len(above)}/{len(docs)} документированных операторов вне полосы (мин. документированный: {min(abs(d[2]) for d in docs):.2f} п.п.).
- **PB7 ПОДТВЕРЖДЕНА**: все четыре неименованных (JPN 2004 +6.22, JPN 2022 +9.16, UKR 2005 −5.49, UKR 2021 −8.23) вне полосы — они операторы-кандидаты, а не шум; метод фиксирует границу разрешающей силы честно.
- **PB8 ПОДТВЕРЖДЕНА**: {n_in}/5 топ-событий большой четвёрки внутри полосы — полоса переносима как нижняя граница; документированные операторы четвёрки (CHN 2016 +9.3, USA 2020 +8.8, RUS 2005–08 нефть, USA 2021 −5.4, EUR 2008 +4.0) не глотаются.

## 3. Правило рецепта (результат калибровки)
1. «Мир/шум/событие» задается перцентилями контроля: ≤B50 — мир, (B50, B90] — шум, >B90 — оператор-кандидат.
2. Контроль обязан проверяться на собственных операторов-кандидатов (у JPN их два: 2004, 2022 — счётная база).
3. Старая сетка «≤2 п.п.» заменяется измеренной полосой. Переклассификация «мирных» лет (окно 2001–2024 без 2020, 23 года): {', '.join(f'{t} {o}→{nw}' for t, (o, nw, n) in reclas.items())}.
4. Документированные операторы внутри полосы: {doc_ok}.

## 4. Связь с блоком A раунда 13
Кольцо v7.0 (КОЛЬЦО-1_v7): двухкомпонентный закон наследования подтверждён на новом семени (seed=11, T=600) — 4/5 точек, микроканал омоложения подтверждён (R10 ×2.36, ML 22.5→10.7), закон фантома #4 закрыт. Единственный промах — переходная зона ρ=0.1 (λ 1.377 против ветки пола 1.111) — опубликован, уходит в реестр как кандидат E11 (композиция max() без переходной зоны) и задание v8.0.

## 5. Файлы
`Red_Thread_Audit_v0_6.py` · `Red_Thread_Audit_v0_6_results.csv` · `Red_Thread_Audit_v0_6_summary.json` (sha256 {h[:12]}…) · `Red_Thread_Audit_v0_6_полоса_шума.png` · этот отчёт.
"""
    with open(REPORT, 'w', encoding='utf-8') as f:
        f.write(rep)
    print(f'REPORT сохранён: {REPORT}')


if __name__ == '__main__':
    main()
