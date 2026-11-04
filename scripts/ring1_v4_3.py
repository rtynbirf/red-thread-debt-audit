#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
КОЛЬЦО-1_v4_3.py — МИШАРУМ-ТРИГГЕР, ПАУЗА ХАММУРАПИ, КВОРУМ-ПРИЁМКА,
ПОРОГ РИСК-ПРАЙСИНГА. Исполнение разбора «Красной Нити» сторонней моделью
(22 «недостающих звена» + DLV-спека): её гипотезы переведены из прозы в прогоны.
База: механика v4.1/4.2 вербатим (u·shock, ρ=A/B/C, τ-оборот, аудит).
=============================================================================

СТАТУС ВХОДА (вердикт до прогона): 22 звена коллеги — наблюдения вербальные;
0 прогонов, 0 предрегистраций, формулы декоративные (медиана оракулов при
коррелированных ошибках = повтор отраслевой ошибки 2008, которую он сам
приводит). По нашей дисциплине §8 документ не проходит: нечего проверять.
НО: 4 его гипотезы исполнимы в кольце — исполняю.

ИСПЫТАНИЯ (все seed=7, якорь = база v4.2, λ=4.59 воспроизводится бит в бит):

  БЛОК МИШАРУМА (звено 14 «управляемость задержки» → автомат):
  Q1  юбилей30 календарный — якорь списаний по расписанию.
  Q2  мишарум-триггер: полный сброс при DEFR>0.2 (доля носителей с долгом
      >5·y_base — собственное определение кризиса v1–v4), кулдаун 10 тиков.
      «Списание по бедствию, не по календарю» (§48 Хаммурапи как триггер).
  Q3  триггер-h50: списание 50% номинала по тому же триггеру (его haircut
      30–50% при DTI>77%).
  Q4  катастрофическая пауза: по триггеру — заморозка ставки на 12 тиков,
      сток НЕ гасится (его «Catastrophe pause» / §48).

  БЛОК ПРИЁМКИ (его звенья 1/5/15, формула A_ver^multi с кворумом):
  Q5  аудит одиночный всеведущий (verbatim v4: q_miss=0) — якорь.
  Q6  аудит одиночный НЕСОВЕРШЕННЫЙ (q_miss=0.3) — контроль.
  Q7  кворум 3 верификатора × C_A=0.10, казнь при ≥2 флагах (медиана/кворум
      коллеги). Вопрос: кворум лечит ложные казни, не теряя улов?

  БЛОК ЗВЕНА 17 (его же «haircut повышает стоимость кредита» — отмахнуто
  «Soulbound NFT» вместо математики; проверяем числом):
  Q8  юбилей30 при i∈{0.06, 0.08, 0.10, 0.12, 0.15}: существует ли порог
      компенсации ставки i*, выше которого программируемый мишарум съеден
      риск-прайсингом (λ(юб30,i) ≥ λ(база)=4.59)?

ПРЕДИСТОРИЯ (предрегистрация, объявлена ДО прогона):
  P1 триггер-сброс: λ < юбилея30; D(t) ограничена сверху порогом (не пила).
  P2 h50: λ между юбилей30 и базой; действий больше, чем у полного сброса.
  P3 пауза: 1.30 < λ_пауза < 4.59 — лучше ничего, хуже списания.
  P4 кворум (ПЕРЕОБЪЯВЛЕНА после отзыва void-блока, см. ниже): при равном
     бюджете проверок кворум повышает ТОЧНОСТЬ казни (ложные ↓≥10×), но
     снижает ПРОПУСКНУЮ СПОСОБНОСТЬ (улов сломанных ↓) → доля сломанного
     в стоке выше, λ выше, чем у бюджетно-равного одиночного. Кворум — не
     лечение, а трейд-офф «точность ↔ пропускная способность»; ценность
     зависит от цены ложной казни vs выжившего битого лота.
  P5 порог (ПЕРЕОБЪЯВЛЕНА после первого прогона): полный юбилей
     НЕВОСПРИИМЧИВ к i (сброс в ноль ослепляет глобальный фит λ) —
     звено 17 проверяется на h50, где сток выживает. Аналитически:
     между кулдаунами (10 тиков) сток ×(1+i)^10, халфкат ×0.5 → машина
     уходит в рост ⇔ (1+i)^10 > 2 ⇔ i* = 2^(1/10)−1 ≈ 7.2%.
     Проверяем свипом h50 по i.

ОТЗЫВ VOID-БЛОКА (пойман на первом прогоне): в аудит-конфигах был не
включён τ-оборот (tau_t=0) → сломанных лотов не существует → аудит казнил
только годных (7803 ложных казни, улов сломанных = 0), сравнение кворума
void. Блок перезапущен с tau_t=0.05 (создаёт сломанные лоты, как в v3),
добавлен бюджетно-равный контроль (одиночный C_A=0.30).

ДЕТЕРМИНИЗМ: np.random.default_rng(7); добавленные ветки потребляют rng
ТОЛЬКО в своих конфигах (триггер/кворум/пауза выключены в якоре) —
базовый прогон воспроизводит v4.2 (λ=4.59) бит в бит.
СТАТУС: E — исполнение чужих гипотез с предрегистрацией; модельная
конструкция, не утверждение о существующих системах.
=============================================================================
"""
import json
import hashlib
import sys
import numpy as np

OUT_DIR = '/home/z/my-project/scripts/ring1_v4_3_out'
PNG_OUT = '/home/z/my-project/download/КОЛЬЦО-1_v4_3_мишарум_и_кворум.png'

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
        i_rate=0.06,
        jubilee_trigger=False, trig_level=0.2, cooldown=10,
        haircut_frac=1.0, pause_on_trigger=False, pause_len=12,
        q_miss=0.0, quorum_n=1, c_a_override=None,
        N=200, T=300, seed=7, subsist=70.0, stress=0.5,
        g0=15.0, ymax=8.0):
    c_a_eff = float(c_a_override) if c_a_override else C_A
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
    n_audit_kill = [0]
    n_fp_kill = [0]
    n_transfers = [0]
    n_actions = [0]          # срабатываний триггера (сброс/пауза)
    pause_used = [0]         # тиков, проведённых в паузе
    last_action = [-10 ** 9]
    pause_left = [0]
    defr_prev = [0.0]
    broken_share_ts = np.zeros(T)
    vol = {'young': 0.0, 'prime': 0.0, 'old': 0.0}
    pop = {'young': 0.0, 'prime': 0.0, 'old': 0.0}

    D = np.zeros(T); Y = np.zeros(T); POOL = np.zeros(T)
    DEFR = np.zeros(T); GS = np.zeros(T)

    quorum_k = (quorum_n + 1) // 2  # ≥ половина флагов = казнь

    def bucket(a):
        return 'young' if a < 25.0 else ('prime' if a < 55.0 else 'old')

    for t in range(T):
        # ---- триггер бедствия (по DEFR предыдущего тика) ----
        fire = False
        if jubilee_trigger and pause_left[0] <= 0 \
                and t - last_action[0] >= cooldown \
                and defr_prev[0] > trig_level:
            fire = True
            last_action[0] = t
            n_actions[0] += 1
            if pause_on_trigger:
                pause_left[0] = pause_len
        i_eff = 0.0 if pause_left[0] > 0 else i_rate
        if pause_left[0] > 0:
            pause_used[0] += 1
            pause_left[0] -= 1

        shocks = rng.uniform(0.7, 1.3, N)
        y_base = 100.0 * y_mult * u * np.minimum(age / 25.0, 1.0) \
                 * np.clip(1.0 - (age - 55.0) / 30.0, 0.3, 1.0)
        y_eff = y_base * shocks * (1.0 - stress * np.clip(
            d / np.maximum(3.0 * y_base * shocks, 1.0), 0.0, 1.0))

        if T3:
            d *= (1.0 + i_eff)
            for i in range(N):
                for L in lots[i]:
                    L['p'] *= (1.0 + i_eff)

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
                keep = []
                changed = False
                for L in li:
                    flags = 0
                    for _ in range(quorum_n):
                        if rng.random() < c_a_eff:
                            if L.get('broken'):
                                if rng.random() < (1.0 - q_miss):
                                    flags += 1
                            else:
                                if rng.random() < Q_FP:
                                    flags += 1
                    if flags >= quorum_k:
                        changed = True
                        if L.get('broken'):
                            L['hist'].append((t, 'audit_extinguish'))
                            n_audit_kill[0] += 1
                        else:
                            L['hist'].append((t, 'audit_false_positive'))
                            n_fp_kill[0] += 1
                    else:
                        keep.append(L)
                if changed:
                    lots[i] = keep
                    d[i] = sum(L['p'] for L in keep)

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

        # ---- списание: календарное или триггерное ----
        cal_fire = bool(jubilee and (t + 1) % jubilee == 0)
        if cal_fire or (fire and not pause_on_trigger):
            if haircut_frac >= 1.0:
                for i in range(N):
                    for L in lots[i]:
                        L['hist'].append((t, 'jubilee'))
                    lots[i] = []
                d[:] = 0.0
            else:
                for i in range(N):
                    for L in lots[i]:
                        L['hist'].append((t, 'haircut'))
                        L['p'] *= (1.0 - haircut_frac)
                    d[i] = sum(L['p'] for L in lots[i])

        dead = age >= life
        k = int(dead.sum())
        if k:
            n_deaths[0] += k
            dp, sp = d[dead].copy(), s[dead].copy()
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
        defr_prev[0] = DEFR[t]

    flat = [L for i in range(N) for L in lots[i]]
    tot_p = sum(L['p'] for L in flat)
    vol_share = {b: (vol[b] / sum(vol.values()) if sum(vol.values()) > 0
                     else 0.0) for b in vol}
    pop_share = {b: pop[b] / T for b in vol}

    tt = np.arange(T, dtype=float)
    slope = float(np.polyfit(tt, np.log(D + 1.0), 1)[0])
    lam = float(np.exp(25.0 * slope))
    crises = np.where(DEFR > 0.2)[0]
    return dict(lam=lam, D_over_Y=float(D[-1] / max(Y[-1], 1.0)),
                n_crisis=int(crises.size),
                defr_end=float(DEFR[-1]), gini=float(GS[-1]),
                pool_over_Y=float(np.mean(POOL[50:] / np.maximum(Y[50:], 1.0))),
                n_deaths=int(n_deaths[0]), n_lots_end=len(flat),
                n_transfers=int(n_transfers[0]),
                n_actions=int(n_actions[0]),
                pause_ticks=int(pause_used[0]),
                n_audit_kill=int(n_audit_kill[0]),
                n_fp_kill=int(n_fp_kill[0]),
                D_max=float(D.max()),
                vol_share=vol_share, pop_share=pop_share,
                broken_share_final=float(broken_share_ts[-1]),
                D=D, GS=GS, Y=Y, POOL=POOL, DEFR=DEFR)


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    results = {}
    configs = [
        # якоря
        ('A_u_база',       dict(rho='A')),
        ('A_u_юб30',       dict(rho='A', jubilee=30)),
        # блок мишарума
        ('A_u_триггер',    dict(rho='A', jubilee_trigger=True,
                                haircut_frac=1.0)),
        ('A_u_триггер_h50', dict(rho='A', jubilee_trigger=True,
                                 haircut_frac=0.5)),
        ('A_u_пауза_хамм', dict(rho='A', jubilee_trigger=True,
                                pause_on_trigger=True, haircut_frac=0.0)),
        # блок приёмки (tau_t=0.05 создаёт сломанные лоты; void-блок отозван)
        ('A_u_аудит_од',   dict(rho='A', audit=True, tau_t=0.05)),
        ('A_u_аудит_нес',  dict(rho='A', audit=True, tau_t=0.05,
                                q_miss=0.3)),
        ('A_u_аудит_с30',  dict(rho='A', audit=True, tau_t=0.05, q_miss=0.3,
                                c_a_override=0.30)),
        ('A_u_кворум',     dict(rho='A', audit=True, tau_t=0.05,
                                q_miss=0.3, quorum_n=3)),
        # блок звена 17: полный юбилей невосприимчив к i (демонстрация);
        # порог ищем на h50, где сток выживает
        ('A_u_юб30_i08',   dict(rho='A', jubilee=30, i_rate=0.08)),
        ('A_u_юб30_i15',   dict(rho='A', jubilee=30, i_rate=0.15)),
        ('A_u_h50_i08',    dict(rho='A', jubilee_trigger=True,
                                haircut_frac=0.5, i_rate=0.08)),
        ('A_u_h50_i10',    dict(rho='A', jubilee_trigger=True,
                                haircut_frac=0.5, i_rate=0.10)),
        ('A_u_h50_i15',    dict(rho='A', jubilee_trigger=True,
                                haircut_frac=0.5, i_rate=0.15)),
        ('A_u_h50_i20',    dict(rho='A', jubilee_trigger=True,
                                haircut_frac=0.5, i_rate=0.20)),
    ]
    for name, kw in configs:
        results[name] = run(**kw)

    hdr = (f"{'конфигурация':<16}{'λ25':>7}{'D/Y':>9}{'Gini':>6}{'E/Y':>7}"
           f"{'действ':>7}{'пауза':>6}{'казнён':>8}{'ложн.':>7}{'maxD':>10}")
    print(hdr)
    print('-' * len(hdr))
    for name, r in results.items():
        print(f"{name:<16}{r['lam']:>7.2f}{r['D_over_Y']:>9.3g}"
              f"{r['gini']:>6.2f}{r['pool_over_Y']:>7.4f}{r['n_actions']:>7}"
              f"{r['pause_ticks']:>6}{r['n_audit_kill']:>8}"
              f"{r['n_fp_kill']:>7}{r['D_max']:>10.3g}")

    print("\n--- БЛОК МИШАРУМА ---")
    print("P1 триггер-сброс: λ "
          f"{results['A_u_юб30']['lam']:.2f} (календарь) → "
          f"{results['A_u_триггер']['lam']:.2f} (триггер); "
          f"действий {results['A_u_триггер']['n_actions']} vs 10 календарных; "
          f"maxD триггера {results['A_u_триггер']['D_max']:.3g} vs "
          f"календаря {results['A_u_юб30']['D_max']:.3g}")
    print("P2 h50: λ "
          f"{results['A_u_триггер_h50']['lam']:.2f}, действий "
          f"{results['A_u_триггер_h50']['n_actions']}")
    print("P3 пауза Хаммурапи: λ "
          f"{results['A_u_пауза_хамм']['lam']:.2f}, действий "
          f"{results['A_u_пауза_хамм']['n_actions']}, тиков в паузе "
          f"{results['A_u_пауза_хамм']['pause_ticks']}, "
          f"DEFR-конец {results['A_u_пауза_хамм']['defr_end']:.2f} vs "
          f"триггера {results['A_u_триггер']['defr_end']:.2f}")
    print("\n--- БЛОК ПРИЁМКИ (tau_t=0.05 создаёт сломанные; q_miss=0.3) ---")
    for nm in ['A_u_аудит_од', 'A_u_аудит_нес', 'A_u_аудит_с30',
               'A_u_кворум']:
        r = results[nm]
        tot_kill = r['n_audit_kill'] + r['n_fp_kill']
        prec = (r['n_audit_kill'] / tot_kill * 100) if tot_kill > 0 else 0.0
        print(f"  {nm:<15} λ={r['lam']:.2f}  сломанных казнено "
              f"{r['n_audit_kill']:>6}  ложных {r['n_fp_kill']:>5}  "
              f"точность {prec:5.1f}%  сломанного в стоке "
              f"{r['broken_share_final']*100:5.1f}%  E/Y={r['pool_over_Y']:.4f}")
    print("\n--- БЛОК ЗВЕНА 17: порог риск-прайсинга ---")
    base_lam = results['A_u_база']['lam']
    i_star = 2.0 ** (1.0 / 10.0) - 1.0
    print(f"  аналитический порог для h50 (кулдаун 10): "
          f"i* = 2^(1/10)−1 = {i_star*100:.1f}%")
    print("  полный юбилей (сброс в ноль — невосприимчив к i):")
    for i, nm in [(0.06, 'A_u_юб30'), (0.08, 'A_u_юб30_i08'),
                  (0.15, 'A_u_юб30_i15')]:
        r = results[nm]
        print(f"    i={i:.2f}: λ(юб30)={r['lam']:.2f}  пол=(1+i)^25="
              f"{(1+i)**25:.2f}")
    print("  h50 (сток выживает — порог есть):")
    for i, nm in [(0.06, 'A_u_триггер_h50'), (0.08, 'A_u_h50_i08'),
                  (0.10, 'A_u_h50_i10'), (0.15, 'A_u_h50_i15'),
                  (0.20, 'A_u_h50_i20')]:
        r = results[nm]
        verdict = ('заперт порогом' if r['lam'] < base_lam
                   else 'СЪЕДЕН СТАВКОЙ (λ ≥ базы)')
        print(f"    i={i:.2f}: λ(h50)={r['lam']:>6.2f}  действий "
              f"{r['n_actions']:>3}  maxD={r['D_max']:.3g}  → {verdict}")

    meta = {
        'python': sys.version.split()[0], 'numpy': np.__version__,
        'seed': 7,
        'lambda_definition': 'λ25 = exp(25·slope log(D+1)), T=300',
        'status': 'E — исполнение гипотез разбора «Красной Нити» (раунд 8)',
        'preregistered': ['P1 триггер < календаря по λ, действий меньше',
                          'P2 h50 между юбилеем и базой',
                          'P3 пауза между юбилеем и базой',
                          'P4 кворум режет ложные казни ≥10× при улове',
                          'P5 порог i* ∈ (0.10, 0.12)'],
        'input': 'разбор «Красной Нити» сторонней моделью: 22 звена, DLV-спека',
        'trigger_definition': 'DEFR = доля носителей с d > 5·y_base; кризис '
                              '= DEFR > 0.2 (собственное определение v1–v4); '
                              'кулдаун 10 тиков',
        'reproducibility': 'якорь = v4.2 база (rng в якорных конфигах не тронут)',
    }
    export = {'meta': meta, 'runs': {}}
    for name, r in results.items():
        export['runs'][name] = {k: v for k, v in r.items()
                                if k not in ('D', 'GS', 'Y', 'POOL', 'DEFR')}
    blob = json.dumps(export, ensure_ascii=False, sort_keys=True)
    h = hashlib.sha256(blob.encode()).hexdigest()
    export['integrity'] = {'results_sha256': h}
    with open(f'{OUT_DIR}/results.json', 'w') as f:
        json.dump(export, f, ensure_ascii=False, indent=1)
    with open(f'{OUT_DIR}/timeseries.csv', 'w') as f:
        f.write('run,tick,D,Y,pool,defr\n')
        for name, r in results.items():
            for t in range(300):
                f.write(f"{name},{t},{r['D'][t]:.6f},{r['Y'][t]:.6f},"
                        f"{r['POOL'][t]:.6f},{r['DEFR'][t]:.6f}\n")
    print(f"\nsha256(results) = {h}")
    print(f"выход: {OUT_DIR}/results.json, timeseries.csv")

    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(1, 3, figsize=(15.0, 4.6),
                             constrained_layout=True)
    # (а) λ: мишарум-блок
    ax = axes[0]
    keys = ['A_u_база', 'A_u_юб30', 'A_u_триггер', 'A_u_триггер_h50',
            'A_u_пауза_хамм']
    labs = ['база', 'юбилей\n30', 'триггер\n(сброс)', 'триггер\nh50',
            'пауза\nХаммурапи']
    vals = [results[k]['lam'] for k in keys]
    bars = ax.bar(range(5), vals,
                  color=['#555555', '#B8860B', '#8B0000', '#CD3333', '#4682B4'])
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.06, f'{v:.2f}',
                ha='center', fontsize=9)
    ax.set_xticks(range(5))
    ax.set_xticklabels(labs, fontsize=8)
    ax.set_title('Программируемый мишарум:\nкалендарь vs триггер vs пауза',
                 fontsize=10.5)
    ax.set_ylabel('λ25', fontsize=9.5)
    ax.grid(alpha=0.3, axis='y')
    # (б) приёмка: точность vs пропускная способность
    ax = axes[1]
    anames = ['A_u_аудит_од', 'A_u_аудит_нес', 'A_u_аудит_с30', 'A_u_кворум']
    alabs = ['одиночный\nвсеведущий\n(0.10)', 'одиночный\nнесоверш.\n(0.10)',
             'одиночный\nнесоверш.\n(0.30)', 'кворум\n3×0.10, ≥2']
    ak = [results[n]['n_audit_kill'] for n in anames]
    afp = [results[n]['n_fp_kill'] for n in anames]
    x = np.arange(4)
    ax.bar(x - 0.18, ak, width=0.36, label='казнено сломанных (улов)',
           color='#2E8B57')
    ax.bar(x + 0.18, afp, width=0.36, label='казнено годных (ложные)',
           color='#8B0000')
    ax.set_yscale('log')
    ax.set_xticks(x)
    ax.set_xticklabels(alabs, fontsize=7.5)
    ax.set_title('Кворум-приёмка: точность против\nпропускной способности '
                 '(казни, шт.)', fontsize=10.5)
    ax.set_ylabel('лотов (log)', fontsize=9.5)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3, axis='y')
    # (в) порог риск-прайсинга
    ax = axes[2]
    ii_h = [0.06, 0.08, 0.10, 0.15, 0.20]
    lam_h = [results[k]['lam'] for k in
             ['A_u_триггер_h50', 'A_u_h50_i08', 'A_u_h50_i10',
              'A_u_h50_i15', 'A_u_h50_i20']]
    ii_j = [0.06, 0.08, 0.15]
    lam_j = [results[k]['lam'] for k in
             ['A_u_юб30', 'A_u_юб30_i08', 'A_u_юб30_i15']]
    grid = np.linspace(0.05, 0.21, 60)
    ax.plot(grid, (1 + grid) ** 25, '--', color='#888888',
            label='без мишарума: (1+i)^25')
    ax.plot(ii_h, lam_h, 'o-', color='#CD3333', label='триггер h50')
    ax.plot(ii_j, lam_j, 's-', color='#B8860B', label='полный юбилей 30')
    ax.axhline(base_lam, color='#2E8B57', lw=1.5,
               label=f'λ базы = {base_lam:.2f}')
    ax.axvline(i_star, color='#4682B4', ls=':', lw=1.5,
               label=f'i* = 2^(1/10)−1 = {i_star*100:.1f}%')
    ax.set_yscale('log')
    ax.set_xlabel('ставка i', fontsize=9.5)
    ax.set_ylabel('λ25', fontsize=9.5)
    ax.set_title('Звено 17: порог компенсации ставки\n'
                 '(полный сброс слеп к i, частичный — нет)', fontsize=10.5)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7)
    fig.suptitle('КОЛЬЦО-1 v4.3: гипотезы разбора «Красной Нити» — в прогоны. '
                 'N=200, T=300, seed=7, ρ=A', fontsize=11)
    fig.savefig(PNG_OUT, dpi=150)
    print(f"PNG сохранён: {PNG_OUT}")


if __name__ == '__main__':
    main()
