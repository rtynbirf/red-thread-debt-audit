#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
КОЛЬЦО-1_v2.py — абляция T1–T4 + capture-развилка + родословная требований
(оператор I). Развитие канонического КОЛЬЦО-1 (ring1_sim.py, раунд 3)
по предрегистрации коллеги (раунд 4).
=============================================================================

МЕХАНИКА v1 СОХРАНЕНА ДОСЛОВНО (сравнимость λ; база A воспроизводит 5.87).
Порядок тика v1 (зафиксирован для аудита):
  1) продуктивность: горб возраста (min(age/25,1), спад после 55 clip 0.3..1) × y_mult
  2) стресс долга: y_eff = y_base·(1 − 0.5·clip(d/3y_base, 0, 1))
  3) проценты: d ×= (1+0.06)                                   [T3]
  4) потребление: cons = max(70, 0.6·y_eff)
  5) заём на прожиточный минимум: d += max(cons−y_eff, 0)      [σ, T1]
  6) обслуживание: inc_pay = min(max(y_eff−cons,0), d);
     ликвидация: liq = min(s, d−inc_pay)                       [T2∧T3]
  7) пул = inc_pay + liq; рента пула — имущим ∝ s               [D4-канал]
  8) φ-канал: y_mult ×= (1+φ·пул/Σy_eff), cap 8
  9) юбилей каждые K тиков: d := 0                              [падёж по закону]
 10) смерть (age≥life 48–78); перенос ρ (+g0=15 всем наследникам) [T4]
 11) age += 1

ЕДИНСТВЕННАЯ ПРАВКА v2 (задокументирована, влияет только на B):
  В v1 ρ=B гасила заявку активом (s_new = max(s−d,0)), но изъятое min(d,s)
  ИСПАРЯЛОСЬ — не зачислялось в пул. В v2 estate-изъятие зачисляется в пул
  (при T2∧T3). λ_B от этого НЕ меняется (запас d в B умирает на смерти так же),
  меняются пул/рента/Gini. База A не затронута.

ВЫКЛЮЧАТЕЛИ (предрегистрация коллеги, его §7):
  T1 запись         : OFF → требование не существует как объект:
                          разрыв съедается имуществом/голодом, d ≡ 0.
                          (В безликом пуле T1-OFF ≡ σ-OFF: кредит = запись.)
  T2 квалификация   : OFF → записи и проценты есть, взыскания нет (пул ≡ 0).
                          Зомби-запас: номинальный рост без исполнимости.
  T3 извлечение     : OFF → нет процентов И взыскания (E ≡ 0).
                          Запас растёт только аддитивно (новые займы).
  T4 воспроизводство: OFF → требование строго личное: умирает с носителем.
                          Имущество s наследуется (право собственности живо).

CAPTURE-КОНТРОЛЬ (критическая развилка коллеги, его §7-контроль):
  T1 OFF + прямое изъятие τ·y_eff у источника (дань), БЕЗ записи и взыскания.
  τ калибруется = средний (пул/Y) базы A после разогрева (измерено, не подогнано).
  Вопрос развилки: поддерживает ли дань извлечение без запаса требований?

РОДОСЛОВНАЯ (I-оператор коллеги, его §8):
  Каждая доля требования несёт: id, тик рождения, число пережитых смертей
  носителя, журнал событий (orig / carrier_death / asset_settled / reset /
  jubilee / terminal). Метрики: гистограмма глубины lineage по ЧИСЛУ долей
  и по ДОЛЕ ЗАПАСА; ключевая величина — ДОЛЯ ЗАПАСА, ПРИНАДЛЕЖАЩАЯ УЖЕ
  МЁРТВЫМ НОСИТЕЛЯМ (deaths ≥ 1). Симуляционный реестр хранит родословную
  по построению → контрпример к универсальной форме «Lineage(Ψ)=∅»
  в абстракто; эмпирический вопрос остаётся за классами физических реестров.

ОПРЕДЕЛЕНИЕ λ (как в v1, для сравнимости):
  λ25 = exp(25 · наклон log(D+1)) по всем 300 тикам — устойчив к юбилейным
  пилам и сбросам. λ25>1 ⇔ взрыв запаса, λ25≈1 ⇔ стационарность.

ПОЛНЫЙ СПИСОК КАНАЛОВ ПЕРЕНОСА (аудит «скрытых каналов нет»):
  1) наследование d и s (ρ=A); 2) estate-гашение (ρ=B, зачисление в пул —
  правка v2); 3) подъёмные g0=15 всем наследникам (ex nihilo);
  4) юбилей (гашение d, s не трогается); 5) рента пула имущим ∝ s;
  6) новые займы σ (заём на прожиточный минимум); 7) стресс долга на
  продуктивность. ДРУГИХ ПЕРЕНОСОВ НЕТ.

ДЕТЕРМИНИЗМ: np.random.default_rng(7) на каждый прогон (как в v1);
  numpy — единственная зависимость. Статус результатов: E/G — демонстрация
  изоляции операторов в силлоговом пространстве, НЕ открытие; параметры
  игрушечные, зафиксированы до прогона; принуждение/реестр неявны.
=============================================================================
"""
import json
import hashlib
import sys
import numpy as np

OUT_DIR = '/home/z/my-project/scripts/ring1_v2_out'
PNG_OUT = '/home/z/my-project/download/КОЛЬЦО-1_v2_абляция_и_родословная.png'


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
        N=200, T=300, i_rate=0.06, seed=7, subsist=70.0, stress=0.5,
        g0=15.0, ymax=8.0):
    rng = np.random.default_rng(seed)
    age = rng.uniform(18.0, 50.0, N)
    life = 18.0 + rng.uniform(30.0, 60.0, N)
    life = np.maximum(life, age + 2.0)
    d = np.zeros(N)
    s = rng.uniform(0.0, 20.0, N)
    y_mult = 1.0

    # родословная: lots[i] — список долей агента i
    lots = [[] for _ in range(N)]
    lot_seq = [0]
    recover_fracs = []      # ρ=B: доля заявки, погашенная активом estate
    depth_hist = None
    depth_stock = None
    stock_dead = float('nan')
    max_depth = 0
    n_lots_end = 0
    sample_chains = []

    D = np.zeros(T); Y = np.zeros(T); POOL = np.zeros(T)
    DEFR = np.zeros(T); GS = np.zeros(T); TOP = np.zeros(T)

    for t in range(T):
        y_base = 100.0 * y_mult * np.minimum(age / 25.0, 1.0) \
                 * np.clip(1.0 - (age - 55.0) / 30.0, 0.3, 1.0)
        y_eff = y_base * (1.0 - stress * np.clip(
            d / np.maximum(3.0 * y_base, 1.0), 0.0, 1.0))

        # --- проценты [T3] ---
        if T3:
            d *= (1.0 + i_rate)
            for i in range(N):
                for L in lots[i]:
                    L['p'] *= (1.0 + i_rate)

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
                                    'birth': t, 'deaths': 0,
                                    'hist': [(t, 'orig')]})
            else:
                # T1 OFF: записи нет — требование не существует как объект
                s = np.maximum(s - short, 0.0)
            # --- взыскание [T2∧T3] ---
            if T2 and T3:
                inc_pay = np.minimum(np.maximum(y_eff - cons, 0.0), d)
                liq = np.minimum(s, d - inc_pay)
                s -= liq
                d -= (inc_pay + liq)
                collected = inc_pay + liq
                pool = float(collected.sum())
                for i in np.where(collected > 1e-12)[0]:
                    rem = float(collected[i])
                    while rem > 1e-9 and lots[i]:
                        L = lots[i][0]
                        take = min(L['p'], rem)
                        L['p'] -= take
                        rem -= take
                        if L['p'] <= 1e-9:
                            lots[i].pop(0)
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
            if not T4:
                d_new = np.zeros(k)
                s_new = sp + g0
                for j, i in enumerate(np.where(dead)[0]):
                    for L in lots[i]:
                        L['hist'].append((t, 'carrier_death_terminal'))
                    lots[i] = []
            elif rho == 'A':
                d_new, s_new = dp.copy(), sp.copy() + g0
                for i in np.where(dead)[0]:
                    for L in lots[i]:
                        L['deaths'] += 1
                        L['hist'].append((t, 'carrier_death'))
                    max_depth = max(max_depth,
                                    max((L['deaths'] for L in lots[i]),
                                        default=0))
            elif rho == 'B':
                seizure = np.minimum(dp, sp)
                if T2 and T3:
                    pool += float(seizure.sum())   # ПРАВКА v2: estate → пул
                s_new = np.maximum(sp - dp, 0.0) + g0
                d_new = np.zeros(k)
                for j, i in enumerate(np.where(dead)[0]):
                    f = float(seizure[j] / dp[j]) if dp[j] > 1e-9 else 1.0
                    if dp[j] > 1e-9:
                        recover_fracs.append(f)
                    for L in lots[i]:
                        L['hist'].append((t, 'asset_settled', round(f, 4)))
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
        age += 1.0

        D[t], Y[t], POOL[t] = float(d.sum()), float(y_eff.sum()), pool
        DEFR[t] = float(np.mean(d > 5.0 * np.maximum(y_base, 1.0)))
        GS[t], TOP[t] = gini(s), top_share(s)

    # --- родословная на конец прогона ---
    flat = [L for i in range(N) for L in lots[i]]
    n_lots_end = len(flat)
    tot_p = sum(L['p'] for L in flat)
    buckets = [0, 1, 2, 3, 4, 5]
    cnt = {b: 0 for b in buckets}
    stk = {b: 0.0 for b in buckets}
    for L in flat:
        b = min(L['deaths'], 5)
        cnt[b] += 1
        stk[b] += L['p']
    depth_hist = {str(b): cnt[b] for b in buckets}
    depth_stock = {str(b): (stk[b] / tot_p if tot_p > 0 else 0.0)
                   for b in buckets}
    stock_dead = (sum(stk[b] for b in buckets if b >= 1) / tot_p
                  if tot_p > 0 else 0.0)
    if flat:
        deepest = sorted(flat, key=lambda L: -L['deaths'])[:5]
        sample_chains = [{'id': L['id'], 'p': round(L['p'], 2),
                          'birth': L['birth'], 'deaths': L['deaths'],
                          'hist': L['hist'][-12:]} for L in deepest]

    # --- метрики ---
    tt = np.arange(T, dtype=float)
    slope = float(np.polyfit(tt, np.log(D + 1.0), 1)[0])
    lam = float(np.exp(25.0 * slope))
    crises = np.where(DEFR > 0.2)[0]
    dY = np.diff(Y[50:]) / np.maximum(Y[50:-1], 1.0)
    corr = float('nan')
    if np.std(dY) > 0 and np.std(POOL[50:-1]) > 0:
        corr = float(np.corrcoef(dY, POOL[50:-1])[0, 1])
    return dict(lam=lam, D_over_Y=float(D[-1] / max(Y[-1], 1.0)),
                n_crisis=int(crises.size),
                first_crisis=int(crises[0]) if crises.size else -1,
                defr_end=float(DEFR[-1]), gini=float(GS[-1]),
                top=float(TOP[-1]),
                Y_growth=float(np.mean(dY)) * 100.0, corr_dY_R=corr,
                pool_over_Y=float(np.mean(POOL[50:] / np.maximum(Y[50:], 1.0))),
                n_lots_end=n_lots_end, depth_hist=depth_hist,
                depth_stock=depth_stock, stock_dead=float(stock_dead),
                max_depth=int(max_depth),
                B_recovery=(float(np.mean(recover_fracs))
                            if recover_fracs else None),
                B_n_deaths=len(recover_fracs),
                sample_chains=sample_chains,
                D=D, GS=GS, Y=Y, POOL=POOL)


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    results = {}

    # 0) база A — калибровка τ для capture
    r_A = run(rho='A')
    results['base_A'] = r_A
    tau = r_A['pool_over_Y']           # измерено, не подогнано

    configs = [
        ('base_B',          dict(rho='B')),
        ('base_C',          dict(rho='C')),
        ('T1выкл_запись',   dict(rho='A', T1=False)),
        ('T2выкл_квалиф',   dict(rho='A', T2=False)),
        ('T3выкл_извлеч',   dict(rho='A', T3=False)),
        ('T4выкл_перенос',  dict(rho='A', T4=False)),
        ('capture_дань',    dict(rho='A', T1=False, capture=True, tau=tau)),
        ('A_юбилей30',      dict(rho='A', jubilee=30)),
        ('A_phi025',        dict(rho='A', phi=0.25)),
        ('A_phi050',        dict(rho='A', phi=0.5)),
    ]
    for name, kw in configs:
        results[name] = run(**kw)

    # --- сводная таблица ---
    hdr = (f"{'конфигурация':<16}{'λ25':>7}{'D/Y':>13}{'криз.':>6}{'Gini':>6}"
           f"{'top10%':>7}{'E/Y':>7}{'макс.gl':>8}{'доля гл.мёртв':>14}")
    print(hdr)
    print('-' * len(hdr))
    for name, r in results.items():
        lam = f"{r['lam']:.2f}"
        sd = (f"{r['stock_dead']:.2f}" if r['stock_dead'] == r['stock_dead']
              else '—')
        print(f"{name:<16}{lam:>7}{r['D_over_Y']:>13.3g}{r['n_crisis']:>6}"
              f"{r['gini']:>6.2f}{r['top']:>7.2f}{r['pool_over_Y']:>7.3f}"
              f"{r['max_depth']:>8}{sd:>14}")

    print(f"\nτ (калибровка capture) = pool/Y базы A = {tau:.4f}")
    print(f"base_A: λ25={results['base_A']['lam']:.2f} "
          f"(v1: 5.87 — воспроизводимость)")
    print(f"base_B: recovery estate = {results['base_B']['B_recovery']} "
          f"по {results['base_B']['B_n_deaths']} смертям")
    sc = results['base_A']['sample_chains']
    if sc:
        print(f"base_A: глубочайшая родословная: deaths={sc[0]['deaths']}, "
              f"журнал={sc[0]['hist']}")

    # --- JSON ---
    meta = {
        'python': sys.version.split()[0],
        'numpy': np.__version__,
        'seed': 7,
        'lambda_definition': 'λ25 = exp(25·slope log(D+1)), T=300',
        'tau_capture': tau,
        'status': 'E/G — демонстрация изоляции операторов, не открытие',
        'v2_fix': 'estate-изъятие ρ=B зачисляется в пул (в v1 испарялось)',
        'transfer_channels': ['наследование d,s (ρ=A)', 'estate-гашение (ρ=B)',
                              'g0=15 ex nihilo', 'юбилей', 'рента пула ∝ s',
                              'займы σ', 'стресс долга'],
    }
    export = {'meta': meta, 'runs': {}}
    for name, r in results.items():
        export['runs'][name] = {k: v for k, v in r.items()
                                if k not in ('D', 'GS', 'Y', 'POOL')}
    blob = json.dumps(export, ensure_ascii=False, sort_keys=True)
    h = hashlib.sha256(blob.encode()).hexdigest()
    export['integrity'] = {'results_sha256': h}
    with open(f'{OUT_DIR}/results.json', 'w') as f:
        json.dump(export, f, ensure_ascii=False, indent=1)
    with open(f'{OUT_DIR}/timeseries.csv', 'w') as f:
        f.write('run,tick,D,Y,pool\n')
        for name, r in results.items():
            for t in range(300):
                f.write(f"{name},{t},{r['D'][t]:.6f},{r['Y'][t]:.6f},"
                        f"{r['POOL'][t]:.6f}\n")
    print(f"\nsha256(results) = {h}")
    print(f"выход: {OUT_DIR}/results.json, timeseries.csv")

    # --- PNG ---
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 4.8),
                             constrained_layout=True)
    panel1 = [('base_A', 'база ρ=A (все операторы)', '#8B0000'),
              ('T2выкл_квалиф', 'T2 выкл (зомби-запас)', '#B8860B'),
              ('T3выкл_извлеч', 'T3 выкл (аддитив)', '#2E8B57'),
              ('T4выкл_перенос', 'T4 выкл (требование личное)', '#4682B4'),
              ('A_юбилей30', 'ρ=A + юбилей 30', '#6A0DAD')]
    ax = axes[0]
    for key, label, color in panel1:
        y = results[key]['D'].copy()
        y[y <= 0] = np.nan
        ax.plot(y, lw=1.5, label=label, color=color)
    ax.set_yscale('log')
    ax.set_title('Абляция T₁–T₄: суммарная заявка ΣD(t), log', fontsize=10.5)
    ax.set_xlabel('тики (годы)', fontsize=9.5)
    ax.set_ylabel('ΣD', fontsize=9.5)
    ax.grid(alpha=0.3)
    ax2 = axes[1]
    ds = results['base_A']['depth_stock']
    keys = ['0', '1', '2', '3', '4', '5']
    labels = ['0 смертей\n(живой носитель)', '1', '2', '3', '4', '5+']
    vals = [ds[k] for k in keys]
    bars = ax2.bar(range(6), vals,
                   color=['#999999'] + ['#8B0000'] * 5, alpha=0.85)
    ax2.set_xticks(range(6))
    ax2.set_xticklabels(labels, fontsize=8.5)
    ax2.set_title('base_A: доля запаса ΣD по глубине родословной\n'
                  f"доля запаса у мёртвых носителей = "
                  f"{results['base_A']['stock_dead']:.2f}", fontsize=10.5)
    ax2.set_ylabel('доля запаса', fontsize=9.5)
    ax2.set_xlabel('число пережитых смертей носителя (deaths)', fontsize=9.5)
    ax2.grid(alpha=0.3, axis='y')
    for b, v in zip(bars, vals):
        if v > 0.01:
            ax2.text(b.get_x() + b.get_width() / 2, v + 0.01, f'{v:.2f}',
                     ha='center', fontsize=8.5)
    handles, labs = axes[0].get_legend_handles_labels()
    fig.legend(handles, labs, loc='outside lower center', ncols=3,
               fontsize=8.4)
    fig.suptitle('КОЛЬЦО-1 v2: предрегистрационная абляция коллеги + '
                 'родословная требований (I). N=200, T=300, seed=7',
                 fontsize=11)
    fig.savefig(PNG_OUT, dpi=150)
    print(f"PNG сохранён: {PNG_OUT}")


if __name__ == '__main__':
    main()
