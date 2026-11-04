#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTA v0.5 — РЕЕСТР ВЕРИФИКАЦИИ (веб-поиск 2026-09-08, после вычисления
остатков) + PNG + финальный summary.json.
Протокол: каждому событию календаря (|resid| ≥ 5 п.п., топ-10/территорию)
нейтральный запрос «территория + год»; совпадение ±1 год (процессный
прецедент v0.2-P3). Вердикты: НАЙДЕНО (документированный оператор стока),
НЕ НАЙДЕНО (оператор не документирован), НЕИЗВЕСТНОЕ (события нет; кандидат
— счётная база). Реестр публикуется ЦЕЛИКОМ, включая промахи.
"""
import json
import numpy as np

OUT = '/home/z/my-project/scripts/rta_v0_5_out'
PNG = '/home/z/my-project/download/Red_Thread_Audit_v0_5_календарь_операторов.png'

# (год, resid, вердикт, оператор, класс кольца, источник)
REG = {
 'UKR': [
  (2014, 27.2, 'НАЙДЕНО', 'девальвация гривны (кризис, революция); курс-переоценка валютного долга', 'L3', 'IMF Survey 2008-15; переоценка'),
  (2015, 26.8, 'НАЙДЕНО', 'IMF EFF $17.5 млрд (март-2015) + реструктуризация/обмен евробондов (авг-2015) + девальвация; переоценка доминирует над haircut', 'L3(+L9)', 'IMF EFF 11.03.2015; Weil Gotshal: обмен авг-2015'),
  (2016, 9.6, 'НАЙДЕНО', 'национализация ПриватБанка 18.12.2016: рекап-облигации Минфина Hr 116.8–148 млрд ($4.4–5.6 млрд ≈ 4–5% ВВП) — социализация', 'L6', 'Reuters 19.12.2016; nationalization wiki'),
  (2021, -8.2, 'НЕ НАЙДЕНО', 'документированного оператора стока нет; кандидат: переоценка/знаменатель; первый купон GDP-warrant $40.75 млн (май-2021) — мал', 'неизвестное', 'поиск: только купоны warrant'),
  (2009, 7.8, 'НАЙДЕНО', 'IMF SBA $16.4 млрд (11.2008) + «perfect storm»: разворот потоков, девальвация', 'L3', 'IMF Press 05.11.2008; Bakker/Gulde'),
  (2008, 7.5, 'НАЙДЕНО', 'тот же комплекс 2008: SBA, обвал стали, начало девальвации', 'L3', 'IMF 2008'),
  (2019, -5.5, 'НАЙДЕНО', 'укрепление гривны (2019) → переоценка валютного долга вниз; «public debt fell by more…»', 'L3', 'World Bank/DFC 2019 chapter'),
  (2005, -5.5, 'НЕ НАЙДЕНО', 'укрепление гривны 2005 (~5%) даёт ≤2.5 п.п.; документированного оператора стока нет', 'неизвестное', 'поиск: без события стока'),
 ],
 'TUR': [
  (2001, 34.2, 'НАЙДЕНО', 'кризис 02.2001: принятие «duty losses» банков Казначейством, спец-облигации TL 22.9 млрд, рекапитализация, float лиры — социализация + переоценка', 'L6+L3', 'IMF CR 01/89; BDDK papers'),
  (2002, 16.1, 'НАЙДЕНО', 'продолжение: облигации реструктуризации банков (Istanbul Approach)', 'L6', 'BIS/IMF papers 2002'),
  (2003, 5.5, 'НАЙДЕНО', 'завершение выкупа duty-loss receivables спец-облигациями', 'L6', 'ResearchGate: From Crisis to Fin. Stability'),
  (2020, 6.7, 'НАЙДЕНО', 'падение лиры 2020 (~−34% за год)', 'L3', 'кризис 2018–… wiki'),
  (2021, 7.9, 'НАЙДЕНО', 'лира потеряла 44% за 2021', 'L3', 'Orhangazi 2024; wiki'),
  (2022, 7.8, 'НАЙДЕНО', 'инфляция 78.6% (2022), продолжение падения лиры', 'L3', 'wiki кризис 2018–…'),
  (2023, 5.8, 'НАЙДЕНО', 'пост-выборный обвал лиры (май–июнь 2023), инфляция ~65%', 'L3', 'факт 2023'),
 ],
 'BRA': [
  (2001, 7.1, 'НАЙДЕНО', 'падение реала 2000–2002 (заражение Аргентиной, 9/11) → переоценка долларового долга', 'L3', 'Giambiagi 2004'),
  (2002, 13.0, 'НАЙДЕНО', 'обвал реала (кризис выборов-2002) → «debt denominated in USD increased»; IMF $30 млрд (авг-2002)', 'L3', 'Giambiagi 2004'),
 ],
 'PAK': [
  (2001, 5.9, 'НАЙДЕНО', 'Парижский клуб 13.12.2001: реструктуризация стока $12.5 млрд (reprofiling — номинал сохраняется); знак + от переоценки/доначислений', 'L9(событие)/L3(знак)', 'Paris Club PR 13.12.2001; Kundi 2016'),
  (2008, 6.3, 'НАЙДЕНО', 'BoP-кризис 2008 (нефть), rupee под давлением → IMF SBA $7.6 млрд (17.11.2008)', 'L3', 'IMF 17.11.2008; ISAS-NUS'),
  (2009, 9.9, 'НАЙДЕНО', 'продолжение кризиса 2008–09: FDI $5.41→3.72 млрд, девальвация', 'L3', 'IMF SBA; Feb-2023 обзор'),
  (2018, 5.1, 'НАЙДЕНО', 'цикл девальваций рупии (дек-2017 → 2019), BoP-проблемы 2018', 'L3', 'ISAS-NUS 2020'),
  (2019, 11.1, 'НАЙДЕНО', 'IMF EFF $6 млрд (03.07.2019); внешний долг → $103.4 млрд; девальвация рупии', 'L3', 'IMF 03.07.2019'),
  (2022, 7.5, 'НАЙДЕНО', 'наводнения + рекордно низкая рупия (03.2023), задержка транша', 'L3', 'Reuters 02.03.2023'),
  (2023, 12.3, 'НАЙДЕНО', 'IMP $3 млрд (30.06.2023), рупия до 285, дефолт на грани', 'L3', 'AP/Reuters 30.06.2023'),
 ],
 'JPN': [
  (2004, 6.2, 'НЕИЗВЕСТНОЕ', 'документированного оператора стока 2004 нет (Resona-инъекция ¥2 трлн — май-2003, мал); кандидат: разрыв счётной базы WEO/GFS', 'неизвестное (база)', 'поиск 2026-09-08: без события'),
  (2022, 9.2, 'НЕИЗВЕСТНОЕ', 'оператора стока нет (долг — в иенах, переоценки нет); кандидат: допбюджеты вне pb-базы (несогласованность серий)', 'неизвестное (база)', 'поиск 2026-09-08: без события'),
 ],
}


def main():
    with open(f'{OUT}/summary.json', encoding='utf-8') as f:
        S = json.load(f)

    # ---- реестр + вердикты PB2/PB4 ----
    total, hits, unknown, named = 0, 0, 0, 0
    for t, evs in REG.items():
        for y, v, verd, op, cls, src in evs:
            total += 1
            if verd == 'НАЙДЕНО':
                hits += 1
                named += 1
            else:
                # и НЕ НАЙДЕНО, и НЕИЗВЕСТНОЕ — вне таксономии кольца
                unknown += 1
    hit_rate = hits / total
    unknown_rate = unknown / total
    pb2 = hit_rate >= 0.70
    pb4 = unknown_rate <= 0.30
    S['verification'] = {t: [dict(year=y, resid_pp=v, verdict=verd,
                                  operator=op, ring_class=cls, source=src)
                             for y, v, verd, op, cls, src in evs]
                         for t, evs in REG.items()}
    S['verification_stats'] = {
        'total_events': total, 'named': hits,
        'unknown': unknown, 'hit_rate': round(hit_rate, 3),
        'threshold': 0.70}
    S['prereg']['PB2'] = pb2
    S['prereg']['PB4'] = pb4
    with open(f'{OUT}/summary.json', 'w', encoding='utf-8') as f:
        json.dump(S, f, ensure_ascii=False, indent=1)

    print('=' * 70)
    print('PB2: НАЙДЕНО', hits, '/', total, '=', f'{hit_rate*100:.1f}%',
          '→', 'ПОДТВЕРЖДЕНА' if pb2 else 'ОТКЛОНЕНА', '(порог ≥70%)')
    print('PB4: НЕИЗВЕСТНОЕ', unknown, '/', total, '=',
          f'{unknown_rate*100:.1f}%', '→',
          'ПОДТВЕРЖДЕНА' if pb4 else 'ОТКЛОНЕНА', '(порог ≤30%)')
    classes = {}
    for t, evs in REG.items():
        for y, v, verd, op, cls, src in evs:
            if verd == 'НАЙДЕНО':
                classes[cls] = classes.get(cls, 0) + 1
    print('таксономия названных:', classes,
          '— реальность не выходит за звенья L3/L6/L9')
    for t, evs in REG.items():
        print(f'--- {t} ---')
        for y, v, verd, op, cls, src in evs:
            print(f'  {y}: {v:+6.1f} [{verd}] {cls:<10} {op[:70]}')

    # ---- PNG ----
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.0),
                             constrained_layout=True)
    sfa = {t: {int(y): vv for y, vv in S['sfa_full'][t].items()}
           for t in S['sfa_full']}
    # (а) ряды остатков
    ax = axes[0, 0]
    cols = {'UKR': '#8B0000', 'TUR': '#B8860B', 'BRA': '#2E8B57',
            'PAK': '#4682B4', 'JPN': '#555555'}
    for t in ['UKR', 'TUR', 'BRA', 'PAK', 'JPN']:
        ys = sorted(sfa[t])
        vs = [sfa[t][y] for y in ys]
        ax.plot(ys, vs, '-', color=cols[t], lw=1.1, alpha=0.75, label=t)
        big = [(y, v) for y, v in zip(ys, vs) if abs(v) >= 5.0]
        ax.plot([y for y, _ in big], [v for _, v in big], 'o', ms=4,
                color=cols[t])
    ax.axhline(0, color='#888888', lw=0.8)
    ax.axhspan(-5, 5, color='#2E8B57', alpha=0.06)
    ax.set_title('SFA-остатки (независимые кейсы, граф v0.1 не менялся)\n'
                 'точки — события ≥5 п.п.; залита полоса «мирных» ±2 п.п.',
                 fontsize=10.5)
    ax.set_xlabel('год', fontsize=9.5)
    ax.set_ylabel('остаток, п.п. ВВП', fontsize=9.5)
    ax.legend(fontsize=8, loc='upper right')
    ax.grid(alpha=0.3)
    # (б) топ-события и вердикты
    ax = axes[0, 1]
    evs = []
    for t, evlist in REG.items():
        for y, v, verd, op, cls, src in evlist:
            evs.append((f'{t} {y}', v, verd))
    evs.sort(key=lambda e: -abs(e[1]))
    lab = [e[0] for e in evs][::-1]
    val = [e[1] for e in evs][::-1]
    vc = {'НАЙДЕНО': '#2E8B57', 'НЕ НАЙДЕНО': '#CD3333',
          'НЕИЗВЕСТНОЕ': '#8B4513'}
    colors = [vc[e[2]] for e in evs][::-1]
    ax.barh(range(len(val)), val, color=colors, alpha=0.85)
    ax.set_yticks(range(len(val)))
    ax.set_yticklabels(lab, fontsize=6.8)
    ax.axvline(0, color='#888888', lw=0.8)
    handles = [plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.85)
               for c in vc.values()]
    ax.legend(handles, [f'{k} ({sum(1 for e in evs if e[2]==k)})'
                        for k in vc], fontsize=7.5, loc='lower right')
    ax.set_title(f'Календарь операторов ex-ante и верификация:\n'
                 f'НАЙДЕНО {hits}/{total} = {hit_rate*100:.0f}% '
                 f'(порог ≥70% — ПОДТВЕРЖДЕНА)', fontsize=10.5)
    ax.set_xlabel('SFA-остаток, п.п. ВВП', fontsize=9.5)
    ax.grid(alpha=0.3, axis='x')
    # (в) мирные годы
    ax = axes[1, 0]
    ps = S['peaceful_share']
    ts = sorted(ps, key=lambda t: ps[t])
    vals = [ps[t] * 100 for t in ts]
    bars = ax.bar(ts, vals, color=[cols[t] for t in ts], alpha=0.85)
    ax.axhline(S['peaceful_share_agg'] * 100, color='#8B0000', ls='--',
               lw=1.5, label=f"агрегат {S['peaceful_share_agg']*100:.1f}%")
    ax.axhline(60, color='#555555', ls=':', lw=1.5,
               label='порог 60% (PB1)')
    for b, t in zip(bars, ts):
        ax.annotate(f'{ps[t]*100:.0f}%', (b.get_x() + b.get_width() / 2,
                                          b.get_height() + 1),
                    ha='center', fontsize=9)
    ax.set_ylim(0, 75)
    ax.set_title('PB1 подтверждена: мирные годы несводимы к r−g−pb\n'
                 f"вне выборки тоже ({S['peaceful_share_agg']*100:.1f}% < 60%;"
                 ' v0.2 давал 37%)', fontsize=10.5)
    ax.set_ylabel('доля мирных лет, %', fontsize=9.5)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis='y')
    # (г) контроль JPN
    ax = axes[1, 1]
    ys = sorted(y for y in sfa['JPN'] if y != 2020)
    vs = [abs(sfa['JPN'][y]) for y in ys]
    ax.bar(ys, vs, color='#555555', alpha=0.8)
    ax.axhline(5, color='#CD3333', ls='--', lw=1.5,
               label='порог 5 п.п. (PB3)')
    for y, v in zip(ys, vs):
        if v >= 5:
            ax.annotate(f'{y}: {v:.1f}', (y, v), textcoords='offset points',
                        xytext=(0, 4), ha='center', fontsize=8.5,
                        color='#CD3333')
    ax.set_title('PB3: контроль специфичности JPN (без реструктуризаций)\n'
                 'ОТКЛОНЕНА: 2004 +6.2 — не именуется экономикой;\n'
                 'кандидат — счётная база (честная публикация)', fontsize=10.5)
    ax.set_xlabel('год', fontsize=9.5)
    ax.set_ylabel('|остаток|, п.п. ВВП', fontsize=9.5)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis='y')
    fig.suptitle('RED THREAD AUDIT v0.5 — ex-ante операторы на независимых '
                 'кейсах (UKR/TUR/BRA/PAK + JPN-контроль), EGY исключён: '
                 'pb/ie отсутствуют в FM', fontsize=11.5)
    fig.savefig(PNG, dpi=150)
    print(f'\nPNG: {PNG}')
    import hashlib
    h = hashlib.sha256(
        open(f'{OUT}/summary.json', 'rb').read()).hexdigest()
    print(f'sha256(summary.json) = {h[:12]}…')


if __name__ == '__main__':
    main()
