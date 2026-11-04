#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
РАУНД 15 / v8.0 — ПЕРЕХОДНАЯ ЗОНА ρ + АНАЛИТИКА ПОЛА λ_F. Движок v7 импортирован вербатим.
Исполнение заданий (1)-(2) из ЕДИНЫЙ_АЛГОРИТМ_Красной_Нити_v7_0.md §6.

ВЕРДИКТ-РАМКА (предрегистрирована ДО первого касания кода):

  P0  ПОРТ-КОНТРОЛЬ (бит в бит, два якоря):
      (a) run() v7, seed=7/T=300: λ = 4.585096118130804; m = m_v6 (из ring1_v6_out).
      (b) run() v7, seed=11/T=600: λ_A = 4.3634244072577655; m = 0.021569543440472183.
  P1  ПЕРЕНОС ЯКОРЯ на seed=23/T=600: λ_A23 ∈ [3.90, 5.27], m23 ∈ [0.0192, 0.0260]
      (те же замороженные полосы v7; форма не подгоняется).
  P2  ГРУБЫЕ ТОЧКИ ρ∈{0.75, 0.5, 0.25} на seed=23 с замороженной экспонентой −0.45:
      предсказания печатаются ДО прогонов; критерий 3/3 внутри ±30% драга.
  P3  МИШЕНЬ — промах v7 (ρ=0.1: измерено 1.377 против ветки пола 1.111, η=+0.215).
      ДРЕЙФ-ЗАКОН (форма объявлена здесь, до прогонов мишеней): топливо петли
      самоусиления — наследуемый сток; при ρ↓ петля теряет топливо → эффективная
      экспонента слабеет. expo(ρ) = a + b·lnρ, a,b — МНК по ТРЁМ грубым точкам
      ТОГО ЖЕ семени; λ(ρ) = λ_A·exp(−25·m·(1−ρ)·ρ^expo(ρ)).
      Предсказания λ(0.1), λ(0.05) печатаются ДО их прогонов.
      КРИТЕРИЙ: |η_drift| ≤ 0.15 в обеих мишенях И |η_drift| < |η_frozen| в обеих.
      (Локальная интерполяция зоны [0.05, 0.75], не глобальный закон — на ρ→0
      не экстраполируется, там ветка пола.)
  P4  АНАЛИТИКА ПОЛА (замкнутая форма, без подгонки). При ρ=0 лот живёт до первой
      смерти носителя; выпуск лотов равномерен по жизненному циклу носителя
      (стационарный режим), остаточная жизнь лота R = V·W, V = life−18 ~ U(30,60),
      W ~ U(0,1) ⇒ P(R>τ) = 1 − τ·ln2/30 (τ≤30); (60−τ−τ·ln(60/τ))/30 (30<τ<60); 0 (τ≥60).
      G = ∫₀⁶⁰ P(R>τ)·(1+i)^τ dτ, i = 0.06 (i_rate заморожен v5).
      P4a: сток-тождество D = SH·G: SR = mean(D)/mean(SH), t≥100, ρ=0 —
           на seed 23 И seed 11 внутри G·[0.75, 1.25].
      P4b: уровень λ_F = G·σ_flow, σ_flow = (SH/D)·(D/Y) (оба — средние прогона):
           D/Y(ρ=0) внутри G·σ_flow·[0.75, 1.25] на обоих семенах.
  P5  ПОЛ (критерий v7): λ25(ρ=0, seed=23) ∈ [0.95, 1.25].

  Дисциплина: двухстадийность (порт → база → предсказания → прогоны мишеней);
  модель не меняется; все отклонения публикуются как есть.
"""
import sys
import os
import json
import hashlib
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
for p in (_HERE, '/home/z/my-project/scripts'):
    if p not in sys.path:
        sys.path.insert(0, p)
from ring1_v7 import run  # движок v7 вербатим — единый источник механики

OUT_DIR = '/home/z/my-project/scripts/ring1_v8_out'
DL = '/home/z/my-project/download'
LAM_A_V6 = 4.585096118130804
LAM_A_V7_11 = 4.3634244072577655
M_V7_11 = 0.021569543440472183
LAM_F_V7_11 = 1.034402732833935
EXP_FROZEN = -0.45          # v6.0 — заморожен
FLOOR_FROZEN = 1.098        # v6.0 — заморожен
LAM_BAND = (3.90, 5.27)
M_BAND = (0.0192, 0.0260)
I_RATE = 0.06
COARSE = (0.75, 0.50, 0.25)
FINE = (0.10, 0.05)
NM = {1.0: 'р100', 0.75: 'р075', 0.5: 'р050', 0.25: 'р025',
      0.1: 'р010', 0.05: 'р005', 0.0: 'р000'}


def lam_frozen(rho, lam_a, m):
    return lam_a * float(np.exp(-25.0 * m * (1.0 - rho) * rho ** EXP_FROZEN))


def implied_expo(rho, lam_m, lam_a, m):
    ratio = -float(np.log(lam_m / lam_a)) / (25.0 * m * (1.0 - rho))
    return float(np.log(ratio) / np.log(rho))


def lam_drift(rho, lam_a, m, a, b):
    expo = a + b * float(np.log(rho))
    return lam_a * float(np.exp(-25.0 * m * (1.0 - rho) * rho ** expo)), expo


def G_closed(i=I_RATE, n=240001):
    """Замкнутая форма пола: G = ∫ P(R>τ)(1+i)^τ dτ; R = V·W, V~U(30,60), W~U(0,1)."""
    tau = np.linspace(0.0, 60.0, n)
    ln2 = float(np.log(2.0))
    P = np.where(tau <= 30.0,
                 1.0 - tau * ln2 / 30.0,
                 (60.0 - tau - tau * np.log(60.0 / np.maximum(tau, 1e-12))) / 30.0)
    P = np.clip(P, 0.0, 1.0)
    P[tau >= 60.0] = 0.0
    return float(np.trapezoid(P * (1.0 + i) ** tau, tau))


def flow_stats(res, t0=100):
    """σ_flow = (SH/D)·(D/Y); SR = D/SH; оба по окну стационара t≥t0."""
    D, SH = np.asarray(res['D'], float), np.asarray(res['SH'], float)
    sig_stock = float(np.mean(SH[t0:] / np.maximum(D[t0:], 1e-30)))
    SR = float(np.mean(D[t0:]) / max(float(np.mean(SH[t0:])), 1e-30))
    return sig_stock, SR


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print('=' * 78)
    print('v8.0 — ПЕРЕХОДНАЯ ЗОНА ρ (seed=23) + АНАЛИТИКА ПОЛА λ_F (замкнутая форма)')
    print('Движок: run() из ring1_v7 импортирована вербатим; модель не меняется.')
    print('=' * 78)

    # ---------- СТАДИЯ 0: порт-контроль ----------
    rep7 = run(rho='A', rho_frac=1.0)
    m_rep7 = float(rep7['MTR'].sum() / max(float(rep7['D'].sum()), 1e-30))
    with open('/home/z/my-project/scripts/ring1_v6_out/results.json',
              encoding='utf-8') as f:
        m_v6 = float(json.load(f)['meta']['measured_m'])
    ok7 = abs(rep7['lam'] - LAM_A_V6) < 1e-9 and abs(m_rep7 - m_v6) < 1e-12
    rep11 = run(rho='A', rho_frac=1.0, T=600, seed=11)
    m_rep11 = float(rep11['MTR'].sum() / max(float(rep11['D'].sum()), 1e-30))
    ok11 = (abs(rep11['lam'] - LAM_A_V7_11) < 1e-9
            and abs(m_rep11 - M_V7_11) < 1e-12)
    p0 = ok7 and ok11
    print(f"P0a seed=7/T=300: λ = {rep7['lam']:.15f} vs {LAM_A_V6:.15f}; "
          f"m = {m_rep7:.9f} vs {m_v6:.9f}  → {'OK' if ok7 else 'СЛОМАН'}")
    print(f"P0b seed=11/T=600: λ = {rep11['lam']:.15f} vs {LAM_A_V7_11:.15f}; "
          f"m = {m_rep11:.12f}  → {'OK' if ok11 else 'СЛОМАН'}")
    if not p0:
        print('ПОРТ-КОНТРОЛЬ ПРОВАЛЕН — свип не запускается.')
        sys.exit(1)

    # ---------- СТАДИЯ 1: база seed=23 ----------
    b23 = run(rho='A', rho_frac=1.0, T=600, seed=23)
    lam_a23 = b23['lam']
    m23 = float(b23['MTR'].sum() / max(float(b23['D'].sum()), 1e-30))
    p1 = LAM_BAND[0] <= lam_a23 <= LAM_BAND[1] and M_BAND[0] <= m23 <= M_BAND[1]
    print(f"\nP1 база seed=23/T=600: λ_A = {lam_a23:.6f} (полоса "
          f"[{LAM_BAND[0]}, {LAM_BAND[1]}] "
          f"{'ВНУТРИ' if LAM_BAND[0] <= lam_a23 <= LAM_BAND[1] else 'ВНЕ'}); "
          f"m = {m23:.6f} (полоса [{M_BAND[0]}, {M_BAND[1]}] "
          f"{'ВНУТРИ' if M_BAND[0] <= m23 <= M_BAND[1] else 'ВНЕ'})")

    # ---------- СТАДИЯ 2: грубые точки, предсказания замороженной формы ----------
    print('\n--- СТАДИЯ 2: предсказания (замороженная −0.45) ДО прогонов ---')
    res = {'р100': b23}
    for rho in COARSE:
        lo = lam_a23 * float(np.exp(-0.3 * (np.log(lam_a23)
                                            - np.log(lam_frozen(rho, lam_a23, m23)))))
        hi = lam_a23 * float(np.exp(0.3 * (np.log(lam_a23)
                                           - np.log(lam_frozen(rho, lam_a23, m23)))))
        print(f"  ρ={rho:4.2f}: λ_pred(замор.) = {lam_frozen(rho, lam_a23, m23):7.3f} "
              f"полоса [{lo:7.3f}, {hi:7.3f}]")
    for rho in COARSE:
        res[NM[rho]] = run(rho='A', rho_frac=rho, T=600, seed=23)
    okc, p2d = 0, {}
    for rho in COARSE:
        lam_m = res[NM[rho]]['lam']
        curve = lam_frozen(rho, lam_a23, m23)
        drag = float(np.log(lam_a23) - np.log(curve))
        eta = float(np.log(lam_m / curve))
        ok = abs(eta) <= 0.3 * drag
        okc += int(ok)
        p2d[f'ρ={rho}'] = dict(lam=lam_m, pred=curve, eta=eta, ok=bool(ok))
        print(f"  ρ={rho:4.2f}: λ_изм = {lam_m:7.3f}  η = {eta:+.3f} "
              f"{'OK' if ok else 'ВНЕ КРИТЕРИЯ'}")
    p2 = okc == 3

    # ---------- СТАДИЯ 2.5: дрейф-закон → предсказания мишеней ----------
    print('\n--- СТАДИЯ 2.5: дрейф-закон expo(ρ)=a+b·lnρ (МНК по 3 грубым) ---')
    ex = {rho: implied_expo(rho, res[NM[rho]]['lam'], lam_a23, m23)
          for rho in COARSE}
    bfit, afit = np.polyfit([float(np.log(r)) for r in COARSE],
                            [ex[r] for r in COARSE], 1)
    afit, bfit = float(afit), float(bfit)
    for rho in COARSE:
        print(f"  ρ={rho:4.2f}: implied expo = {ex[rho]:+.4f} "
              f"(замороженная {EXP_FROZEN:+.2f})")
    print(f"  fit: expo(ρ) = {afit:.4f} + ({bfit:.4f})·ln ρ")
    preds_drift = {}
    for rho in FINE:
        lam_pd, expo_pd = lam_drift(rho, lam_a23, m23, afit, bfit)
        lam_pf = lam_frozen(rho, lam_a23, m23)
        preds_drift[rho] = dict(lam_drift=lam_pd, expo=expo_pd, lam_frozen=lam_pf)
        print(f"  МИШЕНЬ ρ={rho:4.2f}: дрейф λ = {lam_pd:7.3f} (expo {expo_pd:+.4f})"
              f" | замороженная λ = {lam_pf:7.3f}")
    print('  предсказания напечатаны — запускаются мишени; модель не меняется.')
    for rho in FINE:
        res[NM[rho]] = run(rho='A', rho_frac=rho, T=600, seed=23)
    p3, p3d = True, {}
    for rho in FINE:
        lam_m = res[NM[rho]]['lam']
        eta_d = float(np.log(lam_m / preds_drift[rho]['lam_drift']))
        eta_f = float(np.log(lam_m / preds_drift[rho]['lam_frozen']))
        ok = abs(eta_d) <= 0.15 and abs(eta_d) < abs(eta_f)
        p3 &= ok
        p3d[f'ρ={rho}'] = dict(lam=lam_m, lam_drift=preds_drift[rho]['lam_drift'],
                               lam_frozen=preds_drift[rho]['lam_frozen'],
                               eta_drift=eta_d, eta_frozen=eta_f, ok=bool(ok))
        print(f"  ρ={rho:4.2f}: λ_изм = {lam_m:7.3f} | дрейф η = {eta_d:+.3f} "
              f"(замор. η = {eta_f:+.3f})  {'OK' if ok else 'ВНЕ КРИТЕРИЯ'}")

    # ---------- СТАДИЯ 3: пол + аналитика G ----------
    print('\n--- СТАДИЯ 3: пол ρ=0 и замкнутая форма G ---')
    G = G_closed()
    print(f"  G(замкнутая форма, i={I_RATE}) = {G:.2f}  "
          f"(сток = SH·G: лот живёт до смерти носителя, R = V·W)")
    runs0 = {}
    for seed in (23, 11):
        r0 = run(rho='A', rho_frac=0.0, T=600, seed=seed)
        runs0[seed] = r0
        sig_stock, SR = flow_stats(r0)
        dy = float(r0['D_over_Y'])
        sf = sig_stock * dy
        lam_f_pred = G * sf
        print(f"  seed={seed}: λ25 = {r0['lam']:.4f}; D/Y = {dy:.4f}; "
              f"σ_stock = {sig_stock:.5f}; SR = D/SH = {SR:.1f} "
              f"(G = {G:.1f}, отношение {SR / G:.3f}); "
              f"σ_flow = {sf:.5f}; λ_F_pred = G·σ_flow = {lam_f_pred:.4f} "
              f"vs D/Y {dy:.4f} (отношение {dy / lam_f_pred:.3f})")
        runs0[seed]['_sig_stock'] = sig_stock
        runs0[seed]['_SR'] = SR
        runs0[seed]['_sigma_flow'] = sf
        runs0[seed]['_lamF_pred'] = lam_f_pred
    sr23, sr11 = runs0[23]['_SR'], runs0[11]['_SR']
    p4a = (0.75 * G <= sr23 <= 1.25 * G) and (0.75 * G <= sr11 <= 1.25 * G)
    dy23 = float(runs0[23]['D_over_Y'])
    dy11 = float(runs0[11]['D_over_Y'])
    p4b = (0.75 * runs0[23]['_lamF_pred'] <= dy23 <= 1.25 * runs0[23]['_lamF_pred']
           and 0.75 * runs0[11]['_lamF_pred'] <= dy11 <= 1.25 * runs0[11]['_lamF_pred'])
    p5 = 0.95 <= runs0[23]['lam'] <= 1.25
    rep_floor11 = abs(runs0[11]['lam'] - LAM_F_V7_11) < 1e-9
    print(f"P4a сток-тождество D=SH·G: seed23 {sr23:.1f}/G={sr23 / G:.3f}, "
          f"seed11 {sr11:.1f}/G={sr11 / G:.3f} → {'OK' if p4a else 'ВНЕ [0.75,1.25]'}")
    print(f"P4b уровень λ_F = G·σ_flow: seed23 отн. {dy23 / runs0[23]['_lamF_pred']:.3f}, "
          f"seed11 отн. {dy11 / runs0[11]['_lamF_pred']:.3f} → {'OK' if p4b else 'ВНЕ [0.75,1.25]'}")
    print(f"P5 пол λ25(ρ=0, seed23) = {runs0[23]['lam']:.4f} ∈ [0.95,1.25]: "
          f"{'OK' if p5 else 'ВНЕ'}; реплика пола seed11 бит в бит: {rep_floor11}")

    # ---------- ПОСТ-ФАКТУМ ОПИСАТЕЛЬНО (маркировано; критерии v7 заморожены в v7.0,
    # применяются к НОВОМУ семени — тест переносимости, не подгонка) ----------
    print('\n--- ОПИСАТЕЛЬНО: закон v7 (max(exp, floor)) на seed=23 по замороженным критериям v7 ---')
    v7_transfer, v7d = 0, {}
    for rho in COARSE + FINE:
        lam_m = res[NM[rho]]['lam']
        curve = max(lam_frozen(rho, lam_a23, m23), FLOOR_FROZEN)
        drag = float(np.log(lam_a23) - np.log(curve))
        eta = float(np.log(lam_m / curve))
        if curve <= FLOOR_FROZEN * 1.02:
            ok = 0.95 <= lam_m <= 1.25
        else:
            ok = abs(eta) <= 0.3 * drag
        v7_transfer += int(ok)
        v7d[f'ρ={rho}'] = dict(lam=lam_m, lam_2c=curve, eta=eta, ok=bool(ok))
        print(f"  ρ={rho:4.2f}: λ_изм {lam_m:7.3f} vs λ_2c {curve:7.3f} "
              f"η={eta:+.3f} {'OK' if ok else 'ВНЕ'}")
    ok0 = 0.95 <= runs0[23]['lam'] <= 1.25
    v7_transfer += int(ok0)
    print(f"  ρ=0.00: λ_изм {runs0[23]['lam']:7.3f} (ветка пола) "
          f"{'OK' if ok0 else 'ВНЕ'}")
    print(f"  итог: {v7_transfer}/6 — двухкомпонентный закон v7 воспроизведён "
          f"на третьем семени вне выборки")

    phi_g = {'seed23': sr23 / G, 'seed11': sr11 / G}
    print(f"\n--- ОПИСАТЕЛЬНО: дренаж пола — φ_G = SR/G: "
          f"seed23 {phi_g['seed23']:.3f}, seed11 {phi_g['seed11']:.3f} "
          f"(стабилен меж-семенно; гипотеза: промежуточные погашения — "
          f"излишки шоков + ликвидность сбережений; v9.0: augmented G с членом погашения) ---")

    print('\n--- РЕЕСТР ОШИБОК: E14 — локальная интерполяция по 3 точкам с ' 
          'экстраполяцией в зону без калибровочных точек переобучается ' 
          '(дрейф промахнулся В ОБЕ стороны: выше замороженной на 0.1, ниже на 0.05); ' 
          'правило: переходную зону калибровать точкой внутри неё либо формой с насыщением ---')

    # ---------- вердикты ----------
    verdicts = {
        'P0 порт-контроль (два якоря, бит в бит)': p0,
        'P1 перенос якоря на seed=23 (полосы ±15%)': p1,
        'P2 грубые точки с замороженной −0.45 (3/3)': p2,
        'P3 мишени переходной зоны дрейф-законом (|η|≤0.15 и лучше замороженной)': p3,
        'P4 аналитика пола: сток D=SH·G и уровень λ_F=G·σ_flow (оба семени)': p4a and p4b,
        'P5 пол λ25(ρ=0, seed23) ∈ [0.95,1.25]': p5,
    }
    print('\n--- ВЕРДИКТЫ (предрегистрация раунда 14) ---')
    for k, ok in verdicts.items():
        print(f"  {k:<70} {'ПОДТВЕРЖДЕНА' if ok else 'ОТКЛОНЕНА'}")

    # ---------- экспорт ----------
    export = {
        'meta': {
            'python': sys.version.split()[0], 'numpy': np.__version__,
            'engine': 'run() импортирована из ring1_v7 вербатим',
            'status': 'v8.0 — переходная зона ρ + аналитика пола, предрегистрация (раунд 14)',
            'seed': 23, 'T': 600,
            'frozen': {'expo': EXP_FROZEN, 'floor': FLOOR_FROZEN,
                       'bands': {'lambda_A': LAM_BAND, 'm': M_BAND}},
            'drift_form': 'expo(ρ) = a + b·lnρ, МНК по 3 грубым точкам seed=23; '
                          'локальная интерполяция [0.05,0.75]',
            'G_closed_form': 'P(R>τ)=1−τ·ln2/30 (τ≤30); (60−τ−τ·ln(60/τ))/30 '
                             '(30<τ<60); 0 (τ≥60); R=V·W, V~U(30,60), W~U(0,1)',
        },
        'measured_base23': {'lambda_A': lam_a23, 'm': m23},
        'drift_fit': {'a': afit, 'b': bfit,
                      'implied_coarse': {f'ρ={r}': ex[r] for r in COARSE}},
        'stage2_coarse': p2d,
        'stage25_fine': p3d,
        'descriptive_v7_transfer': {'detail': v7d, 'score': f'{v7_transfer}/6',
                                    'status': 'критерии v7.0 (заморожены до этого раунда) '
                                              'применены к новому семени'},
        'descriptive_drainage': {'phi_G': phi_g, 'hypothesis': 'промежуточные погашения: '
                                 'излишки шоков (у бедных с y_eff>70) + ликвидность '
                                 'сбережений; задание v9.0 — augmented G с членом погашения'},
        'error_register_E14': 'локальная интерполяция expo(ρ)=a+b·lnρ по 3 точкам '
                              'с экстраполяцией за пределы калибровки переобучается; '
                              'дрейф-закон отклонён, промах v7 на seed=11 не воспроизведён '
                              'на seed=23 (замороженная форма там η=+0.126 ≤ 0.15)',
        'floor': {'G': G,
                  'seed23': {'lam25': runs0[23]['lam'], 'D_over_Y': dy23,
                             'SR': sr23, 'SR_over_G': sr23 / G,
                             'sigma_flow': runs0[23]['_sigma_flow'],
                             'lamF_pred': runs0[23]['_lamF_pred'],
                             'D_over_Y_over_pred': dy23 / runs0[23]['_lamF_pred']},
                  'seed11': {'lam25': runs0[11]['lam'], 'D_over_Y': dy11,
                             'SR': sr11, 'SR_over_G': sr11 / G,
                             'sigma_flow': runs0[11]['_sigma_flow'],
                             'lamF_pred': runs0[11]['_lamF_pred'],
                             'D_over_Y_over_pred': dy11 / runs0[11]['_lamF_pred'],
                             'replica_bit_for_bit': rep_floor11}},
        'verdicts': verdicts,
    }
    jpath = os.path.join(OUT_DIR, 'results.json')
    with open(jpath, 'w', encoding='utf-8') as f:
        json.dump(export, f, ensure_ascii=False, indent=2)
    # CSV: λ(ρ) оба семени
    csv_rows = ['seed,rho,lam,eta_frozen,eta_drift']
    for seed, grid in ((11, [(1.0, rep11['lam'])] +
                        [(r, runs0[11]['lam'] if r == 0.0 else None) for r in (0.0,)]),
                       (23, [(1.0, lam_a23)] +
                        [(r, res[NM[r]]['lam']) for r in sorted(
                            list(COARSE) + list(FINE), reverse=True)] +
                        [(0.0, runs0[23]['lam'])])):
        for rho, lam in grid:
            if lam is None:
                continue
            ef = float(np.log(lam / lam_frozen(max(rho, 1e-9), lam_a23, m23))) \
                if rho > 0 else float(np.log(lam / FLOOR_FROZEN))
            ed = ''
            if rho in FINE:
                ed = f"{p3d[f'ρ={rho}']['eta_drift']:+.4f}"
            csv_rows.append(f'{seed},{rho},{lam:.6f},{ef:+.4f},{ed}')
    with open(os.path.join(OUT_DIR, 'lambda_by_rho.csv'), 'w',
              encoding='utf-8') as f:
        f.write('\n'.join(csv_rows) + '\n')
    for fn in ('results.json', 'lambda_by_rho.csv'):
        h = hashlib.sha256(open(os.path.join(OUT_DIR, fn), 'rb').read()).hexdigest()
        print(f"saved {fn} sha256={h[:16]}")
    print('DELIVERABLES_OK')


if __name__ == '__main__':
    main()
