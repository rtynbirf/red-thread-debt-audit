#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
=============================================================================
КОЛЬЦО-1_v7 — ДВУХКОМПОНЕНТНЫЙ ЗАКОН НАСЛЕДОВАНИЯ + МИКРОКАНАЛ ОМОЛОЖЕНИЯ.
Раунд 13. Исполнение заданий (4) и (6) из ЕДИНЫЙ_АЛГОРИТМ_Красной_Нити_v6_0.md:
  (4) двухкомпонентный закон наследования — предрегистрированный ex-ante
      на НОВОМ seed=11 и T=600;
  (6) микроканал омоложения — инструментация распределения долга по
      остатку жизни носителя (предсказание v6.0: доля долга у носителей
      с остатком жизни <10 лет растёт при ρ↓).

ЗАМОРОЖЕННЫЕ КОНСТАНТЫ ФОРМЫ (опубликованы в v6.0, seed=7; переносятся
без подгонки — тест меж-семенной переносимости ФОРМЫ закона):
  экспонента самоусиления: −0.45 (m_eff/m измерено 1.00→3.31;
    экспоненты точек −0.49…−0.39);
  пол (внутрижизненная компонента): λ_F = 1.098 = λ(ρ=0), seed=7.
ПЕРЕИЗМЕРЯЕМЫЕ МАСШТАБЫ (двухстадийная дисциплина v6.0):
  λ_A = λ(ρ=1) и m — измеряются в базе seed=11 ДО свипа, переносятся
  на сетку ρ; свип не влияет на модель.

ДВУХКОМПОНЕНТНЫЙ ЗАКОН (форма объявлена ДО свипа):
  компонента наследственного стока (с самоусилением — омоложение):
      ln λ_exp(ρ) = ln λ_A − 25·m·ρ^(−0.45)·(1−ρ);
  пол свежего (внутрижизненного) потока: при ρ→0 экспонента гаснет,
      машина живёт на свежем долге:
      λ_2c(ρ) = max(λ_exp(ρ), λ_F).
  ВЕТКА ВЕРДИКТА (машинное правило): точка на ветке пола, если
  λ_2c ≤ 1.02·λ_F — критерий коридор [0.95, 1.25]; иначе ветка
  экспоненты — критерий полоса ±30% драга.

ВЕРДИКТ-РАМКА (предрегистрация, объявлена ДО прогонов; ни один новый
блок не потребляет rng — якорь обязан выжить):
  P0 ПОРТ-КОНТРОЛЬ: реплика seed=7/T=300 воспроизводит якорь v6
     λ = 4.585096118130804 бит в бит и m = measured_m(v6) — код перенесён
     вербатим, инструментация v7 чисто считающая.
  P1 ЯКОРЬ-ПЕРЕНОС: λ_A(seed=11, T=600) ∈ [3.90, 5.27] (±15% от якоря
     v6: инвариантность наклона экспоненты к удвоению окна) и
     m ∈ [0.0192, 0.0260] (0.022643 ±15%).
  P2 ДВУХКОМПОНЕНТНЫЙ ЗАКОН (главный тест): ≥ 4 из 5 точек свипа
     ρ ∈ {0.75, 0.5, 0.25, 0.1, 0} внутри критерия своей ветки.
     Числовые предсказания печатаются ДО свипа.
  P3 ОТРИЦАТЕЛЬНЫЙ КОНТРОЛЬ (закон v6 не был шумом семени): первый
     порядок с константной m на seed=11 ТОЖЕ отвергнут в той же
     сигнатуре — все η<0 при ρ≤0.25 и ≥2 точки вне полосы ±30%.
     Если первый порядок пройдёт — закон v6 объявляется шумом семени
     (публикуется как есть).
  P4 МИКРОКАНАЛ ОМОЛОЖЕНИЯ (предсказание v6.0 §6-(6)):
     (а) R10 — стоимостная доля долга у носителей с остатком жизни
         <10 лет — растёт при ρ↓: R10(ρ=0) > R10(ρ=1), монотонность
         по сетке;
     (в) ML — долг-взвешенная средняя остаточная жизнь держателей —
         убывает при ρ↓: ML(ρ=0) < ML(ρ=1).
     P4 = (а) ∧ (в); сила (б): R10(0) ≥ 1.3·R10(1) публикуется отдельно.
  P5 ЗАКОН ФАНТОМА #4 (SFA на новом семени, ρ=0.5): тождество стока
     D[t] = D[t−1]·(1+i) + SH − POOL − WO закрывается < 1e-8·max(D);
     слепой мост (без члена WO) видит фантом ≥ 0.3·max|WO|.

СТАТУС: E — модельная конструкция с предрегистрацией; модель не меняется
по результату; промахи публикуются как есть.
ДЕТЕРМИНИЗМ: seed=11, T=600 объявлены заданием (4) v6.0 до прогона.
=============================================================================
"""
import json
import hashlib
import sys
import numpy as np

OUT_DIR = '/home/z/my-project/scripts/ring1_v7_out'
PNG_OUT = '/home/z/my-project/download/КОЛЬЦО-1_v7_двухкомпонентный_закон.png'

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
    MRL = np.zeros(T)   # v7: долг-взвешенная средняя остаточная жизнь
    R10S = np.zeros(T)  # v7: доля долга у носителей с остатком <10 лет
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
        # --- v7: инструментация микроканала омоложения (чисто считающая,
        #     rng не потребляет — якорь обязан выжить бит в бит) ---
        wdb = d > 1e-9
        if wdb.any():
            rem_life = life - age
            dw = d[wdb]
            rw = rem_life[wdb]
            MRL[t] = float((rw * dw).sum() / dw.sum())
            R10S[t] = float(dw[rw < 10.0].sum() / dw.sum())
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
                mrl_mean=float(MRL[50:].mean()),
                r10_mean=float(R10S[50:].mean()),
                D=D, GS=GS, Y=Y, POOL=POOL, DEFR=DEFR, SH=SH, IEFF=IEFF,
                WO=WRITEOFF, MTR=MTR, MRL=MRL, R10S=R10S, ZS=ZS)


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


def lam_2c(rho, lam_a, m, exp_frozen=-0.45, floor=1.098):
    """Двухкомпонентный закон (форма заморожена до свипа).
    Возвращает (кривая, ветка)."""
    if rho <= 0.0:
        return floor, 'floor'
    lam_exp = lam_a * float(np.exp(-25.0 * m * rho ** (-0.45) * (1.0 - rho)))
    curve = max(lam_exp, floor)
    branch = 'floor' if curve <= floor * 1.02 else 'exp'
    return curve, branch


def main():
    import os
    os.makedirs(OUT_DIR, exist_ok=True)
    results = {}
    LAM_A_V6 = 4.585096118130804
    EXP_FROZEN = -0.45      # v6.0, seed=7 — заморожен ex-ante
    FLOOR_FROZEN = 1.098    # v6.0, λ(ρ=0), seed=7 — заморожен ex-ante
    LAM_BAND = (3.90, 5.27)     # ±15% якоря v6 (P1)
    M_BAND = (0.0192, 0.0260)   # 0.022643 ±15% (P1)
    RHO_GRID = (1.0, 0.75, 0.5, 0.25, 0.1, 0.0)
    NM = {1.0: 'v7_р100', 0.75: 'v7_р075', 0.5: 'v7_р050',
          0.25: 'v7_р025', 0.1: 'v7_р010', 0.0: 'v7_р000'}

    # ---- СТАДИЯ 0: порт-контроль (seed=7/T=300, вербатим v6) ----
    print('=' * 74)
    print('СТАДИЯ 0: ПОРТ-КОНТРОЛЬ. Реплика v6 (seed=7, T=300) должна дать')
    print('якорь бит в бит: код v6 перенесён вербатим, v7-блоки только читают.')
    print('=' * 74)
    rep = run(rho='A', rho_frac=1.0)
    lam_rep = rep['lam']
    m_rep = float(rep['MTR'].sum() / max(float(rep['D'].sum()), 1e-30))
    with open('/home/z/my-project/scripts/ring1_v6_out/results.json',
              encoding='utf-8') as f:
        m_v6 = float(json.load(f)['meta']['measured_m'])
    p0 = (abs(lam_rep - LAM_A_V6) < 1e-9) and (abs(m_rep - m_v6) < 1e-12)
    print(f"P0 реплика: λ = {lam_rep:.15f} (v6: {LAM_A_V6:.15f}); "
          f"m = {m_rep:.6f} (v6: {m_v6:.6f})  →  {'OK' if p0 else 'СЛОМАН'}")
    if not p0:
        print('ПОРТ-КОНТРОЛЬ ПРОВАЛЕН — свип не запускается.')
        sys.exit(1)

    # ---- СТАДИЯ 1: база seed=11/T=600 + измерение масштабов ----
    print('\n' + '=' * 74)
    print('СТАДИЯ 1: база seed=11, T=600 (задание (4) v6.0). Измеряются')
    print('масштабы λ_A и m; форма закона (экспонента −0.45, пол 1.098)')
    print('заморожена из v6.0 и НЕ подгоняется.')
    print('=' * 74)
    results['v7_р100'] = run(rho='A', rho_frac=1.0, T=600, seed=11)
    lam_a = results['v7_р100']['lam']
    m = float(results['v7_р100']['MTR'].sum()
              / max(float(results['v7_р100']['D'].sum()), 1e-30))
    sd = results['v7_р100']
    sigma_base = float(np.mean(sd['SH'][50:] / np.maximum(sd['D'][50:], 1e-30)))
    print(f"λ_A(seed=11, T=600) = {lam_a:.6f}   "
          f"полоса P1 [3.90, 5.27]: "
          f"{'ВНУТРИ' if LAM_BAND[0] <= lam_a <= LAM_BAND[1] else 'ВНЕ'}")
    print(f"m(seed=11) = {m:.6f}   полоса P1 [0.0192, 0.0260]: "
          f"{'ВНУТРИ' if M_BAND[0] <= m <= M_BAND[1] else 'ВНЕ'}")
    print(f"σ базы (свежий приток SH/D, t≥50) = {sigma_base:.4f}")

    print('\n--- СТАДИЯ 1.5: ЧИСЛОВЫЕ ПРЕДСКАЗАНИЯ ДО СВИПА (заморожены) ---')
    preds, branches = {}, {}
    for rho in RHO_GRID[1:]:
        curve, branch = lam_2c(rho, lam_a, m, EXP_FROZEN, FLOOR_FROZEN)
        preds[rho] = curve
        branches[rho] = branch
        if branch == 'floor':
            print(f'  ρ={rho:4.2f}: ВЕТКА ПОЛА  λ_2c = {curve:.3f}   '
                  f'критерий [0.95, 1.25]')
        else:
            lo = curve * float(np.exp(-0.3 * (np.log(lam_a) - np.log(curve))))
            hi = curve * float(np.exp(0.3 * (np.log(lam_a) - np.log(curve))))
            drag = np.log(lam_a) - np.log(curve)
            print(f'  ρ={rho:4.2f}: ветка экспоненты λ_2c = {curve:7.3f}   '
                  f'полоса ±30% драга: [{lo:7.3f}, {hi:7.3f}] '
                  f'(драг {drag:.3f})')
    lam_fo = {rho: lam_a * float(np.exp(-25.0 * m * (1.0 - rho)))
              for rho in RHO_GRID[1:]}
    print(f'  первый порядок (контроль P3): ' +
          ', '.join(f'ρ={r:g}: {lam_fo[r]:.3f}' for r in RHO_GRID[1:]))
    print('  объявления сделаны — запускается свип; модель не меняется.')

    # ---- СТАДИЯ 2: свип ρ на seed=11/T=600 + тернарные приоры ----
    configs = [
        ('v7_р075', dict(rho='A', rho_frac=0.75)),
        ('v7_р050', dict(rho='A', rho_frac=0.50)),
        ('v7_р025', dict(rho='A', rho_frac=0.25)),
        ('v7_р010', dict(rho='A', rho_frac=0.10)),
        ('v7_р000', dict(rho='A', rho_frac=0.00)),
        ('v7_тернB', dict(rho='B')),
        ('v7_тернC', dict(rho='C')),
    ]
    for name, kw in configs:
        results[name] = run(T=600, seed=11, **kw)

    hdr = (f"{'конфигурация':<10}{'λ25':>8}{'D/Y':>9}{'Gini':>7}"
           f"{'R10%':>7}{'ML':>6}{'σ%':>7}{'ΣWO/Σp0':>10}")
    print('\n' + hdr)
    print('-' * len(hdr))
    for name, r in results.items():
        wo_p0 = float(r['WO'].sum()) / max(r['p0_created'], 1e-30)
        sig = float(np.mean(r['SH'][50:] / np.maximum(r['D'][50:], 1e-30)))
        print(f"{name:<10}{r['lam']:>8.3f}{r['D_over_Y']:>9.3g}"
              f"{r['gini']:>7.3f}{r['r10_mean']*100:>7.1f}"
              f"{r['mrl_mean']:>6.1f}{sig*100:>7.2f}"
              f"{wo_p0:>10.2f}")

    print('\n--- СУДЬБЫ ЛОТОВ (доля p0, выборка) ---')
    for name in ['v7_р100', 'v7_р050', 'v7_р000', 'v7_тернB', 'v7_тернC']:
        fs = results[name]['fates_share']
        top = sorted(fs.items(), key=lambda kv: -kv[1])[:4]
        print(f"  {name:<10} " + ", ".join(f"{k}={v*100:.1f}%"
                                           for k, v in top))

    # ---- вердикты ----
    v = {}
    v['P0'] = p0

    v['P1'] = (LAM_BAND[0] <= lam_a <= LAM_BAND[1]
               and M_BAND[0] <= m <= M_BAND[1])

    ok_pts, p2_detail = 0, {}
    for rho in RHO_GRID[1:]:
        lam_m = results[NM[rho]]['lam']
        curve, branch = branches[rho], None
        curve = preds[rho]
        if branch is None:
            branch = 'floor' if curve <= FLOOR_FROZEN * 1.02 else 'exp'
        if branch == 'floor':
            ok = 0.95 <= lam_m <= 1.25
            eta = float(np.log(lam_m / curve))
        else:
            drag = float(np.log(lam_a) - np.log(curve))
            eta = float(np.log(lam_m / curve))
            ok = abs(eta) <= 0.3 * drag
        ok_pts += int(ok)
        p2_detail[NM[rho]] = dict(lam=lam_m, lam_2c=curve, branch=branch,
                                  eta=eta, ok=bool(ok))
        print(f"P2 {NM[rho]}: λ_изм {lam_m:7.3f} vs λ_2c {curve:7.3f} "
              f"[{branch}]  η={eta:+.3f}  {'OK' if ok else 'ВНЕ КРИТЕРИЯ'}")
    v['P2'] = ok_pts >= 4

    eta_fo, fo_out = {}, 0
    for rho in (0.75, 0.5, 0.25, 0.1):
        lam_m = results[NM[rho]]['lam']
        drag = 25.0 * m * (1.0 - rho)
        eta = float(np.log(lam_m / lam_a)) + drag
        eta_fo[NM[rho]] = eta
        fo_out += int(abs(eta) > 0.3 * drag)
    all_neg = all(eta_fo[NM[r]] < 0 for r in (0.75, 0.5, 0.25, 0.1))
    print(f"P3 первый порядок: η = " +
          ", ".join(f"{eta_fo[NM[r]]:+.3f}" for r in (0.75, 0.5, 0.25, 0.1)) +
          f"; вне полосы: {fo_out}/4; все η<0: {all_neg}")
    v['P3'] = all_neg and fo_out >= 2

    r10s = {r: results[NM[r]]['r10_mean'] for r in RHO_GRID}
    mls = {r: results[NM[r]]['mrl_mean'] for r in RHO_GRID}
    seq_r10 = [r10s[r] for r in RHO_GRID]
    mono_r10 = all(seq_r10[i] <= seq_r10[i + 1] + 1e-12
                   for i in range(len(seq_r10) - 1))
    strength = r10s[0.0] / max(r10s[1.0], 1e-30)
    print(f"P4 R10: ρ=1 → {r10s[1.0]*100:.1f}% … ρ=0 → {r10s[0.0]*100:.1f}% "
          f"(×{strength:.2f}); R10(0)>R10(1): {r10s[0.0] > r10s[1.0]}; "
          f"монотонность: {mono_r10}")
    print(f"   ML: ρ=1 → {mls[1.0]:.1f} лет … ρ=0 → {mls[0.0]:.1f} лет; "
          f"ML(0)<ML(1): {mls[0.0] < mls[1.0]}")
    v['P4'] = (r10s[0.0] > r10s[1.0] and mono_r10
               and mls[0.0] < mls[1.0])

    r5 = results['v7_р050']
    resid_raw = sfa_decomp(r5)
    wo = r5['WO']
    tol = 1e-8 * float(r5['D'].max())
    err_with = float(np.abs(resid_raw + wo).max())
    blind_mag = float(np.abs(resid_raw).max())
    wo_max = float(wo.max())
    print(f"P5 SFA (ρ=0.5, seed=11): max|resid+WO| = {err_with:.3e} "
          f"(допуск {tol:.3e}); слепой мост: фантом {blind_mag:.4g} "
          f"при max|WO| = {wo_max:.4g}")
    v['P5'] = err_with < tol and blind_mag > 0.3 * wo_max

    # ---- описательно: перенос экспоненты (без вердикта) ----
    expo_meas = {}
    for rho in (0.75, 0.5, 0.25, 0.1):
        lam_m = results[NM[rho]]['lam']
        ratio = -float(np.log(lam_m / lam_a)) / (25.0 * m * (1.0 - rho))
        expo_meas[NM[rho]] = float(np.log(ratio) / np.log(rho)) if rho > 0 \
            else None
    print('\n--- ОПИСАТЕЛЬНО: перенос экспоненты самоусиления '
          '(заморожена −0.45) ---')
    for rho in (0.75, 0.5, 0.25, 0.1):
        ratio = -float(np.log(results[NM[rho]]['lam'] / lam_a)
                       ) / (25.0 * m * (1.0 - rho))
        print(f"  {NM[rho]}: m_eff/m = {ratio:.2f}  "
              f"экспонента = {expo_meas[NM[rho]]:+.2f}")

    print('\n--- ВЕРДИКТЫ (предрегистрация раунда 13) ---')
    verdicts = {
        'P0 порт-контроль: реплика v6 бит в бит': v['P0'],
        'P1 якорь-перенос: λ_A, m внутри полос ±15%': v['P1'],
        'P2 двухкомпонентный закон (≥4/5 точек)': v['P2'],
        'P3 первый порядок отвергнут и на seed=11': v['P3'],
        'P4 микроканал омоложения: R10↑, ML↓ при ρ↓': v['P4'],
        'P5 закон фантома #4 (SFA, seed=11)': v['P5'],
    }
    for k, ok in verdicts.items():
        print(f"  {k:<58} {'ПОДТВЕРЖДЕНА' if ok else 'ОТКЛОНЕНА'}")

    # ---- экспорт: json + csv ----
    meta = {
        'python': sys.version.split()[0], 'numpy': np.__version__,
        'seed': 11, 'T': 600,
        'lambda_definition': 'λ25 = exp(25·slope log(D+1)), T=600, N=200',
        'status': 'E — двухкомпонентный закон наследования + микроканал '
                  'омоложения, предрегистрация (раунд 13)',
        'preregistered': list(verdicts.keys()),
        'frozen_from_v6': {'exponent': EXP_FROZEN, 'floor': FLOOR_FROZEN,
                           'lambda_anchor_v6_seed7': LAM_A_V6,
                           'm_v6_seed7': m_v6},
        'bands': {'lambda_A': LAM_BAND, 'm': M_BAND},
        'measured_base': {'lambda_A_seed11': lam_a, 'm_seed11': m,
                          'sigma_base': sigma_base},
        'law_2c': 'λ_2c(ρ) = max(λ_A·exp(−25m·ρ^(−0.45)(1−ρ)), λ_F); '
                  'ветка пола — критерий [0.95,1.25], ветка экспоненты — '
                  '±30% драга',
        'microchannel': 'R10 — доля долга у носителей с остатком жизни '
                        '<10 лет; ML — долг-взвешенная остаточная жизнь; '
                        'инструментация без rng',
        'predictions_2c': {f'ρ={k}': vv for k, vv in preds.items()},
        'branches': {f'ρ={k}': vv for k, vv in branches.items()},
        'p2_detail': p2_detail,
        'eta_first_order': eta_fo,
        'expo_measured': expo_meas,
        'r10_by_rho': {f'ρ={k}': vv for k, vv in r10s.items()},
        'mrl_by_rho': {f'ρ={k}': vv for k, vv in mls.items()},
    }
    export = {'meta': meta,
              'verdicts': {k: bool(x) for k, x in verdicts.items()},
              'runs': {}}
    for name, r in results.items():
        sig = float(np.mean(r['SH'][50:] / np.maximum(r['D'][50:], 1e-30)))
        export['runs'][name] = {
            k: vv for k, vv in r.items()
            if k not in ('D', 'GS', 'Y', 'POOL', 'DEFR', 'SH', 'IEFF',
                         'ZS', 'WO', 'MTR', 'MRL', 'R10S')}
        export['runs'][name]['wo_total'] = float(r['WO'].sum())
        export['runs'][name]['mtr_total'] = float(r['MTR'].sum())
        export['runs'][name]['sigma_mean'] = sig
        export['runs'][name]['zone_mean_после_50'] = r['zone_mean']
    blob = json.dumps(export, ensure_ascii=False, sort_keys=True)
    h = hashlib.sha256(blob.encode()).hexdigest()
    export['integrity'] = {'results_sha256': h}
    with open(f'{OUT_DIR}/results.json', 'w', encoding='utf-8') as f:
        json.dump(export, f, ensure_ascii=False, indent=1)
    with open(f'{OUT_DIR}/timeseries.csv', 'w', encoding='utf-8') as f:
        f.write('run,tick,D,Y,pool,defr,slavery_share,wo,mtr,mrl,r10\n')
        for name, r in results.items():
            for t in range(600):
                f.write(f"{name},{t},{r['D'][t]:.6f},{r['Y'][t]:.6f},"
                        f"{r['POOL'][t]:.6f},{r['DEFR'][t]:.6f},"
                        f"{r['ZS']['рабство'][t]:.6f},{r['WO'][t]:.6e},"
                        f"{r['MTR'][t]:.6e},{r['MRL'][t]:.6f},"
                        f"{r['R10S'][t]:.6f}\n")
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

    # (а) двухкомпонентный закон на новом семени
    ax = axes[0, 0]
    rho_cont = np.linspace(0.0, 1.0, 400)
    lam_exp_c = np.where(
        rho_cont > 0,
        lam_a * np.exp(-25.0 * m * np.power(np.maximum(rho_cont, 1e-6),
                                            -0.45) * (1.0 - rho_cont)),
        0.0)
    curve_c = np.maximum(lam_exp_c, FLOOR_FROZEN)
    fo_c = lam_a * np.exp(-25.0 * m * (1.0 - rho_cont))
    drag_c = np.log(lam_a) - np.maximum(np.log(curve_c),
                                        np.log(FLOOR_FROZEN) - 20.0)
    drag_c = np.maximum(drag_c, 0.0)
    ax.fill_between(rho_cont, curve_c * np.exp(-0.3 * drag_c),
                    curve_c * np.exp(0.3 * drag_c),
                    color='#B8860B', alpha=0.18, label='полоса ±30% драга')
    ax.plot(rho_cont, curve_c, '-', color='#8B0000', lw=1.8,
            label=f'двухкомпонентный (заморожен: −0.45, пол {FLOOR_FROZEN})')
    ax.plot(rho_cont, fo_c, '--', color='#4682B4', lw=1.5,
            label='первый порядок (константная m) — контроль P3')
    ax.axhline(FLOOR_FROZEN, color='#888888', ls=':', lw=1.2,
               label=f'пол λ_F = {FLOOR_FROZEN} (v6, seed=7)')
    for rho in RHO_GRID:
        lm = results[NM[rho]]['lam']
        ax.plot(rho, lm, 'o', ms=7, color='#8B0000')
        ax.annotate(f'{lm:.2f}', (rho, lm), textcoords='offset points',
                    xytext=(6, 5), fontsize=8.5)
    ax.plot([0], [results['v7_тернB']['lam']], 'x', ms=8, color='#555555')
    ax.plot([0], [results['v7_тернC']['lam']], 'x', ms=8, color='#555555')
    ax.plot([], [], 'x', color='#555555', label='тернарные B/C (seed=11)')
    ax.plot([], [], 'o', color='#8B0000', label='измерено (seed=11, T=600)')
    ax.text(0.02, 0.98,
            f'λ_A = {lam_a:.3f}; m = {m:.4f} (база seed=11);\n'
            f'форма закона заморожена из v6.0 без подгонки.',
            transform=ax.transAxes, fontsize=7.2, va='top',
            bbox=dict(boxstyle='round', fc='#FFF8DC', alpha=0.85))
    ax.set_xlabel('ρ — доля долга, переживаемая наследником', fontsize=9.5)
    ax.set_ylabel('λ25', fontsize=9.5)
    ax.set_yscale('log')
    ax.set_title('Двухкомпонентный закон наследования на новом семени\n'
                 'seed=11, T=600; форма перенесена из v6.0 ex-ante',
                 fontsize=10.5)
    ax.legend(fontsize=7, loc='lower right')
    ax.grid(alpha=0.3, which='both')

    # (б) траектории D
    ax = axes[0, 1]
    for rho in RHO_GRID:
        ax.plot(range(600), results[NM[rho]]['D'], lw=1.2,
                label=f'ρ={rho:g} (λ={results[NM[rho]]["lam"]:.2f})')
    ax.set_yscale('log')
    ax.set_xlabel('тик', fontsize=9.5)
    ax.set_ylabel('D (сто standing стока)', fontsize=9.5)
    ax.set_title('Стоячий сток при T=600: экспонента гасится клапаном ρ\n'
                 'log-шкала, seed=11', fontsize=10.5)
    ax.legend(fontsize=7.5, loc='upper left')
    ax.grid(alpha=0.3, which='both')

    # (в) микроканал омоложения
    ax = axes[1, 0]
    rgs = list(RHO_GRID)
    r10v = [r10s[r] * 100.0 for r in rgs]
    ax.bar([f'{r:g}' for r in rgs], r10v, color='#8B4513', alpha=0.75,
           label='R10 — доля долга у носителей с остатком <10 лет')
    for i, (r_, w_) in enumerate(zip(rgs, r10v)):
        ax.annotate(f'{w_:.1f}%', (i, w_), textcoords='offset points',
                    xytext=(0, 4), ha='center', fontsize=8)
    ax.set_xlabel('ρ', fontsize=9.5)
    ax.set_ylabel('R10, % стока', fontsize=9.5, color='#8B4513')
    ax2 = ax.twinx()
    ax2.plot([f'{r:g}' for r in rgs], [mls[r] for r in rgs], 'D--',
             color='#4682B4', lw=1.5, label='ML — средняя остаточная жизнь')
    ax2.set_ylabel('ML, тиков (лет)', fontsize=9.5, color='#4682B4')
    ax.set_title('Микроканал омоложения (предсказание v6.0 §6-(6)):\n'
                 'при ρ↓ долг молодеет — R10 растёт, ML падает', fontsize=10.5)
    ln1, lb1 = ax.get_legend_handles_labels()
    ln2, lb2 = ax2.get_legend_handles_labels()
    ax.legend(ln1 + ln2, lb1 + lb2, fontsize=7.5, loc='upper center')
    ax.grid(alpha=0.3, axis='y')

    # (г) перенос экспоненты самоусиления
    ax = axes[1, 1]
    pts = [r for r in (0.75, 0.5, 0.25, 0.1)]
    ratio_meas = []
    for rho in pts:
        lm = results[NM[rho]]['lam']
        ratio_meas.append(-float(np.log(lm / lam_a))
                          / (25.0 * m * (1.0 - rho)))
    ax.plot(pts, [1.0] * len(pts), 's-', color='#888888', lw=1.2,
            label='константная m (первый порядок) — отвергнут v6')
    ax.plot(pts, ratio_meas, 'o', ms=7, color='#8B0000',
            label='измерено на seed=11/T=600')
    rc = np.linspace(0.05, 1.0, 200)
    ax.plot(rc, rc ** EXP_FROZEN, '--', color='#2E8B57', lw=1.6,
            label=f'замороженный закон ρ^(−0.45) (v6, seed=7)')
    for r_, w_ in zip(pts, ratio_meas):
        ax.annotate(f'{w_:.2f}', (r_, w_), textcoords='offset points',
                    xytext=(5, 5), fontsize=8.5)
    ax.set_yscale('log')
    ax.set_xlabel('ρ', fontsize=9.5)
    ax.set_ylabel('m_eff / m', fontsize=9.5)
    ax.set_title('Самоусиление клапана: перенос экспоненты на новое семя\n'
                 'экспоненты точек: ' +
                 ', '.join(f'{e:+.2f}' for e in expo_meas.values() if e),
                 fontsize=10.5)
    ax.legend(fontsize=7.5, loc='upper right')
    ax.grid(alpha=0.3, which='both')

    fig.suptitle('КОЛЬЦО-1 v7.0 — ДВУХКОМПОНЕНТНЫЙ ЗАКОН НАСЛЕДОВАНИЯ + '
                 'МИКРОКАНАЛ ОМОЛОЖЕНИЯ. N=200, T=600, seed=11',
                 fontsize=12)
    fig.savefig(PNG_OUT, dpi=150)
    print(f"PNG сохранён: {PNG_OUT}")


if __name__ == '__main__':
    main()

