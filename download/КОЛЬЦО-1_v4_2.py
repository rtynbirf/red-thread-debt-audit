#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
КОЛЬЦО-1_v4_2.py — СЫТОСТЬ И ДАРЕНИЕ ПРИ ЖИЗНИ.
Ответ на упрёк (раунд 7, заказчик через второго ЛЛМ): «СТАРОМУ НИЧЕГО НЕ НАДО,
У НЕГО УЖЕ ЕСТЬ!!! ОН ОТДАЁТ ЧАСТЬ НАЖИТОГО ДЕТЯМ ВНУКАМ ПРАВНУКАМ!»
База: механика v4.1 вербатим (u·shock в доходе, ρ=A/B/C, τ-оборот, аудит).
=============================================================================

ЧТО УПРЁК ВСКРЫЛ В v4 (проверено по коду до прогона):
  (1) потребность ПОСТОЯННА: cons = max(subsist=70, 0.6·y_eff) для ЛЮБОГО
      возраста — модель заставляет старых заёмать (y_eff после 55 обваливается
      до 0.3·базы, а «надо» остаётся 70). Q1b v4 это и поймало: старшие 55+
      = 29.9% объёма новых займов при 21.7% населения (жизнь ×4 — 91.8%!).
      «Старому ничего не надо» в модели НЕВЫГОВАРИВАЕМО.
  (2) вся межпоколенческая трансмиссия отложена до смерти (ρ=A: наследник
      получает ДОЛГ + сбережения + g0=15). Дарение при жизни отсутствует.
  (3) слотовая топология: наследник рождается В ТИК СМЕРТИ предшественника —
      у живого старика коэффициент живых потомков = 0. «Детям внукам
      правнукам» отдать некому: дети ещё не родились. Клапан «смерть»
      в v4 — не открытие, а следствие предположенной таблицы ρ.

ПЕРЕКЛЮЧАТЕЛИ v4.2 (в базовой конфигурации оба выключены — якорь):
  satiate  («сытость»): после sat_age=65 потребность линейно спадает за 10
           лет до sat_frac=0.5·subsist — «старому меньше надо, у него есть».
  gift     («дарение»): каждый тик носители age ≥ gift_age=60 с сбережениями
           s > s_keep=140 отдают g_frac=0.25 излишка (s − s_keep); пул
           распределяется ПРОПОРЦИОНАЛЬНО ДЕФИЦИТУ среди age < 30, гася его
           ДО того, как он станет займом (семейный трансфер вместо кредита);
           нераспределённый излишек аллокации — в сбережения получателя.

ПРЕДИСТОРИЯ (предрегистрация, объявлена ДО прогона):
  P1 сытость: λ < базы (главный клапан Q1b — старость — перекрывается);
     доля объёма займов старших 55+ падает с 29.9%.
  P2 дарение: значимая доля дефицита молодёжи гасится дарением до займа;
     доля объёма займов 18–25 падает с 14.3%; λ < базы.
  P3 «дед» (сытость+дарение): λ ниже, чем каждая по отдельности
     (эффекты бьют в разные клапаны — старость и молодёжь).
  P4 ALGO+дарение: gift_total = 0 — в бессмертном носителе никто не
     доживает до «старому ничего не надо» (возраст заморожен в 40):
     механизм дарения мёртв ПО ПОСТРОЕНИЮ, не по параметру.

ДЕТЕРМИНИЗМ: np.random.default_rng(7); добавленные ветки НЕ потребляют rng —
базовый прогон воспроизводит v4 (A_u_жизньx1, λ=4.59) бит в бит.
СТАТУС: E — исполнение упрёка заказчика; изоляция двух операторов
(насыщение, трансмиссия-при-жизни), не открытие.
=============================================================================
"""
import json
import hashlib
import sys
import numpy as np

OUT_DIR = '/home/z/my-project/scripts/ring1_v4_2_out'
PNG_OUT = '/home/z/my-project/download/КОЛЬЦО-1_v4_2_дарение_и_сытость.png'

Q_BREAK = 0.15
C_A = 0.10
Q_FP = 0.02


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    tot = x.sum()
    if n == 0 or tot <= 0:
        return 0.0
    cum = np.cumsum(x)
    return float((n + 1 - 2.0 * (cum / tot).sum()) / n)


def run(rho='A', T1=True, T2=True, T3=True, T4=True, sigma=True,
        phi=0.0, jubilee=0, capture=False, tau=0.0,
        tau_t=0.0, audit=False, kappa_liq=1.0,
        life_mult=1.0, freeze_age=False,
        satiate=False, sat_age=65.0, sat_frac=0.5,
        gift=False, gift_age=60.0, s_keep=140.0, g_frac=0.25,
        gift_young_max=30.0,
        N=200, T=300, i_rate=0.06, seed=7, subsist=70.0, stress=0.5,
        g0=15.0, ymax=8.0):
    rng = np.random.default_rng(seed)
    age = rng.uniform(18.0, 50.0, N)
    if freeze_age:
        age[:] = 40.0
    life = 18.0 + rng.uniform(30.0, 60.0, N) * life_mult
    life = np.maximum(life, age + 2.0)
    u = rng.uniform(0.4, 1.6, N)
    cls = np.where(u < 1.0, 'бед', 'им')
    d = np.zeros(N)
    s = rng.uniform(0.0, 20.0, N)
    y_mult = 1.0

    lots = [[] for _ in range(N)]
    lot_seq = [0]
    n_deaths = [0]
    rec_by_cls = {'бед': [], 'им': []}
    dcls = {'бед': 0, 'им': 0}
    n_audit_kill = [0]
    n_fp_kill = [0]
    n_transfers = [0]
    gift_total = [0.0]
    gift_covered = [0.0]
    broken_share_ts = np.zeros(T)
    vol = {'young': 0.0, 'prime': 0.0, 'old': 0.0}
    pop = {'young': 0.0, 'prime': 0.0, 'old': 0.0}

    D = np.zeros(T); Y = np.zeros(T); POOL = np.zeros(T)
    DEFR = np.zeros(T); GS = np.zeros(T); GIFT = np.zeros(T)

    def bucket(a):
        return 'young' if a < 25.0 else ('prime' if a < 55.0 else 'old')

    for t in range(T):
        shocks = rng.uniform(0.7, 1.3, N)
        y_base = 100.0 * y_mult * u * np.minimum(age / 25.0, 1.0) \
                 * np.clip(1.0 - (age - 55.0) / 30.0, 0.3, 1.0)
        y_eff = y_base * shocks * (1.0 - stress * np.clip(
            d / np.maximum(3.0 * y_base * shocks, 1.0), 0.0, 1.0))

        # v4.2: кривая насыщения — «старому меньше надо»
        if satiate:
            ramp = np.clip((age - sat_age) / 10.0, 0.0, 1.0)
            need_mult = 1.0 - (1.0 - sat_frac) * ramp
        else:
            need_mult = np.ones(N)

        if T3:
            d *= (1.0 + i_rate)
            for i in range(N):
                for L in lots[i]:
                    L['p'] *= (1.0 + i_rate)

        if tau_t > 0:
            for i in range(N):
                li = lots[i]
                if not li:
                    continue
                r = rng.random(len(li))
                for j in np.where(r < tau_t)[0]:
                    L = li[j]
                    L['hist'].append((t, 'holder_transfer'))
                    L['transfers'] += 1
                    n_transfers[0] += 1
                    if not L.get('broken') and rng.random() < Q_BREAK:
                        L['broken'] = True
                        L['hist'].append((t, 'lineage_break'))

        if audit:
            for i in range(N):
                li = lots[i]
                if not li:
                    continue
                r = rng.random(len(li))
                dead_idx = []
                for j in np.where(r < C_A)[0]:
                    L = li[j]
                    if L.get('broken'):
                        dead_idx.append(j)
                        L['hist'].append((t, 'audit_extinguish'))
                        n_audit_kill[0] += 1
                    elif rng.random() < Q_FP:
                        dead_idx.append(j)
                        L['hist'].append((t, 'audit_false_positive'))
                        n_fp_kill[0] += 1
                if dead_idx:
                    lots[i] = [L for j, L in enumerate(li) if j not in dead_idx]
                    d[i] = sum(L['p'] for L in lots[i])

        if capture:
            net = (1.0 - tau) * y_eff
            cons = np.maximum(subsist, 0.6 * net)
            short = np.maximum(cons - net, 0.0)
            s = np.maximum(s - short, 0.0)
            s += np.maximum(net - cons, 0.0)
            pool = float(tau * y_eff.sum())
        else:
            cons = np.maximum(subsist * need_mult, 0.6 * y_eff)
            short = np.maximum(cons - y_eff, 0.0)

            # v4.2: дарение при жизни — излишек стариков гасит дефицит
            # молодых ДО того, как он станет займом
            if gift:
                donors = (age >= gift_age) & (s > s_keep)
                G = np.where(donors, g_frac * (s - s_keep), 0.0)
                w = np.where((age < gift_young_max) & (short > 0),
                             short, 0.0)
                tw = float(w.sum())
                if tw > 0 and G.sum() > 0:
                    s -= G
                    gift_total[0] += float(G.sum())
                    alloc = float(G.sum()) * w / tw
                    covered = np.minimum(short, alloc)
                    short = short - covered
                    gift_covered[0] += float(covered.sum())
                    s += alloc - covered  # излишек — в сбережения получателя

            if T1 and sigma:
                d += short
                for i in np.where(short > 0)[0]:
                    lot_seq[0] += 1
                    lots[i].append({'id': lot_seq[0], 'p': float(short[i]),
                                    'birth': t, 'deaths': 0, 'transfers': 0,
                                    'broken': False,
                                    'hist': [(t, 'orig')]})
                    vol[bucket(age[i])] += float(short[i])
            else:
                s = np.maximum(s - short, 0.0)
            if T2 and T3:
                pool = 0.0
                for i in range(N):
                    li = lots[i]
                    d_ok = sum(L['p'] for L in li if not L.get('broken'))
                    avail = max(y_eff[i] - cons[i], 0.0)
                    inc_pay = min(d_ok, avail)
                    liq = min(s[i], kappa_liq * (d_ok - inc_pay))
                    if inc_pay + liq > 0:
                        rem = inc_pay + liq
                        for L in li:
                            if rem <= 1e-9:
                                break
                            if L.get('broken'):
                                continue
                            take = min(L['p'], rem)
                            L['p'] -= take
                            rem -= take
                        lots[i] = [L for L in li if L['p'] > 1e-9]
                        d[i] = sum(L['p'] for L in lots[i])
                        s[i] -= liq
                    pool += inc_pay + liq
            else:
                pool = 0.0

        tot_s = float(s.sum())
        if tot_s > 0:
            s += pool * (s / tot_s)
        if phi > 0:
            y_mult = min(y_mult * (1.0 + phi * pool /
                                   max(float(y_eff.sum()), 1.0)), ymax)

        if jubilee and (t + 1) % jubilee == 0:
            for i in range(N):
                for L in lots[i]:
                    L['hist'].append((t, 'jubilee'))
                lots[i] = []
            d[:] = 0.0

        dead = age >= life
        k = int(dead.sum())
        if k:
            n_deaths[0] += k
            dp, sp = d[dead].copy(), s[dead].copy()
            for i in np.where(dead)[0]:
                dcls[cls[i]] += 1
            if not T4:
                d_new = np.zeros(k)
                s_new = sp + g0
                for i in np.where(dead)[0]:
                    for L in lots[i]:
                        L['hist'].append((t, 'carrier_death_terminal'))
                    lots[i] = []
            elif rho == 'A':
                d_new, s_new = dp.copy(), sp.copy() + g0
                for i in np.where(dead)[0]:
                    for L in lots[i]:
                        L['deaths'] += 1
                        L['hist'].append((t, 'carrier_death'))
            elif rho == 'B':
                seizure = np.minimum(dp, sp)
                if T2 and T3:
                    pool += float(seizure.sum())
                s_new = np.maximum(sp - dp, 0.0) + g0
                d_new = np.zeros(k)
                for j, i in enumerate(np.where(dead)[0]):
                    if dp[j] > 1e-9:
                        rec_by_cls[cls[i]].append(float(seizure[j] / dp[j]))
                    for L in lots[i]:
                        L['hist'].append((t, 'asset_settled'))
                    lots[i] = []
            else:
                s_new = np.zeros(k) + g0
                d_new = np.zeros(k)
                for i in np.where(dead)[0]:
                    for L in lots[i]:
                        L['hist'].append((t, 'reset'))
                    lots[i] = []
            d[dead], s[dead] = d_new, s_new
            age[dead] = 18.0
            life[dead] = 18.0 + rng.uniform(30.0, 60.0, k) * life_mult
            for i in np.where(dead)[0]:
                u[i] = rng.uniform(0.4, 1.6)
                cls[i] = 'бед' if u[i] < 1.0 else 'им'
        if not freeze_age:
            age += 1.0

        bcount = {'young': 0, 'prime': 0, 'old': 0}
        for a in age:
            bcount[bucket(a)] += 1
        for b in vol:
            pop[b] += bcount[b] / N

        tot_p = sum(L['p'] for i in range(N) for L in lots[i])
        brk_p = sum(L['p'] for i in range(N) for L in lots[i]
                    if L.get('broken'))
        broken_share_ts[t] = brk_p / tot_p if tot_p > 0 else 0.0
        D[t], Y[t], POOL[t] = float(d.sum()), float(y_eff.sum()), pool
        DEFR[t] = float(np.mean(d > 5.0 * np.maximum(y_base, 1.0)))
        GS[t] = gini(s)
        GIFT[t] = gift_covered[0]

    flat = [L for i in range(N) for L in lots[i]]
    tot_p = sum(L['p'] for L in flat)
    max_carrier = max((L['deaths'] for L in flat), default=0)
    mean_holder = (sum(L['transfers'] * L['p'] for L in flat) / tot_p
                   if tot_p > 0 else 0.0)
    vol_share = {b: (vol[b] / sum(vol.values()) if sum(vol.values()) > 0
                     else 0.0) for b in vol}
    pop_share = {b: pop[b] / T for b in vol}
    young_borrowed = vol['young']
    covered_share = (gift_covered[0] / (gift_covered[0] + young_borrowed)
                     if (gift_covered[0] + young_borrowed) > 0 else 0.0)

    tt = np.arange(T, dtype=float)
    slope = float(np.polyfit(tt, np.log(D + 1.0), 1)[0])
    lam = float(np.exp(25.0 * slope))
    crises = np.where(DEFR > 0.2)[0]
    return dict(lam=lam, D_over_Y=float(D[-1] / max(Y[-1], 1.0)),
                n_crisis=int(crises.size),
                first_crisis=int(crises[0]) if crises.size else -1,
                defr_end=float(DEFR[-1]), gini=float(GS[-1]),
                pool_over_Y=float(np.mean(POOL[50:] / np.maximum(Y[50:], 1.0))),
                n_deaths=int(n_deaths[0]), n_lots_end=len(flat),
                max_carrier_depth=int(max_carrier),
                mean_holder_depth=float(mean_holder),
                n_transfers=int(n_transfers[0]),
                gift_total=float(gift_total[0]),
                gift_covered=float(gift_covered[0]),
                gift_covered_share=float(covered_share),
                vol_share=vol_share, pop_share=pop_share,
                broken_share_final=float(broken_share_ts[-1]),
                rec_by_cls={'бед': {'mean': (float(np.mean(rec_by_cls['бед']))
                                             if rec_by_cls['бед'] else None),
                                    'n': len(rec_by_cls['бед'])},
                            'им': {'mean': (float(np.mean(rec_by_cls['им']))
                                            if rec_by_cls['им'] else None),
                                   'n': len(rec_by_cls['им'])}},
                deaths_by_cls=dict(dcls),
                D=D, GS=GS, Y=Y, POOL=POOL, GIFT=GIFT)


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    results = {}
    LAM_FLOOR = float(1.06 ** 25)  # λ_пол = e^{25·i} — сток растёт процентом
    configs = [
        ('A_u_база',      dict(rho='A')),                       # якорь = v4 x1
        ('A_u_сытость',   dict(rho='A', satiate=True)),
        ('A_u_дарение',   dict(rho='A', gift=True)),
        ('A_u_дед',       dict(rho='A', satiate=True, gift=True)),
        ('A_u_дар_макс',  dict(rho='A', gift=True, g_frac=1.0, s_keep=70.0)),
        ('A_u_дед_макс',  dict(rho='A', satiate=True, gift=True,
                               g_frac=1.0, s_keep=70.0)),
        ('A_u_ALGO',      dict(rho='A', freeze_age=True)),
        ('A_u_ALGO_дар',  dict(rho='A', freeze_age=True, gift=True)),
    ]
    for name, kw in configs:
        results[name] = run(**kw)

    hdr = (f"{'конфигурация':<15}{'λ25':>7}{'D/Y':>10}{'Gini':>6}{'E/Y':>7}"
           f"{'смертей':>8}{'дар-во':>10}{'покр.мол':>9}")
    print(hdr)
    print('-' * len(hdr))
    for name, r in results.items():
        print(f"{name:<15}{r['lam']:>7.2f}{r['D_over_Y']:>10.3g}"
              f"{r['gini']:>6.2f}{r['pool_over_Y']:>7.4f}{r['n_deaths']:>8}"
              f"{r['gift_total']:>10.3g}{r['gift_covered_share']*100:>8.1f}%")

    print("\nP1 сытость: λ "
          f"{results['A_u_база']['lam']:.2f} → {results['A_u_сытость']['lam']:.2f}; "
          "инъекция 55+: объём "
          f"{results['A_u_база']['vol_share']['old']*100:.1f}% → "
          f"{results['A_u_сытость']['vol_share']['old']*100:.1f}% "
          "(население "
          f"{results['A_u_сытость']['pop_share']['old']*100:.1f}%)")
    print("P2 дарение: λ "
          f"{results['A_u_база']['lam']:.2f} → {results['A_u_дарение']['lam']:.2f}; "
          f"покрыто дарением {results['A_u_дарение']['gift_covered_share']*100:.1f}% "
          "молодёжного спроса на займ; инъекция 18–25: объём "
          f"{results['A_u_база']['vol_share']['young']*100:.1f}% → "
          f"{results['A_u_дарение']['vol_share']['young']*100:.1f}%")
    print("P3 дед: λ "
          f"{results['A_u_дед']['lam']:.2f}  (сытость "
          f"{results['A_u_сытость']['lam']:.2f}, дарение "
          f"{results['A_u_дарение']['lam']:.2f}, база "
          f"{results['A_u_база']['lam']:.2f})")
    print("P4 ALGO+дарение: gift_total = "
          f"{results['A_u_ALGO_дар']['gift_total']:.3g} "
          "(механизм мёртв по построению: возраст заморожен в 40, "
          "никто не доживает до «старому ничего не надо»)")
    print(f"\nПОЛ СТАВКИ: λ_пол = 1.06^25 = {LAM_FLOOR:.2f}; "
          "премия над полом (вся сумма клапанов жизни):")
    for nm in ['A_u_база', 'A_u_сытость', 'A_u_дарение', 'A_u_дед',
               'A_u_дар_макс', 'A_u_дед_макс', 'A_u_ALGO']:
        r = results[nm]
        print(f"  {nm:<15} λ={r['lam']:.2f}  премия "
              f"{100*(r['lam']/LAM_FLOOR-1):+.1f}%  "
              f"D/Y={r['D_over_Y']:.3g}  Gini={r['gini']:.2f}")
    print("клапан до/дед (объём/население):")
    for b, lab in [('young', '18–25'), ('prime', '25–55'), ('old', '55+')]:
        rb, rd = results['A_u_база'], results['A_u_дед']
        print(f"  {lab}: {rb['vol_share'][b]*100:.1f}%/"
              f"{rb['pop_share'][b]*100:.1f}% → "
              f"{rd['vol_share'][b]*100:.1f}%/"
              f"{rd['pop_share'][b]*100:.1f}%")

    meta = {
        'python': sys.version.split()[0], 'numpy': np.__version__,
        'seed': 7,
        'lambda_definition': 'λ25 = exp(25·slope log(D+1)), T=300',
        'status': 'E — исполнение упрёка заказчика (раунд 7)',
        'preregistered': ['P1 сытость закрывает старостный клапан, λ↓',
                          'P2 дарение гасит дефицит молодёжи до займа, λ↓',
                          'P3 дед < каждой по отдельности',
                          'P4 ALGO+дарение: gift_total=0 (мёртв по построению)'],
        'new_channels_vs_v4': ['satiate: потребность 1.0→0.5·subsist после 65',
                               'gift: g_frac=0.25 излишка (s>140, age≥60) вниз, '
                               'age<30, пропорционально дефициту, до займа',
                               'предельные: g_frac=1.0, s_keep=70'],
        'lambda_floor': 'λ_пол = 1.06^25 = 4.29 — сток растёт процентом; '
                        'клапаны жизни (рождение/старость/дарение) '
                        '= премия над полом',
        'reproducibility': 'базовый прогон = v4 A_u_жизньx1 (rng не тронут)',
    }
    export = {'meta': meta, 'runs': {}}
    for name, r in results.items():
        export['runs'][name] = {k: v for k, v in r.items()
                                if k not in ('D', 'GS', 'Y', 'POOL', 'GIFT')}
    blob = json.dumps(export, ensure_ascii=False, sort_keys=True)
    h = hashlib.sha256(blob.encode()).hexdigest()
    export['integrity'] = {'results_sha256': h}
    with open(f'{OUT_DIR}/results.json', 'w') as f:
        json.dump(export, f, ensure_ascii=False, indent=1)
    with open(f'{OUT_DIR}/timeseries.csv', 'w') as f:
        f.write('run,tick,D,Y,pool,gift_covered\n')
        for name, r in results.items():
            for t in range(300):
                f.write(f"{name},{t},{r['D'][t]:.6f},{r['Y'][t]:.6f},"
                        f"{r['POOL'][t]:.6f},{r['GIFT'][t]:.6f}\n")
    print(f"\nsha256(results) = {h}")
    print(f"выход: {OUT_DIR}/results.json, timeseries.csv")

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.6),
                             constrained_layout=True)
    # (а) λ по режимам + пол ставки
    ax = axes[0]
    keys = ['A_u_база', 'A_u_дарение', 'A_u_дед', 'A_u_дар_макс',
            'A_u_дед_макс']
    labs = ['база\n(v4 ×1)', 'дарение', 'дед', 'дарение\nмакс', 'дед\nмакс']
    vals = [results[k]['lam'] for k in keys]
    bars = ax.bar(range(5), vals,
                  color=['#555555', '#2E8B57', '#8B0000', '#7CCD7C', '#CD3333'])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.03, f'{v:.2f}',
                ha='center', fontsize=9)
    ax.axhline(LAM_FLOOR, color='#B8860B', ls='--', lw=1.5)
    ax.text(4.45, LAM_FLOOR + 0.02, f'пол ставки\n1.06^25={LAM_FLOOR:.2f}',
            fontsize=8, color='#B8860B', ha='right')
    ax.set_ylim(4.0, 4.75)
    ax.set_xticks(range(5))
    ax.set_xticklabels(labs, fontsize=8.5)
    ax.set_title('λ25: упрёк исполнен — λ стоит на проценте\n'
                 '(клапаны жизни = премия над полом)',
                 fontsize=10.5)
    ax.set_ylabel('λ25', fontsize=9.5)
    ax.grid(alpha=0.3, axis='y')
    # (б) клапан до/после «деда»
    ax = axes[1]
    r0, r1 = results['A_u_база'], results['A_u_дед']
    x = np.arange(3)
    v1 = [r0['vol_share'][b] * 100 for b in ['young', 'prime', 'old']]
    v2 = [r0['pop_share'][b] * 100 for b in ['young', 'prime', 'old']]
    v3 = [r1['vol_share'][b] * 100 for b in ['young', 'prime', 'old']]
    ax.bar(x - 0.22, v1, width=0.22, label='объём займов, база', color='#8B0000')
    ax.bar(x, v2, width=0.22, label='население, база', color='#999999')
    ax.bar(x + 0.22, v3, width=0.22, label='объём займов, «дед»', color='#2E8B57')
    ax.set_xticks(x)
    ax.set_xticklabels(['18–25', '25–55', '55+'])
    ax.set_title('Клапан инъекции до и после\n(объём займов vs население, %)',
                 fontsize=10.5)
    ax.set_ylabel('%', fontsize=9.5)
    ax.legend(fontsize=7.5)
    ax.grid(alpha=0.3, axis='y')
    # (в) D(t)
    ax = axes[2]
    for key, lab, c in [('A_u_база', 'база', '#555555'),
                        ('A_u_сытость', 'сытость', '#4682B4'),
                        ('A_u_дарение', 'дарение', '#2E8B57'),
                        ('A_u_дед', 'дед (оба)', '#8B0000')]:
        y = results[key]['D'].copy()
        y[y <= 0] = np.nan
        ax.plot(y, lw=1.5, label=lab, color=c)
    ax.set_yscale('log')
    ax.set_title('ΣD(t), log', fontsize=10.5)
    ax.set_xlabel('тики', fontsize=9.5)
    ax.set_ylabel('ΣD', fontsize=9.5)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.suptitle('КОЛЬЦО-1 v4.2: насыщение и дарение при жизни. '
                 'N=200, T=300, seed=7, ρ=A', fontsize=11)
    fig.savefig(PNG_OUT, dpi=150)
    print(f"PNG сохранён: {PNG_OUT}")


if __name__ == '__main__':
    main()
