#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
КОЛЬЦО-1_v4.py — СМЕРТНОСТЬ НОСИТЕЛЯ И АЛГОРИТМИЧЕСКИЙ НОСИТЕЛЬ.
Исполнение поворота коллеги (раунд 6): «ПРАВИЛО → АЛГОРИТМ → ДАННЫЕ →
ПРОВЕРКА → ПЕРЕДАЧА → ДЕЙСТВИЕ» — его контур, замкнутый нашими операторами.
База: механика v1–v3 сохранена (base воспроизводит λ≈5.87–5.89).
=============================================================================

ИСПРАВЛЕНИЕ v4.1 (отзыв дефекта v3): в v1–v3 гетерогенность доходов была
  ТОЛЬКО возрастной; метка класса (u<1/u≥1) НЕ БЫЛА подключена к доходу —
  класс-тест v3 измерял шум и ОТЗЫВАЕТСЯ. В v4.1 доход = y_base·u·shock:
  класс подключён, класс-тест перезапускается честно (B_u_hard/soft).
  Механика v4 = v3 + u·shock в доходе — НОВАЯ СЕМЕЙСТВА чисел; база
  пересчитана; числа v1–v3 остаются валидными для своей конфигурации.

ВОПРОС РАУНДА (коллега §«алгоритмы»): «зачем в контуре человеческий оператор?»
Наш ответ операторной алгеброй — носитель-человек делает в кольце три вещи,
которые алгоритмическому носителю не достались бесплатно:
  (1) ОН СМЕРТЕН — его смерть создаёт ρ-события: гасит (B/C), переносит (A)
      и ВПУСКАЕТ нового заёмщика (наследник стартует ниже прожиточного
      минимума — рождение есть впускной клапан машины);
  (2) ОН СТАРЕЕТ — продуктивность имеет горб и спад; вторая граница жизни
      (старость) — второй впускной клапан;
  (3) ОН — ОТДЕЛЬНОЕ ОТ КОНТУРА ИСПОЛНЕНИЯ МЕСТО ПРИЁМКИ НА КОРЕНЬ
      (может спросить «откуда требование», а не только «исполнимо ли»).

ИСПЫТАНИЯ (все seed=7, механика v1–v3 вербатим, отличия только в носителе):
  Q1  m-свип: жизнь ×{1,2,4} — λ(смертность). Предсказание: λ РАСТЁТ со
      смертностью в режиме A (смерть = не тормоз, а впускной клапан:
      молодняк 18–25 заёмает непропорционально + наследование компаундит).
  Q2  био-бессмертие (life_mult=1e9, старение идёт) — машина без границ?
  Q3  ALGO-носитель: смерть выключена, возраст заморожен в 40 (продуктивность
      постоянна) — это «ПРАВИЛО → АЛГОРИТМ → ДАННЫЕ» из письма коллеги.
      Предсказания: (а) родословная по смертям замирает: carrier-depth ≡ 0,
      вся живая ось идентичности уходит на τ-сторону (передачи держателей);
      (б) ρ-таблица пустеет — некому маршрутизировать; (в) юбилей остаётся
      единственным размыкателем λ; (г) инъекция новых займов теряет границы
      жизни — топливо машины = только хронические должники.
  Q4  ALGO + оборот + аудит: чисто τ-сторонняя машина.

ИНЪЕКЦИОННАЯ МЕТРИКА (прямое измерение «рождение = впускной клапан»):
  объём новых займов по возрастным вёдрам (18–25 / 25–55 / 55+) против
  средней доли населения в тех же вёдрах.

ОПРЕДЕЛЕНИЕ λ: как в v1–v3 — λ25 = exp(25·наклон log(D+1)), T=300, seed=7.
НОВЫЕ КАНАЛЫ ПЕРЕНОСА против v3: нет (life_mult/freeze_age меняют только
  частоту срабатывания существующих каналов).
ДЕТЕРМИНИЗМ: np.random.default_rng(7); numpy — единственная зависимость.
СТАТУС: E/G — изоляция операторов, НЕ открытие; ALGO-носитель — модельная
  конструкция, а не утверждение о существующих системах.
=============================================================================
"""
import json
import hashlib
import sys
import numpy as np

OUT_DIR = '/home/z/my-project/scripts/ring1_v4_out'
PNG_OUT = '/home/z/my-project/download/КОЛЬЦО-1_v4_смертность_и_алгоноситель.png'

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
    broken_share_ts = np.zeros(T)
    # инъекция: объём займов и население по вёдрам возраста
    vol = {'young': 0.0, 'prime': 0.0, 'old': 0.0}
    pop = {'young': 0.0, 'prime': 0.0, 'old': 0.0}

    D = np.zeros(T); Y = np.zeros(T); POOL = np.zeros(T)
    DEFR = np.zeros(T); GS = np.zeros(T)

    def bucket(a):
        return 'young' if a < 25.0 else ('prime' if a < 55.0 else 'old')

    for t in range(T):
        shocks = rng.uniform(0.7, 1.3, N)
        y_base = 100.0 * y_mult * u * np.minimum(age / 25.0, 1.0) \
                 * np.clip(1.0 - (age - 55.0) / 30.0, 0.3, 1.0)
        y_eff = y_base * shocks * (1.0 - stress * np.clip(
            d / np.maximum(3.0 * y_base * shocks, 1.0), 0.0, 1.0))

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
            cons = np.maximum(subsist, 0.6 * y_eff)
            short = np.maximum(cons - y_eff, 0.0)
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

        # население по вёдрам (для сравнения с объёмом займов)
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

    flat = [L for i in range(N) for L in lots[i]]
    tot_p = sum(L['p'] for L in flat)
    max_carrier = max((L['deaths'] for L in flat), default=0)
    mean_holder = (sum(L['transfers'] * L['p'] for L in flat) / tot_p
                   if tot_p > 0 else 0.0)
    vol_share = {b: (vol[b] / sum(vol.values()) if sum(vol.values()) > 0
                     else 0.0) for b in vol}
    pop_share = {b: pop[b] / T for b in vol}

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
                n_audit_kill=int(n_audit_kill[0]),
                n_fp_kill=int(n_fp_kill[0]),
                vol_share=vol_share, pop_share=pop_share,
                broken_share_final=float(broken_share_ts[-1]),
                rec_by_cls={'бед': {'mean': (float(np.mean(rec_by_cls['бед']))
                                             if rec_by_cls['бед'] else None),
                                    'n': len(rec_by_cls['бед'])},
                            'им': {'mean': (float(np.mean(rec_by_cls['им']))
                                            if rec_by_cls['им'] else None),
                                   'n': len(rec_by_cls['им'])}},
                deaths_by_cls=dict(dcls),
                D=D, GS=GS, Y=Y, POOL=POOL)


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    results = {}
    configs = [
        ('A_u_жизньx1',   dict(rho='A', life_mult=1.0)),          # новая база семьи v4
        ('A_u_жизньx2',   dict(rho='A', life_mult=2.0)),
        ('A_u_жизньx4',   dict(rho='A', life_mult=4.0)),
        ('A_u_биобессм',  dict(rho='A', life_mult=1e9)),          # старение без смерти
        ('A_u_ALGO',      dict(rho='A', freeze_age=True)),         # без смерти и старения
        ('A_u_ALGO_юб',   dict(rho='A', freeze_age=True, jubilee=30)),
        ('A_u_ALGO_об+а', dict(rho='A', freeze_age=True, tau_t=0.05, audit=True)),
        ('B_u_hard',      dict(rho='B', kappa_liq=1.0)),           # класс-тест: жёсткое взыскание
        ('B_u_soft',      dict(rho='B', kappa_liq=0.3)),           # класс-тест: мягкое взыскание
    ]
    for name, kw in configs:
        results[name] = run(**kw)

    hdr = (f"{'конфигурация':<15}{'λ25':>7}{'D/Y':>11}{'Gini':>6}{'E/Y':>7}"
           f"{'смертей':>8}{'max.gl':>7}{'hold.gl':>8}{'пер.':>7}")
    print(hdr)
    print('-' * len(hdr))
    for name, r in results.items():
        print(f"{name:<15}{r['lam']:>7.2f}{r['D_over_Y']:>11.3g}"
              f"{r['gini']:>6.2f}{r['pool_over_Y']:>7.4f}{r['n_deaths']:>8}"
              f"{r['max_carrier_depth']:>7}{r['mean_holder_depth']:>8.2f}"
              f"{r['n_transfers']:>7}")

    print("\nQ1 λ(смертность): "
          + ' → '.join(f"{results[k]['lam']:.2f}" for k in
                       ['A_u_жизньx1', 'A_u_жизньx2', 'A_u_жизньx4', 'A_u_биобессм']))
    print("Q1b инъекция A_u_жизньx1 (объём займов / доля населения):")
    for b, lab in [('young', '18–25'), ('prime', '25–55'), ('old', '55+')]:
        r = results['A_u_жизньx1']
        print(f"  {lab}: объём {r['vol_share'][b]*100:.1f}% / "
              f"население {r['pop_share'][b]*100:.1f}%")
    print("Q3 ALGO-носитель: carrier-depth max = "
          f"{results['A_u_ALGO']['max_carrier_depth']}; "
          f"λ(ALGO)={results['A_u_ALGO']['lam']:.2f}; "
          f"λ(ALGO+юб)={results['A_u_ALGO_юб']['lam']:.2f}; "
          f"λ(ALGO+об+а)={results['A_u_ALGO_об+а']['lam']:.2f}")
    print("Q3 ALGO инъекция (объём/население): "
          + ', '.join(f"{b}:{results['A_u_ALGO']['vol_share'][b]*100:.0f}%/"
                      f"{results['A_u_ALGO']['pop_share'][b]*100:.0f}%"
                      for b in ['young', 'prime', 'old']))
    print("R3 класс-тест (исправленный, u в доходе):")
    for nm in ['B_u_hard', 'B_u_soft']:
        r = results[nm]
        fb, fi = r['rec_by_cls']['бед'], r['rec_by_cls']['им']
        fbs = f"{fb['mean']:.2f} (n={fb['n']})" if fb['mean'] is not None else '—'
        fis = f"{fi['mean']:.2f} (n={fi['n']})" if fi['mean'] is not None else '—'
        print(f"  {nm}: recovery бед={fbs}; им={fis}")

    meta = {
        'python': sys.version.split()[0], 'numpy': np.__version__,
        'seed': 7,
        'lambda_definition': 'λ25 = exp(25·slope log(D+1)), T=300',
        'status': 'E/G — изоляция операторов, не открытие',
        'preregistered': ['Q1 λ растёт со смертностью в режиме A',
                          'Q1b инъекция займов на границах жизни',
                          'Q3 ALGO: carrier-depth≡0, ось идентичности на τ-стороне',
                          'Q3 юбилей — единственный размыкатель ALGO',
                          'Q3 инъекция ALGO теряет границы жизни'],
        'transfer_channels': ['наследование d,s (ρ=A)', 'estate-гашение (ρ=B)',
                              'g0=15 ex nihilo', 'юбилей', 'рента пула ∝ s',
                              'займы σ', 'стресс долга', 'holder_transfer',
                              'audit_extinguish / false_positive'],
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

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.6),
                             constrained_layout=True)
    # (а) λ по режимам носителя
    ax = axes[0]
    keys = ['A_u_жизньx1', 'A_u_жизньx2', 'A_u_жизньx4', 'A_u_биобессм', 'A_u_ALGO']
    labs = ['жизнь\n×1', '×2', '×4', 'био-\nбессмерт', 'ALGO\n(без границ)']
    vals = [results[k]['lam'] for k in keys]
    bars = ax.bar(range(5), vals,
                  color=['#8B0000', '#A52A2A', '#CD5C5C', '#4682B4', '#2F4F4F'])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.06, f'{v:.2f}',
                ha='center', fontsize=9)
    ax.set_xticks(range(5))
    ax.set_xticklabels(labs, fontsize=8.5)
    ax.set_title('λ25 по режиму носителя\n(режим ρ=A, всё прочее одинаково)',
                 fontsize=10.5)
    ax.set_ylabel('λ25', fontsize=9.5)
    ax.grid(alpha=0.3, axis='y')
    # (б) инъекция: объём займов vs население
    ax = axes[1]
    r = results['A_u_жизньx1']
    x = np.arange(3)
    v1 = [r['vol_share'][b] * 100 for b in ['young', 'prime', 'old']]
    v2 = [r['pop_share'][b] * 100 for b in ['young', 'prime', 'old']]
    ax.bar(x - 0.18, v1, width=0.36, label='доля объёма новых займов',
           color='#8B0000')
    ax.bar(x + 0.18, v2, width=0.36, label='средняя доля населения',
           color='#999999')
    ax.set_xticks(x)
    ax.set_xticklabels(['18–25', '25–55', '55+'])
    ax.set_title('Впускной клапан: заёмы по границам жизни\n(база, жизнь ×1)',
                 fontsize=10.5)
    ax.set_ylabel('%', fontsize=9.5)
    ax.legend(fontsize=8.5)
    ax.grid(alpha=0.3, axis='y')
    # (в) D(t) ALGO-варианты
    ax = axes[2]
    for key, lab, c in [('A_u_ALGO', 'ALGO', '#2F4F4F'),
                        ('A_u_ALGO_юб', 'ALGO+юбилей 30', '#B8860B'),
                        ('A_u_ALGO_об+а', 'ALGO+оборот+аудит', '#2E8B57'),
                        ('A_u_биобессм', 'био-бессмертный', '#4682B4')]:
        y = results[key]['D'].copy()
        y[y <= 0] = np.nan
        ax.plot(y, lw=1.5, label=lab, color=c)
    ax.set_yscale('log')
    ax.set_title('Алгоритмический носитель: ΣD(t), log', fontsize=10.5)
    ax.set_xlabel('тики', fontsize=9.5)
    ax.set_ylabel('ΣD', fontsize=9.5)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.suptitle('КОЛЬЦО-1 v4: носитель смертный vs алгоритмический. '
                 'N=200, T=300, seed=7, ρ=A', fontsize=11)
    fig.savefig(PNG_OUT, dpi=150)
    print(f"PNG сохранён: {PNG_OUT}")


if __name__ == '__main__':
    main()
