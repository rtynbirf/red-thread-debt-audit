#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
КОЛЬЦО-1_v3.py — ПРИЁМКА (A_ver) И ОБОРОТ (τ-сторона держателя).
Исполнение матрицы коллеги (раунд 5): lineage × acceptance, численно.
База: механика v1/v2 сохранена дословно (base_A воспроизводит 5.87).
=============================================================================

НОВОЕ ПРОТИВ v2 (всё — по заданиям коллеги, его §4–§5):

1) КЛАСС ДОЛЖНИКА (тест его оставленного-F предсказания
   «имущественный класс объясняет S_D сильнее формы договора»):
   класс = знак (u−1): u<1 — бедный, u≥1 — имущий. Распределение u
   НЕ ИЗМЕНЕНО (U(0.4,1.6)) — классы это срез того же населения.
   В ρ=B при смерти: recovery f = min(d,s)/d записывается ПО КЛАССАМ.
   Предсказание P1: f_им > 0, f_бед ≈ 0 при ОДИНАКОВОЙ форме договора.

2) ОБОРОТ ДЕРЖАТЕЛЯ (τ-сторона, его §1: MERS/eRegistry):
   каждая доля с вероятностью tau_t в тик передаётся держателю:
   событие ('holder_transfer', t) в журнал; с вероятностью q_break=0.15
   передача ДЕФЕКТНА (обрыв lineage — якорь GAO-11-433 / ФРС robo-signing):
   lot.broken=True. Оборванная доля НЕ ВЗЫСКИВАЕТСЯ (нет законной силы),
   но продолжает компаундить (запись живёт).

3) ПРИЁМКА A_ver (его §4–§5: расщепление A на A_ext/A_ver):
   с вероятностью c_a=0.10 в тик доля аудируется.
   - аудирована и broken → гасится (истребление непрослеживаемого);
   - аудирована и чиста → с вероятностью q_fp=0.02 гасится ЛОЖНО
     (ошибка приёмки I рода — «провал годного», Type I).
   Аудит НЕ ищет корень (Ψ⁻¹=∅ у долга) — он сверяет ЦЕЛОСТНОСТЬ ЦЕПИ,
   не истинность требования. Это приёмка на исполнимость, не на корень.

ПРЕДРЕГИСТРАЦИЯ (моя, до прогона — зеркально его дисциплине):
   P1: recovery по классам расходится в базе B (им > 0, бед ≈ 0).
   P2: средняя holder-глубина растёт монотонно по tau_t (depth~turnover).
   P3: доля оборванного запаса растёт по tau_t (нагрузка рвёт родословную).
   P4: аудит гасит оборванный запас (broken share ниже при audit=on),
       НО E/Y падает против базы без оборота — оборот съедает базу
       извлечения; аудит лишь переводит скрытый дефолт в явный.
   P5: номинальный λ выше в noaudit-прогонах (зомби-компаундинг обрывов).

МАТРИЦА КОЛЛЕГИ (его §5) → ячейки:
   (lineage−, acceptance−) = T2-выкл v2: зомби λ=5.88, Gini 0.06, E≡0
   (lineage+, acceptance−) = base_A3 / t005_noaudit: переносимое требование
                             + накапливающийся оборванный запас
   (lineage−, acceptance+) = capture+ревизия: проверяемый неустойчивый поток
   (lineage+, acceptance+) = t*_audit: аудируемый канон (обрывы истребляются)

ОПРЕДЕЛЕНИЕ λ: как в v1/v2 — λ25 = exp(25·наклон log(D+1)), T=300, seed=7.
ПОЛНЫЙ СПИСОК КАНАЛОВ ПЕРЕНОСА: как в v2 + holder_transfer (держатель-сторона)
   + истребление аудитом (обрыв/ложное срабатывание). ДРУГИХ НЕТ.
ДЕТЕРМИНИЗМ: np.random.default_rng(7) на прогон; numpy — единственная зависимость.
СТАТУС: E/G — изоляция операторов в силлоговом пространстве, НЕ открытие.
=============================================================================
"""
import json
import hashlib
import sys
import numpy as np

OUT_DIR = '/home/z/my-project/scripts/ring1_v3_out'
PNG_OUT = '/home/z/my-project/download/КОЛЬЦО-1_v3_приёмка_и_оборот.png'

Q_BREAK = 0.15   # дефектная передача (обрыв lineage) — якорь GAO/ФРС
C_A = 0.10       # охват аудита в тик
Q_FP = 0.02      # ложное истребление годного (ошибка I рода)


def gini(x):
    x = np.sort(np.asarray(x, dtype=float))
    n = x.size
    tot = x.sum()
    if n == 0 or tot <= 0:
        return 0.0
    cum = np.cumsum(x)
    return float((n + 1 - 2.0 * (cum / tot).sum()) / n)


def top_share(x, q=0.10):
    x = np.sort(np.asarray(x, dtype=float))
    k = max(1, int(round(q * x.size)))
    tot = x.sum()
    return float(x[-k:].sum() / tot) if tot > 0 else 0.0


def run(rho='A', T1=True, T2=True, T3=True, T4=True, sigma=True,
        phi=0.0, jubilee=0, capture=False, tau=0.0,
        tau_t=0.0, audit=False, kappa_liq=1.0,
        N=200, T=300, i_rate=0.06, seed=7, subsist=70.0, stress=0.5,
        g0=15.0, ymax=8.0):
    rng = np.random.default_rng(seed)
    age = rng.uniform(18.0, 50.0, N)
    life = 18.0 + rng.uniform(30.0, 60.0, N)
    life = np.maximum(life, age + 2.0)
    u = rng.uniform(0.4, 1.6, N)
    cls = np.where(u < 1.0, 'бед', 'им')          # класс по конституции дохода
    d = np.zeros(N)
    s = rng.uniform(0.0, 20.0, N)
    y_mult = 1.0

    lots = [[] for _ in range(N)]                  # родословная: журнал долей
    lot_seq = [0]
    rec_by_cls = {'бед': [], 'им': []}             # recovery при смерти (ρ=B)
    deaths_by_cls = {'бед': 0, 'им': 0}
    n_audit_kill = [0]                             # истреблено обрывов
    n_fp_kill = [0]                                # ложных истреблений
    n_transfers = [0]                              # всего передач держателя
    broken_share_ts = np.zeros(T)                  # доля оборванного запаса

    D = np.zeros(T); Y = np.zeros(T); POOL = np.zeros(T)
    DEFR = np.zeros(T); GS = np.zeros(T); TOP = np.zeros(T)

    for t in range(T):
        y_base = 100.0 * y_mult * np.minimum(age / 25.0, 1.0) \
                 * np.clip(1.0 - (age - 55.0) / 30.0, 0.3, 1.0)
        y_eff = y_base * (1.0 - stress * np.clip(
            d / np.maximum(3.0 * y_base, 1.0), 0.0, 1.0))

        # --- проценты [T3] (запись компаундит независимо от целостности) ---
        if T3:
            d *= (1.0 + i_rate)
            for i in range(N):
                for L in lots[i]:
                    L['p'] *= (1.0 + i_rate)

        # --- ОБОРОТ ДЕРЖАТЕЛЯ [τ-сторона] + обрывы ---
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

        # --- ПРИЁМКА [A_ver] ---
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

        # --- capture-режим: дань без записи ---
        if capture:
            net = (1.0 - tau) * y_eff
            cons = np.maximum(subsist, 0.6 * net)
            short = np.maximum(cons - net, 0.0)
            s = np.maximum(s - short, 0.0)
            s += np.maximum(net - cons, 0.0)
            pool = float(tau * y_eff.sum())
        else:
            cons = np.maximum(subsist, 0.6 * y_eff)
            short = np.maximum(cons - y_eff, 0.0)
            # --- заём / проедание [σ, T1] ---
            if T1 and sigma:
                d += short
                for i in np.where(short > 0)[0]:
                    lot_seq[0] += 1
                    lots[i].append({'id': lot_seq[0], 'p': float(short[i]),
                                    'birth': t, 'deaths': 0, 'transfers': 0,
                                    'broken': False,
                                    'hist': [(t, 'orig')]})
            else:
                s = np.maximum(s - short, 0.0)
            # --- взыскание [T2∧T3] — ТОЛЬКО целые доли ---
            if T2 and T3:
                pool = 0.0
                for i in range(N):
                    li = lots[i]
                    d_ok = sum(L['p'] for L in li if not L.get('broken'))
                    avail = max(y_eff[i] - cons[i], 0.0)
                    inc_pay = min(d_ok, avail)             # из дохода
                    liq = min(s[i], kappa_liq * (d_ok - inc_pay))  # из имущества (остаток, интенсивность κ_liq)
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
            s += pool * (s / tot_s)          # рента пула — имущим ∝ s [D4]
        if phi > 0:
            y_mult = min(y_mult * (1.0 + phi * pool /
                                   max(float(y_eff.sum()), 1.0)), ymax)

        # --- юбилей ---
        if jubilee and (t + 1) % jubilee == 0:
            for i in range(N):
                for L in lots[i]:
                    L['hist'].append((t, 'jubilee'))
                lots[i] = []
            d[:] = 0.0

        # --- смерть и перенос [T4, ρ] ---
        dead = age >= life
        k = int(dead.sum())
        if k:
            dp, sp = d[dead].copy(), s[dead].copy()
            for j, i in enumerate(np.where(dead)[0]):
                deaths_by_cls[cls[i]] += 1
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
                    pool += float(seizure.sum())   # estate → пул (правка v2)
                s_new = np.maximum(sp - dp, 0.0) + g0
                d_new = np.zeros(k)
                for j, i in enumerate(np.where(dead)[0]):
                    if dp[j] > 1e-9:
                        f = float(seizure[j] / dp[j])
                        rec_by_cls[cls[i]].append(f)
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
            life[dead] = 18.0 + rng.uniform(30.0, 60.0, k)
            # наследник: класс перерисовывается (u~U(0.4,1.6)), u наследует?
            for i in np.where(dead)[0]:
                u[i] = rng.uniform(0.4, 1.6)
                cls[i] = 'бед' if u[i] < 1.0 else 'им'
        age += 1.0

        # метрики тика
        tot_p = sum(L['p'] for i in range(N) for L in lots[i])
        brk_p = sum(L['p'] for i in range(N) for L in lots[i]
                    if L.get('broken'))
        broken_share_ts[t] = brk_p / tot_p if tot_p > 0 else 0.0
        D[t], Y[t], POOL[t] = float(d.sum()), float(y_eff.sum()), pool
        DEFR[t] = float(np.mean(d > 5.0 * np.maximum(y_base, 1.0)))
        GS[t], TOP[t] = gini(s), top_share(s)

    # --- родословная на конец прогона ---
    flat = [L for i in range(N) for L in lots[i]]
    tot_p = sum(L['p'] for L in flat)
    hcnt = {b: 0 for b in [0, 1, 2, 3, 4, 5]}
    hstk = {b: 0.0 for b in [0, 1, 2, 3, 4, 5]}
    for L in flat:
        b = min(L['transfers'], 5)
        hcnt[b] += 1
        hstk[b] += L['p']
    holder_depth_stock = {str(b): (hstk[b] / tot_p if tot_p > 0 else 0.0)
                          for b in [0, 1, 2, 3, 4, 5]}
    mean_holder_depth = (sum(L['transfers'] * L['p'] for L in flat) / tot_p
                         if tot_p > 0 else 0.0)
    max_depth = max((L['deaths'] for L in flat), default=0)
    sample = sorted(flat, key=lambda L: -(L['deaths'] + L['transfers']))[:3]
    sample_chains = [{'id': L['id'], 'p': round(L['p'], 2), 'birth': L['birth'],
                      'deaths': L['deaths'], 'transfers': L['transfers'],
                      'broken': L.get('broken', False),
                      'hist': L['hist'][-10:]} for L in sample]

    tt = np.arange(T, dtype=float)
    slope = float(np.polyfit(tt, np.log(D + 1.0), 1)[0])
    lam = float(np.exp(25.0 * slope))
    crises = np.where(DEFR > 0.2)[0]
    dY = np.diff(Y[50:]) / np.maximum(Y[50:-1], 1.0)
    corr = float('nan')
    if np.std(dY) > 0 and np.std(POOL[50:-1]) > 0:
        corr = float(np.corrcoef(dY, POOL[50:-1])[0, 1])
    rec_stats = {}
    for c, vals in rec_by_cls.items():
        rec_stats[c] = {'mean': float(np.mean(vals)) if vals else None,
                        'n': len(vals)}
    return dict(lam=lam, D_over_Y=float(D[-1] / max(Y[-1], 1.0)),
                n_crisis=int(crises.size),
                first_crisis=int(crises[0]) if crises.size else -1,
                defr_end=float(DEFR[-1]), gini=float(GS[-1]),
                top=float(TOP[-1]),
                Y_growth=float(np.mean(dY)) * 100.0, corr_dY_R=corr,
                pool_over_Y=float(np.mean(POOL[50:] / np.maximum(Y[50:], 1.0))),
                n_lots_end=len(flat), max_carrier_depth=int(max_depth),
                mean_holder_depth=float(mean_holder_depth),
                holder_depth_stock=holder_depth_stock,
                broken_share_final=float(broken_share_ts[-1]),
                broken_share_max=float(broken_share_ts.max()),
                n_transfers=int(n_transfers[0]),
                n_audit_kill=int(n_audit_kill[0]),
                n_fp_kill=int(n_fp_kill[0]),
                rec_by_cls=rec_stats, deaths_by_cls=deaths_by_cls,
                sample_chains=sample_chains,
                D=D, GS=GS, Y=Y, POOL=POOL, broken_share_ts=broken_share_ts)


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    results = {}

    configs = [
        ('base_A3',        dict(rho='A')),                                   # контроль (λ≈5.87)
        ('base_B3',        dict(rho='B')),                                   # класс-тест
        ('base_B3_soft',   dict(rho='B', kappa_liq=0.3)),                    # класс-тест при мягком взыскании
        ('t001_audit',     dict(rho='A', tau_t=0.01, audit=True)),           # канон, слабый оборот
        ('t005_noaudit',   dict(rho='A', tau_t=0.05, audit=False)),          # lineage+, приёмка−
        ('t005_audit',     dict(rho='A', tau_t=0.05, audit=True)),           # канон, средний оборот
        ('t020_noaudit',   dict(rho='A', tau_t=0.20, audit=False)),          # нагрузка без приёмки
        ('t020_audit',     dict(rho='A', tau_t=0.20, audit=True)),           # канон под нагрузкой
        ('capture_ревиз',  dict(rho='A', T1=False, capture=True, tau=0.0091,
                                audit=True)),                                 # поток+приёмка
    ]
    for name, kw in configs:
        results[name] = run(**kw)

    hdr = (f"{'конфигурация':<15}{'λ25':>7}{'D/Y':>11}{'Gini':>6}{'E/Y':>7}"
           f"{'обрыв,доля':>11}{'hold.gl':>8}{'аудит-kill':>10}{'FP':>5}"
           f"{'f(бед)':>8}{'f(им)':>7}")
    print(hdr)
    print('-' * len(hdr))
    for name, r in results.items():
        lam = f"{r['lam']:.2f}"
        fb = r['rec_by_cls']['бед']
        fi = r['rec_by_cls']['им']
        fbs = f"{fb['mean']:.2f}({fb['n']})" if fb['mean'] is not None else '—'
        fis = f"{fi['mean']:.2f}({fi['n']})" if fi['mean'] is not None else '—'
        print(f"{name:<15}{lam:>7}{r['D_over_Y']:>11.3g}{r['gini']:>6.2f}"
              f"{r['pool_over_Y']:>7.4f}{r['broken_share_final']:>11.3f}"
              f"{r['mean_holder_depth']:>8.2f}{r['n_audit_kill']:>10}"
              f"{r['n_fp_kill']:>5}{fbs:>8}{fis:>7}")

    print()
    for c in ['бед', 'им']:
        dc = results['base_B3']['deaths_by_cls'][c]
        rc = results['base_B3']['rec_by_cls'][c]
        print(f"base_B3: класс «{c}»: смертей с долгом={dc}, "
              f"средний recovery={rc['mean']}, n={rc['n']}")
    print("\nP2 depth~turnover (средняя holder-глубина): "
          f"τ=0.01:{results['t001_audit']['mean_holder_depth']:.2f} "
          f"τ=0.05:{results['t005_audit']['mean_holder_depth']:.2f} "
          f"τ=0.20:{results['t020_audit']['mean_holder_depth']:.2f}")
    print("P3 обрывы (доля оборванного запаса): "
          f"τ=0.05 audit={results['t005_audit']['broken_share_final']:.3f} "
          f"noaudit={results['t005_noaudit']['broken_share_final']:.3f}; "
          f"τ=0.20 audit={results['t020_audit']['broken_share_final']:.3f} "
          f"noaudit={results['t020_noaudit']['broken_share_final']:.3f}")
    print("P4 E/Y: база без оборота="
          f"{results['base_A3']['pool_over_Y']:.4f}; "
          f"τ=0.05 audit={results['t005_audit']['pool_over_Y']:.4f}; "
          f"τ=0.20 audit={results['t020_audit']['pool_over_Y']:.4f}")
    sc = results['t005_audit']['sample_chains']
    if sc:
        print(f"пример цепочки (t005_audit): {json.dumps(sc[0], ensure_ascii=False)}")

    # --- JSON ---
    meta = {
        'python': sys.version.split()[0], 'numpy': np.__version__,
        'seed': 7,
        'lambda_definition': 'λ25 = exp(25·slope log(D+1)), T=300',
        'q_break': Q_BREAK, 'c_audit': C_A, 'q_fp': Q_FP,
        'status': 'E/G — изоляция операторов, не открытие',
        'preregistered': ['P1 класс>договор в B', 'P2 depth~turnover',
                          'P3 обрывы растут с оборотом',
                          'P4 аудит гасит обрывы, E/Y падает от оборота',
                          'P5 зомби-компаундинг в noaudit'],
        'transfer_channels': ['наследование d,s (ρ=A)', 'estate-гашение (ρ=B)',
                              'g0=15 ex nihilo', 'юбилей', 'рента пула ∝ s',
                              'займы σ', 'стресс долга',
                              'holder_transfer (τ-сторона)',
                              'audit_extinguish / false_positive (A_ver)'],
    }
    export = {'meta': meta, 'runs': {}}
    for name, r in results.items():
        export['runs'][name] = {k: v for k, v in r.items()
                                if k not in ('D', 'GS', 'Y', 'POOL',
                                             'broken_share_ts')}
    blob = json.dumps(export, ensure_ascii=False, sort_keys=True)
    h = hashlib.sha256(blob.encode()).hexdigest()
    export['integrity'] = {'results_sha256': h}
    with open(f'{OUT_DIR}/results.json', 'w') as f:
        json.dump(export, f, ensure_ascii=False, indent=1)
    with open(f'{OUT_DIR}/timeseries.csv', 'w') as f:
        f.write('run,tick,D,Y,pool,broken_share\n')
        for name, r in results.items():
            for t in range(300):
                f.write(f"{name},{t},{r['D'][t]:.6f},{r['Y'][t]:.6f},"
                        f"{r['POOL'][t]:.6f},{r['broken_share_ts'][t]:.6f}\n")
    print(f"\nsha256(results) = {h}")
    print(f"выход: {OUT_DIR}/results.json, timeseries.csv")

    # --- PNG: 3 панели ---
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.6),
                             constrained_layout=True)
    # (а) обрывы во времени
    ax = axes[0]
    for key, lab, c in [('t005_noaudit', 'τ=0.05 без приёмки', '#B8860B'),
                        ('t005_audit', 'τ=0.05 с приёмкой', '#2E8B57'),
                        ('t020_noaudit', 'τ=0.20 без приёмки', '#8B0000'),
                        ('t020_audit', 'τ=0.20 с приёмкой', '#4682B4')]:
        ax.plot(results[key]['broken_share_ts'], lw=1.5, label=lab, color=c)
    ax.set_title('Доля оборванного запаса (broken/ΣD)', fontsize=10.5)
    ax.set_xlabel('тики', fontsize=9.5)
    ax.set_ylabel('доля запаса', fontsize=9.5)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    # (б) holder-глубина ~ оборот
    ax = axes[1]
    keys = ['t001_audit', 't005_audit', 't020_audit']
    labels = ['τ=0.01', 'τ=0.05', 'τ=0.20']
    width = 0.26
    buckets = ['0', '1', '2', '3', '4', '5']
    colors = ['#999999', '#C0C0C0', '#8B0000', '#A52A2A', '#CD5C5C', '#F08080']
    for bi, b in enumerate(buckets):
        vals = [results[k]['holder_depth_stock'][b] for k in keys]
        x = np.arange(3) + (bi - 2.5) * width
        ax.bar(x, vals, width=width, label=f'глубина {b}', color=colors[bi])
    ax.set_xticks(range(3))
    ax.set_xticklabels(labels)
    ax.set_title('Запас по holder-глубине: depth~turnover', fontsize=10.5)
    ax.set_xlabel('интенсивность оборота τ', fontsize=9.5)
    ax.set_ylabel('доля запаса', fontsize=9.5)
    ax.legend(fontsize=7.5, ncol=2)
    ax.grid(alpha=0.3, axis='y')
    # (в) класс-тест
    ax = axes[2]
    r = results['base_B3']
    cats = ['бедные', 'имущие']
    means = [r['rec_by_cls']['бед']['mean'] or 0, r['rec_by_cls']['им']['mean'] or 0]
    ns = [r['rec_by_cls']['бед']['n'], r['rec_by_cls']['им']['n']]
    bars = ax.bar(cats, means, color=['#555555', '#8B0000'], alpha=0.85,
                  width=0.5)
    for b, v, n in zip(bars, means, ns):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.01,
                f'{v:.3f}\n(n={n})', ha='center', fontsize=9)
    ax.set_ylim(0, 1.05)
    ax.set_title('ρ=B: recovery estate ПО КЛАССАМ\n(форма договора одна и та же)',
                 fontsize=10.5)
    ax.set_ylabel('средний recovery min(d,s)/d', fontsize=9.5)
    ax.grid(alpha=0.3, axis='y')
    fig.suptitle('КОЛЬЦО-1 v3: приёмка A_ver и оборот τ — матрица коллеги численно. '
                 'N=200, T=300, seed=7', fontsize=11)
    fig.savefig(PNG_OUT, dpi=150)
    print(f"PNG сохранён: {PNG_OUT}")


if __name__ == '__main__':
    main()
