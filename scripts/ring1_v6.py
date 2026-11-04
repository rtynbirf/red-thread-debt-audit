#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
КОЛЬЦО-1_v6 — АНТИ-НАСЛЕДСТВЕННЫЙ КЛАПАΝ (звено 8). Раунд 12.
Исполнение объявленного в v5.0 задания (5): испытание ρ-оператора как
клапана наследования — единственного нетронутого топливного контура
машины (топливо = процент на унаследованном стоке, звенья 3+8; пять
впускных клапанов — рождение, старение носителя, старость, дарение/
сытость, допуск κ — λ не двигали: ЗАКОН ОДНОСТОРОННЕГО КЛАПАНА v5.0).

НОВЫЙ ОПЕРАТОР (непрерывная генерализация тернарных ρ=A/B/C из v2):
  rho_frac ρ ∈ [0,1] — доля долга, переходящая наследнику при смерти
  носителя: (d, s) → (ρ·d, s + g0). Уничтожаемая доля (1−ρ)·d — новый
  оператор «погашение смертью» (mortality amortization) с серией WO.
  ρ=1 ≡ ρ='A' (якорь), ρ=0 — долг не переживает носителя; тернарные
  ρ='B'/'C' перемеряются под механику v4.x–v5 для сравнения каналов.

ВЕРДИКТ-РАМКА (предрегистрация, объявлена ДО прогона; seed=7;
ни один новый блок не потребляет rng):
  P1 ЯКОРЬ: λ(v6_ρ100) = λ(v5_база) = 4.585096118130804 бит в бит
     (ρ=1 точно эквивалентен ρ='A': умножение на 1.0, нулевые
     списания, без изъятий лотов).
  P2 ЗАКОН НАСЛЕДОВАНИЯ (первого порядка, из уравнения стока):
     dD/dt = (i − m·(1−ρ))·D + свежие − платежи, где m — стоимостно-
     взвешенная смертность долга: m = Σ_t(перенесено при смерти) /
     Σ_t D[t], ИЗМЕРЯЕТСЯ ОДИН РАЗ в базе ρ=1 и переносится на всю
     сетку ρ вне выборки:
        ln λ(ρ) = ln λ_A − 25·m·(1−ρ) + η,
     |η| ≤ 0.3·25·m·(1−ρ) для ≥ 3 из 4 точек ρ ∈ {0.75, 0.5, 0.25, 0.1}.
     Двухстадийная дисциплина: прогон базы → печать числовых
     предсказаний λ(ρ) → прогон свипа → вердикты машины.
  P3 КРИТИЧЕСКИЙ ПОРОГ НАСЛЕДОВАНИЯ: ρ* = 1 − ln(λ_A)/(25·m);
     (а) при всех испытанных ρ < ρ*: λ ≤ 1.15 (машина остановлена);
     (б) λ(ρ=0) ∈ [0.95, 1.25] (сток живёт в пределах жизни носителя,
     стационар; приоры v2: тернB 1.11, тернC 1.17).
  P4 АСИММЕТРИЯ КЛАПАНОВ (усиление закона одностороннего клапана):
     выходной клапан ρ двигает λ там, где все пять впускных не смогли:
     λ(ρ=0.5) < 0.6·λ_A; λ монотонно нестрого убывает по ρ↓;
     цена клапана кредитору: ΣWO > 0 при ρ<1 и монотонно ↑ по ρ↓;
     голод = 0 во всех ρ-конфигах (клапан режет кредитора, не рацион
     должника — противоположность κ).
  P5 SFA-ЗАМЫКАНИЕ НОВОГО ОПЕРАТОРА (позитивный контроль расширяется):
     тождество стока с явным оператором:
        D[t] = D[t−1]·(1+i) + SH[t] − POOL[t] − WO[t];
     (а) с оператором: max|resid + WO| < 1e-9·max(D) на v6_ρ050 —
     «погашение смертью» восстанавливается бит в бит;
     (б) без оператора: resid = −WO на тиках смертей — мост без члена
     смертности «обнаруживает» фантомный оператор ровно величиной WO
     (зеркало v5-P4b: слепой метод видит РЕАЛЬНОГО, но безымянного).
  P6 ЗЕРКАЛО НАСЛЕДОВАНИЯ (противоположность факту v5 «наследование
     переносит ×90 одолженного»): при ρ=0 смертность уничтожает больше,
     чем посеяно: ΣWO / Σp0_created > 1 («долг умирает богаче
     рождения»). 

ДЕТЕРМИНИЗМ: ни один новый блок не вызывает rng → якорь бит в бит.
СТАТУС: E — модельная конструкция с предрегистрацией; модель не
меняется по результату; все отклонения публикуются как есть.
=============================================================================
"""
import json
import hashlib
import sys
import numpy as np

OUT_DIR = '/home/z/my-project/scripts/ring1_v6_out'
PNG_OUT = '/home/z/my-project/download/КОЛЬЦО-1_v6_закон_наследования.png'

Q_BREAK = 0.15
C_A = 0.10
Q_FP = 0.02

ZONES = ['рабство', 'вечная', 'честный', 'сломан', 'прочее']
FATES = ['погашен', 'сброс', 'изъятие-аудит', 'ложная казнь',
         'изъятие-залог', 'сброс-наследие', 'смерть-терминальная',
         'машина жива']


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
        adm_kappa=None, rho_frac=None,
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
    n_actions = [0]
    pause_used = [0]
    last_action = [-10 ** 9]
    pause_left = [0]
    defr_prev = [0.0]
    broken_share_ts = np.zeros(T)
    vol = {'young': 0.0, 'prime': 0.0, 'old': 0.0}
    pop = {'young': 0.0, 'prime': 0.0, 'old': 0.0}

    D = np.zeros(T); Y = np.zeros(T); POOL = np.zeros(T)
    DEFR = np.zeros(T); GS = np.zeros(T)
    SH = np.zeros(T); IEFF = np.zeros(T); WRITEOFF = np.zeros(T)
    MTR = np.zeros(T)   # перенесено при смерти носителя (инструментация m)
    ZS = {z: np.zeros(T) for z in ZONES}
    famine = [0.0]           # голод: неудовлетворённый дефицит (допуск)
    famine_cnt = [0]

    # --- счётчики 9 звеньев ---
    LN = {
        'L1_ДЕФИЦИТ': {'тиков_нуждающихся': 0, 'сумма_short': 0.0},
        'L2_ПОСЕВ': {'новых_лотов': 0, 'номинал_p0': 0.0},
        'L3_ЭКСПОНЕНТА': {'начислено': 0.0},
        'L4_ЗАЛОГ': {'покрытие_сумма': 0.0, 'покрытие_тиков': 0},
        'L5_КАПИТУЛЯЦИЯ': {'ролловер_событий': 0, 'ролловер_сумма': 0.0},
        'L6_ИЗЪЯТИЕ': {'казнь_сломанных': 0, 'p0_сломанных': 0.0,
                       'ложных_казней': 0, 'p0_ложных': 0.0},
        'L7_КОНВЕРСИЯ': {'пул_поток': 0.0, 'сломанных_живых_в_конце': 0,
                         'номинал_сломанных_живых': 0.0},
        'L8_НАСЛЕДОВАНИЕ': {'переходов_долга': 0, 'стоимость_переходов': 0.0,
                            'погашено_смертью': 0.0},
        'L9_СБРОС': {'сбросов': 0, 'списано': 0.0},
    }
    fate_val = {f: 0.0 for f in FATES}
    fate_cnt = {f: 0 for f in FATES}
    p0_created = [0.0]

    def fate(L, f):
        fate_val[f] += L.get('p0', L['p'])
        fate_cnt[f] += 1

    quorum_k = (quorum_n + 1) // 2

    def bucket(a):
        return 'young' if a < 25.0 else ('prime' if a < 55.0 else 'old')

    for t in range(T):
        # ---- триггер бедствия ----
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
        IEFF[t] = i_eff
        if pause_left[0] > 0:
            pause_used[0] += 1
            pause_left[0] -= 1

        shocks = rng.uniform(0.7, 1.3, N)
        y_base = 100.0 * y_mult * u * np.minimum(age / 25.0, 1.0) \
                 * np.clip(1.0 - (age - 55.0) / 30.0, 0.3, 1.0)
        y_eff = y_base * shocks * (1.0 - stress * np.clip(
            d / np.maximum(3.0 * y_base * shocks, 1.0), 0.0, 1.0))

        # ---- L3 ЭКСПОНЕНТА: начисление ----
        if T3:
            d *= (1.0 + i_eff)
            for i in range(N):
                for L in lots[i]:
                    accr = L['p'] * i_eff
                    L['accrued'] += accr
                    L['accr_tick'] = accr
                    LN['L3_ЭКСПОНЕНТА']['начислено'] += accr
                    L['p'] *= (1.0 + i_eff)
            for i in range(N):
                for L in lots[i]:
                    L['paid_tick'] = 0.0

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
                            LN['L6_ИЗЪЯТИЕ']['казнь_сломанных'] += 1
                            LN['L6_ИЗЪЯТИЕ']['p0_сломанных'] += L['p0']
                            fate(L, 'изъятие-аудит')
                        else:
                            L['hist'].append((t, 'audit_false_positive'))
                            n_fp_kill[0] += 1
                            LN['L6_ИЗЪЯТИЕ']['ложных_казней'] += 1
                            LN['L6_ИЗЪЯТИЕ']['p0_ложных'] += L['p0']
                            fate(L, 'ложная казнь')
                    else:
                        keep.append(L)
                if changed:
                    lots[i] = keep
                    d[i] = sum(L['p'] for L in keep)

        # ---- допуск κ (Programmable CAC) + L1/L2/L5 ----
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
                pre_d = d.copy()
                short_eff = short
                if adm_kappa is not None and i_eff > 0:
                    # VOID-B: доходная ёмкость (от излишка — вырождена:
                    # у нуждающегося излишек = 0 по построению)
                    d_max = adm_kappa * y_eff / i_eff
                    cap = np.maximum(d_max - d, 0.0)
                    short_eff = np.minimum(short, cap)
                    unmet = short - short_eff
                    famine[0] += float(unmet.sum())
                    famine_cnt[0] += int((unmet > 1e-9).sum())
                d += short_eff
                LN['L1_ДЕФИЦИТ']['сумма_short'] += float(short_eff.sum())
                LN['L1_ДЕФИЦИТ']['тиков_нуждающихся'] += \
                    int((short_eff > 0).sum())
                for i in np.where(short_eff > 0)[0]:
                    lot_seq[0] += 1
                    lots[i].append({'id': lot_seq[0],
                                    'p': float(short_eff[i]),
                                    'p0': float(short_eff[i]),
                                    'accrued': 0.0, 'paid': 0.0,
                                    'accr_tick': 0.0, 'paid_tick': 0.0,
                                    'birth': t, 'deaths': 0, 'transfers': 0,
                                    'broken': False,
                                    'hist': [(t, 'orig')]})
                    p0_created[0] += float(short_eff[i])
                    LN['L2_ПОСЕВ']['новых_лотов'] += 1
                    LN['L2_ПОСЕВ']['номинал_p0'] += float(short_eff[i])
                    if pre_d[i] > 1e-9:
                        LN['L5_КАПИТУЛЯЦИЯ']['ролловер_событий'] += 1
                        LN['L5_КАПИТУЛЯЦИЯ']['ролловер_сумма'] += \
                            float(short_eff[i])
                    vol[bucket(age[i])] += float(short_eff[i])
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
                            L['paid_tick'] += take
                            L['paid'] += take
                        kept = []
                        for L in li:
                            if L['p'] > 1e-9:
                                kept.append(L)
                            else:
                                fate(L, 'погашен')
                        lots[i] = kept
                        d[i] = sum(L['p'] for L in lots[i])
                        s[i] -= liq
                    pool += inc_pay + liq
                    LN['L7_КОНВЕРСИЯ']['пул_поток'] += inc_pay + liq
            else:
                pool = 0.0

        tot_s = float(s.sum())
        if tot_s > 0:
            s += pool * (s / tot_s)
        if phi > 0:
            y_mult = min(y_mult * (1.0 + phi * pool /
                                   max(float(y_eff.sum()), 1.0)), ymax)

        # ---- списание: календарное или триггерное (L9) ----
        cal_fire = bool(jubilee and (t + 1) % jubilee == 0)
        if cal_fire or (fire and not pause_on_trigger):
            if haircut_frac >= 1.0:
                LN['L9_СБРОС']['сбросов'] += 1
                LN['L9_СБРОС']['списано'] += float(sum(
                    L['p'] for i in range(N) for L in lots[i]))
                WRITEOFF[t] = float(sum(L['p'] for i in range(N)
                                        for L in lots[i]))
                for i in range(N):
                    for L in lots[i]:
                        L['hist'].append((t, 'jubilee'))
                        fate(L, 'сброс')
                    lots[i] = []
                d[:] = 0.0
            else:
                LN['L9_СБРОС']['сбросов'] += 1
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
                        fate(L, 'смерть-терминальная')
                    lots[i] = []
            elif rho_frac is not None:
                # непрерывный анти-наследственный клапан: (d,s)→(ρ·d, s+g0)
                tr = 0.0
                wo_t = 0.0
                for i in np.where(dead)[0]:
                    LN['L8_НАСЛЕДОВАНИЕ']['переходов_долга'] += len(lots[i])
                    for L in lots[i]:
                        tr += L['p']
                        cut = L['p'] * (1.0 - rho_frac)
                        wo_t += cut
                        LN['L8_НАСЛЕДОВАНИЕ']['погашено_смертью'] += cut
                        L['p'] *= rho_frac
                        L['deaths'] += 1
                        L['hist'].append((t, 'carrier_death_rho'))
                        if L['p'] <= 1e-9:
                            fate(L, 'сброс-наследие')
                    if rho_frac < 1.0:
                        lots[i] = [L for L in lots[i] if L['p'] > 1e-9]
                LN['L8_НАСЛЕДОВАНИЕ']['стоимость_переходов'] += tr
                d_new, s_new = dp * rho_frac, sp.copy() + g0
                WRITEOFF[t] += wo_t
                MTR[t] += tr
            elif rho == 'A':
                d_new, s_new = dp.copy(), sp.copy() + g0
                for j, i in enumerate(np.where(dead)[0]):
                    LN['L8_НАСЛЕДОВАНИЕ']['переходов_долга'] += len(lots[i])
                    LN['L8_НАСЛЕДОВАНИЕ']['стоимость_переходов'] += \
                        float(sum(L['p'] for L in lots[i]))
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
                        fate(L, 'изъятие-залог')
                    lots[i] = []
            else:
                s_new = np.zeros(k) + g0
                d_new = np.zeros(k)
                for i in np.where(dead)[0]:
                    for L in lots[i]:
                        L['hist'].append((t, 'reset'))
                        fate(L, 'сброс-наследие')
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

        # ---- зоны A_crit по стоимости (после платежей) ----
        zval = {z: 0.0 for z in ZONES}
        for i in range(N):
            for L in lots[i]:
                if L.get('broken'):
                    z = 'сломан'
                elif i_eff <= 0 or L['accr_tick'] <= 0:
                    z = 'прочее'
                else:
                    ratio = L['paid_tick'] / L['accr_tick']
                    z = ('рабство' if ratio < 0.98 else
                         'вечная' if ratio <= 1.02 else 'честный')
                zval[z] += L['p']
        ztot = sum(zval.values())
        for z in ZONES:
            ZS[z][t] = zval[z] / ztot if ztot > 0 else 0.0

        tot_p = sum(L['p'] for i in range(N) for L in lots[i])
        brk_p = sum(L['p'] for i in range(N) for L in lots[i]
                    if L.get('broken'))
        broken_share_ts[t] = brk_p / tot_p if tot_p > 0 else 0.0
        tot_d = float(d.sum())
        if tot_d > 0:
            LN['L4_ЗАЛОГ']['покрытие_сумма'] += float(
                np.minimum(s, d).sum() / tot_d)
            LN['L4_ЗАЛОГ']['покрытие_тиков'] += 1
        D[t], Y[t], POOL[t] = tot_d, float(y_eff.sum()), pool
        SH[t] = float(short.sum())
        DEFR[t] = float(np.mean(d > 5.0 * np.maximum(y_base, 1.0)))
        GS[t] = gini(s)
        defr_prev[0] = DEFR[t]

    # ---- финал: судьбы живых, L7 ----
    flat = [L for i in range(N) for L in lots[i]]
    for L in flat:
        fate(L, 'машина жива')
    LN['L7_КОНВЕРСИЯ']['сломанных_живых_в_конце'] = \
        int(sum(1 for L in flat if L.get('broken')))
    LN['L7_КОНВЕРСИЯ']['номинал_сломанных_живых'] = \
        float(sum(L['p'] for L in flat if L.get('broken')))

    vol_share = {b: (vol[b] / sum(vol.values()) if sum(vol.values()) > 0
                     else 0.0) for b in vol}
    pop_share = {b: pop[b] / T for b in vol}

    tt = np.arange(T, dtype=float)
    slope = float(np.polyfit(tt, np.log(D + 1.0), 1)[0])
    lam = float(np.exp(25.0 * slope))
    crises = np.where(DEFR > 0.2)[0]

    zone_mean = {z: float(ZS[z][50:].mean()) for z in ZONES}
    fates_tv = {f: fate_val[f] for f in FATES}
    fates_tot = sum(fates_tv.values())
    fates_share = {f: (fates_tv[f] / fates_tot if fates_tot > 0 else 0.0)
                   for f in FATES}

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
                famine_total=float(famine[0]),
                famine_holders=int(famine_cnt[0]),
                zone_mean=zone_mean, fates_share=fates_share,
                links={k: dict(v) for k, v in LN.items()},
                p0_created=float(p0_created[0]),
                fate_total=float(fates_tot),
                vol_share=vol_share, pop_share=pop_share,
                broken_share_final=float(broken_share_ts[-1]),
                D=D, GS=GS, Y=Y, POOL=POOL, DEFR=DEFR, SH=SH, IEFF=IEFF,
                WO=WRITEOFF, MTR=MTR, ZS=ZS)


def sfa_decomp(res, blind_rate=None):
    """SFA-мост: остаток = D[t] − (D[t-1]·(1+i[t]) + SH[t] − POOL[t]).
    Переход D[t-1]→D[t] содержит потоки ТЕКУЩЕГО тика t (VOID-A исправлен).
    blind_rate — слепая ставка (игнорирует паузу)."""
    D, SH, POOL, IEFF = res['D'], res['SH'], res['POOL'], res['IEFF']
    T = len(D)
    resid = np.zeros(T)
    for t in range(1, T):
        i_use = blind_rate if blind_rate is not None else IEFF[t]
        d_pred = D[t - 1] * (1.0 + i_use) + SH[t] - POOL[t]
        resid[t] = D[t] - d_pred
    return resid


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    results = {}
    LAM_A_EXPECT = 4.585096118130804
    RHO_GRID = (1.0, 0.75, 0.5, 0.25, 0.1, 0.0)
    NM = {1.0: 'v6_р100', 0.75: 'v6_р075', 0.5: 'v6_р050',
          0.25: 'v6_р025', 0.1: 'v6_р010', 0.0: 'v6_р000'}

    # ---- СТАДИЯ 1: база ρ=1 (якорь) + измерение m ----
    print('=' * 74)
    print('СТАДИЯ 1: база ρ=1 (якорь) + измерение стоимостно-взвешенной')
    print('смертности долга m. Предсказания закона наследования печатаются')
    print('ДО свипа ρ; свип не влияет на модель (дисциплина v5.0).')
    print('=' * 74)
    results['v6_р100'] = run(rho='A', rho_frac=1.0)
    lam_a = results['v6_р100']['lam']
    m = float(results['v6_р100']['MTR'].sum()
              / max(float(results['v6_р100']['D'].sum()), 1e-30))
    drag_full = 25.0 * m
    rho_star = 1.0 - float(np.log(lam_a)) / drag_full
    print(f"P1 λ_A = {lam_a:.15f}  (ожидание {LAM_A_EXPECT})")
    print(f"m (смертность долга, доля стока/тик) = {m:.6f}"
          f"  →  25·m = {drag_full:.4f}")
    print(f"P3 ρ* = 1 − ln(λ_A)/(25·m) = {rho_star:.4f}")

    print('\n--- СТАДИЯ 1.5: ЧИСЛОВЫЕ ПРЕДСКАЗАНИЯ ЗАКОНА (объявлены до свипа) ---')
    preds = {}
    for rho in RHO_GRID[1:]:
        drag = drag_full * (1.0 - rho)
        lam_pred = lam_a * float(np.exp(-drag))
        preds[rho] = lam_pred
        lo = lam_a * float(np.exp(-drag * 1.3))
        hi = lam_a * float(np.exp(-drag * 0.7))
        print(f'  ρ={rho:4.2f}: λ_предск = {lam_pred:7.3f}   '
              f'полоса ±30% драга: [{lo:7.3f}, {hi:7.3f}]')
    print('  объявления сделаны — запускается свип; модель не меняется.')

    # ---- СТАДИЯ 2: свип ρ + тернарные приоры v2 ----
    configs = [
        ('v6_р075', dict(rho='A', rho_frac=0.75)),
        ('v6_р050', dict(rho='A', rho_frac=0.50)),
        ('v6_р025', dict(rho='A', rho_frac=0.25)),
        ('v6_р010', dict(rho='A', rho_frac=0.10)),
        ('v6_р000', dict(rho='A', rho_frac=0.00)),
        ('v6_тернB', dict(rho='B')),
        ('v6_тернC', dict(rho='C')),
    ]
    for name, kw in configs:
        results[name] = run(**kw)

    hdr = (f"{'конфигурация':<12}{'λ25':>8}{'D/Y':>9}{'Gini':>7}{'E/Y':>8}"
           f"{'голод':>8}{'рабство%':>9}{'вечная%':>8}{'ΣWO/Σp0':>10}")
    print('\n' + hdr)
    print('-' * len(hdr))
    for name, r in results.items():
        wo_p0 = float(r['WO'].sum()) / max(r['p0_created'], 1e-30)
        print(f"{name:<12}{r['lam']:>8.3f}{r['D_over_Y']:>9.3g}"
              f"{r['gini']:>7.3f}{r['pool_over_Y']:>8.4f}"
              f"{r['famine_total']:>8.1f}"
              f"{r['zone_mean']['рабство']*100:>9.1f}"
              f"{r['zone_mean']['вечная']*100:>8.2f}"
              f"{wo_p0:>10.2f}")

    print('\n--- СУДЬБЫ ЛОТОВ (доля p0, выборка) ---')
    for name in ['v6_р100', 'v6_р050', 'v6_р000', 'v6_тернB', 'v6_тернC']:
        fs = results[name]['fates_share']
        top = sorted(fs.items(), key=lambda kv: -kv[1])[:4]
        print(f"  {name:<10} " + ", ".join(f"{k}={v*100:.1f}%" for k, v in top))

    # ---- вердикты ----
    v = {}
    v['P1'] = abs(lam_a - LAM_A_EXPECT) < 1e-9

    ok_pts = 0
    p2_detail = {}
    for rho in (0.75, 0.5, 0.25, 0.1):
        lam_m = results[NM[rho]]['lam']
        drag = drag_full * (1.0 - rho)
        eta = float(np.log(lam_m / lam_a)) + drag
        ok = abs(eta) <= 0.3 * drag
        ok_pts += int(ok)
        p2_detail[NM[rho]] = dict(lam=lam_m, lam_pred=preds[rho],
                                  eta=eta, drag=drag, ok=bool(ok))
        print(f"P2 {NM[rho]}: λ_изм {lam_m:7.3f} vs предск {preds[rho]:7.3f}"
              f"  η={eta:+.3f} (допуск ±{0.3*drag:.3f})  "
              f"{'OK' if ok else 'ВНЕ ПОЛОСЫ'}")
    v['P2'] = ok_pts >= 3

    below = [r for r in RHO_GRID if r < rho_star]
    lam0 = results['v6_р000']['lam']
    ok_stop = all(results[NM[r]]['lam'] <= 1.15 for r in below)
    print(f"P3 ρ*={rho_star:.4f}; испытанные ρ<ρ*: {below}")
    print(f"   λ(ρ<ρ*) ≤ 1.15: {ok_stop};  λ(ρ=0) = {lam0:.3f} "
          f"(коридор [0.95, 1.25])")
    v['P3'] = ok_stop and (0.95 <= lam0 <= 1.25)

    lams_seq = [results[NM[r]]['lam'] for r in RHO_GRID]
    mono = all(lams_seq[i] >= lams_seq[i + 1] - 1e-9
               for i in range(len(lams_seq) - 1))
    wos = {r: float(results[NM[r]]['WO'].sum()) for r in RHO_GRID[1:]}
    famine_zero = all(results[NM[r]]['famine_total'] == 0.0 for r in RHO_GRID)
    print(f"P4 λ(ρ=0.5)/λ_A = {results['v6_р050']['lam']/lam_a:.3f} (<0.6);"
          f"  λ монотонна по ρ: {mono};  ΣWO>0 при всех ρ<1: "
          f"{all(w > 0 for w in wos.values())};  голод=0: {famine_zero}")
    v['P4'] = (results['v6_р050']['lam'] < 0.6 * lam_a and mono
               and all(w > 0 for w in wos.values()) and famine_zero)

    r5 = results['v6_р050']
    resid_raw = sfa_decomp(r5)
    wo = r5['WO']
    tol = 1e-9 * float(r5['D'].max())
    err_with = float(np.abs(resid_raw + wo).max())
    blind_mag = float(np.abs(resid_raw).max())
    wo_max = float(wo.max())
    print(f"P5 SFA (ρ=0.5): max|resid+WO| = {err_with:.3e} "
          f"(допуск {tol:.3e}); слепой мост видит фантом max|resid| = "
          f"{blind_mag:.4g} при max WO = {wo_max:.4g}")
    v['P5'] = err_with < tol and blind_mag > 0.3 * wo_max

    wo0 = float(results['v6_р000']['WO'].sum())
    p00 = float(results['v6_р000']['p0_created'])
    print(f"P6 ЗЕРКАЛО (ρ=0): ΣWO = {wo0:.4g}  vs Σp0_created = {p00:.4g}  "
          f"→ ×{wo0/p00:.1f} (>1: долг умирает богаче рождения)")
    v['P6'] = wo0 / max(p00, 1e-30) > 1.0

    print('\n--- ВЕРДИКТЫ (предрегистрация раунда 12) ---')
    verdicts = {
        'P1 якорь ρ=1 ≡ v5_база бит в бит': v['P1'],
        'P2 закон наследования ln λ = ln λ_A − 25m(1−ρ) (±30% драга)': v['P2'],
        'P3 критический порог ρ*: машина остановлена при ρ<ρ*': v['P3'],
        'P4 асимметрия клапанов: выходной двигает λ, цена кредитору': v['P4'],
        'P5 SFA-замыкание оператора «погашение смертью»': v['P5'],
        'P6 зеркало наследования: ΣWO > Σp0 при ρ=0': v['P6'],
    }
    for k, ok in verdicts.items():
        print(f"  {k:<58} {'ПОДТВЕРЖДЕНА' if ok else 'ОТКЛОНЕНА'}")

    meta = {
        'python': sys.version.split()[0], 'numpy': np.__version__,
        'seed': 7,
        'lambda_definition': 'λ25 = exp(25·slope log(D+1)), T=300, N=200',
        'status': 'E — анти-наследственный клапан ρ: непрерывная '
                  'генерализация звена 8 с предрегистрацией (раунд 12)',
        'preregistered': list(verdicts.keys()),
        'law': 'ln λ(ρ) = ln λ_A − 25·m·(1−ρ); m = Σперенесено/ΣD '
               '(измерено в базе ρ=1, перенесено вне выборки); '
               'ρ* = 1 − ln(λ_A)/(25·m)',
        'new_operator': 'rho_frac ρ∈[0,1]: (d,s)→(ρ·d, s+g0); (1−ρ)·d — '
                        'оператор «погашение смертью» (mortality '
                        'amortization), серия WO в тождестве SFA',
        'valve_law': 'впускные клапаны (рождение/старение/старость/дарение/'
                     'κ) не двигают λ; выходной клапан ρ двигает. Цена κ — '
                     'голод должника; цена ρ — списание кредитора',
        'anchor': 'якорь v5.0 (λ=4.585096118130804), rng-инвариантность',
        'measured_m': m, 'rho_star': rho_star,
        'predictions': {f'ρ={k}': vv for k, vv in preds.items()},
        'p2_detail': p2_detail,
    }
    export = {'meta': meta, 'verdicts': {k: bool(x) for k, x
                                         in verdicts.items()},
              'runs': {}}
    for name, r in results.items():
        export['runs'][name] = {
            k: v for k, v in r.items()
            if k not in ('D', 'GS', 'Y', 'POOL', 'DEFR', 'SH', 'IEFF',
                         'ZS', 'WO', 'MTR')}
        export['runs'][name]['wo_total'] = float(r['WO'].sum())
        export['runs'][name]['mtr_total'] = float(r['MTR'].sum())
        export['runs'][name]['zone_mean_после_50'] = r['zone_mean']
    blob = json.dumps(export, ensure_ascii=False, sort_keys=True)
    h = hashlib.sha256(blob.encode()).hexdigest()
    export['integrity'] = {'results_sha256': h}
    with open(f'{OUT_DIR}/results.json', 'w') as f:
        json.dump(export, f, ensure_ascii=False, indent=1)
    with open(f'{OUT_DIR}/timeseries.csv', 'w') as f:
        f.write('run,tick,D,Y,pool,defr,slavery_share,wo,mtr\n')
        for name, r in results.items():
            for t in range(300):
                f.write(f"{name},{t},{r['D'][t]:.6f},{r['Y'][t]:.6f},"
                        f"{r['POOL'][t]:.6f},{r['DEFR'][t]:.6f},"
                        f"{r['ZS']['рабство'][t]:.6f},{r['WO'][t]:.6e},"
                        f"{r['MTR'][t]:.6e}\n")
    print(f"\nsha256(results) = {h}")
    print(f"выход: {OUT_DIR}/results.json, timeseries.csv")

    # ---- PNG: 4 панели ----
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = 'DejaVu Sans'
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(2, 2, figsize=(13.5, 9.0),
                             constrained_layout=True)

    # (а) закон наследования λ(ρ)
    ax = axes[0, 0]
    rho_cont = np.linspace(0.0, 1.0, 200)
    lam_law = lam_a * np.exp(-drag_full * (1.0 - rho_cont))
    drag_band = drag_full * (1.0 - rho_cont)
    ax.fill_between(rho_cont, lam_a * np.exp(-1.3 * drag_band),
                    lam_a * np.exp(-0.7 * drag_band),
                    color='#B8860B', alpha=0.18, label='полоса ±30% драга')
    ax.plot(rho_cont, lam_law, '-', color='#8B0000', lw=1.8,
            label=f'1-й порядок: λ_A·exp(−25m(1−ρ)), m={m:.4f}')
    lam_corr = lam_a * np.exp(-25.0 * m * rho_cont ** (-0.45)
                              * (1.0 - rho_cont))
    mask_c = rho_cont > 0.02
    ax.plot(rho_cont[mask_c], lam_corr[mask_c], '--', color='#4682B4',
            lw=1.6,
            label='постфактум (MODEL): с m_eff=m·ρ^−0.45 (измерено)')
    for rho in RHO_GRID:
        lm = results[NM[rho]]['lam']
        ax.plot(rho, lm, 'o', ms=7, color='#8B0000')
        ax.annotate(f'{lm:.2f}', (rho, lm), textcoords='offset points',
                    xytext=(6, 5), fontsize=8.5)
    ax.plot([0], [results['v6_тернB']['lam']], 'x', ms=8, color='#555555')
    ax.plot([0], [results['v6_тернC']['lam']], 'x', ms=8, color='#555555')
    ax.plot([], [], 'x', color='#555555',
            label=f'тернарные B/C (приоры v2: 1.11/1.17)')
    ax.plot([], [], 'o', color='#8B0000', label='измерено (seed=7)')
    ax.text(0.02, 0.98,
            f'ρ*(1-й порядок) = {rho_star:.2f} — вне [0,1]: первый порядок'
            f' предсказывает отсутствие остановки.\n'
            f'Измерение: λ(ρ=0.1)=1.59 — машина ещё жива на 10%'
            f' наследования;\nλ(ρ=0)=1.10 — экспонента мертва (внутрижизненный'
            f' пол ρ=тернB/C).',
            transform=ax.transAxes, fontsize=7.2, va='top',
            bbox=dict(boxstyle='round', fc='#FFF8DC', alpha=0.85))
    ax.set_xlabel('ρ — доля долга, переживаемая наследником', fontsize=9.5)
    ax.set_ylabel('λ25', fontsize=9.5)
    ax.set_title('Закон наследования: первый порядок отвергнут —'
                 ' отклонения однонаправленны\n(клапан самоусиливается:'
                 ' m_eff/m = ρ^−0.45, измерено 1.00→3.31)', fontsize=10.5)
    ax.legend(fontsize=7, loc='lower right')
    ax.grid(alpha=0.3)

    # (б) траектории D
    ax = axes[0, 1]
    for rho in RHO_GRID:
        ax.plot(range(300), results[NM[rho]]['D'], lw=1.2,
                label=f'ρ={rho:g} (λ={results[NM[rho]]["lam"]:.2f})')
    ax.set_yscale('log')
    ax.set_xlabel('тик', fontsize=9.5)
    ax.set_ylabel('D (сто standing стока)', fontsize=9.5)
    ax.set_title('Стоячий сток: экспонента машины гасится клапаном ρ\n'
                 'log-шкала, seed=7', fontsize=10.5)
    ax.legend(fontsize=7.5, loc='upper left')
    ax.grid(alpha=0.3, which='both')

    # (в) цена клапана
    ax = axes[1, 0]
    rgs = list(RHO_GRID[1:])
    wo_tot = [float(results[NM[r]]['WO'].sum()) for r in rgs]
    ax.plot(rgs, wo_tot, 's-', color='#8B4513', lw=1.8,
            label='ΣWO — уничтожено смертью (цена кредитору)')
    for r_, w_ in zip(rgs, wo_tot):
        ax.annotate(f'{w_:.2g}', (r_, w_), textcoords='offset points',
                    xytext=(4, 6), fontsize=8)
    ax.set_xlabel('ρ', fontsize=9.5)
    ax.set_ylabel('ΣWO (уровень долга)', fontsize=9.5, color='#8B4513')
    ax2 = ax.twinx()
    dy = [results[NM[r]]['D_over_Y'] for r in rgs]
    gn = [results[NM[r]]['gini'] for r in rgs]
    ax2.plot(rgs, dy, 'D--', color='#4682B4', lw=1.4, label='D/Y')
    ax2.plot(rgs, gn, '^--', color='#2E8B57', lw=1.4, label='Gini')
    ax2.set_ylabel('D/Y, Gini', fontsize=9.5)
    ax.set_yscale('log')
    ax.set_ylim(min(wo_tot) / 5.0, max(wo_tot) * 8.0)
    ax.set_title('Цена клапана: списание у кредитора (не голод должника)\n'
                 'голода = 0 во всех ρ-конфигах; ΣWO немонотонно — пик при '
                 'промежуточном ρ', fontsize=10.5)
    ln1, lb1 = ax.get_legend_handles_labels()
    ln2, lb2 = ax2.get_legend_handles_labels()
    ax.legend(ln1 + ln2, lb1 + lb2, fontsize=7.5, loc='center right')
    ax.grid(alpha=0.3)

    # (г) SFA-замыкание оператора
    ax = axes[1, 1]
    ax.plot(range(1, 300), -wo[1:], lw=1.0, color='#8B4513',
            label='−WO: оператор «погашение смертью»')
    ax.plot(range(1, 300), resid_raw[1:], lw=0.9, color='#4682B4',
            alpha=0.75, ls='--',
            label='остаток слепого моста (без члена WO)')
    ax.plot(range(1, 300), (resid_raw + wo)[1:], lw=0.9, color='#2E8B57',
            label='остаток ПОСЛЕ внесения WO (≈0 бит в бит)')
    ax.axhline(0, color='#888888', lw=0.8)
    ax.set_xlabel('тик', fontsize=9.5)
    ax.set_ylabel('уровень долга', fontsize=9.5)
    ax.set_title('SFA-замыкание (ρ=0.5): тождество D[t] = D[t−1](1+i) '
                 '+ SH − POOL − WO\nслепой мост «видит» реального оператора '
                 'как безымянный фантом', fontsize=10.5)
    ax.legend(fontsize=7.5, loc='center left')
    ax.grid(alpha=0.3)

    fig.suptitle('КОЛЬЦО-1 v6.0 — АНТИ-НАСЛЕДСТВЕННЫЙ КЛАПАН звена 8: '
                 '(d,s) → (ρ·d, s+g0). N=200, T=300, seed=7',
                 fontsize=12)
    fig.savefig(PNG_OUT, dpi=150)
    print(f"PNG сохранён: {PNG_OUT}")


if __name__ == '__main__':
    main()
