#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""v8.0 plot: переходная зона ρ (оба семени + замороженный закон + дрейф) и пол/дренаж."""
import json
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

OUT = '/home/z/my-project/scripts/ring1_v8_out/'
v8 = json.load(open(OUT + 'results.json'))
v7 = json.load(open('/home/z/my-project/download/КОЛЬЦО-1_v7_результаты.json'))

lam_a23 = v8['measured_base23']['lambda_A']
m23 = v8['measured_base23']['m']
afit, bfit = v8['drift_fit']['a'], v8['drift_fit']['b']

def lam_2c(rho, lam_a, m):
    if rho <= 0:
        return 1.098
    return max(lam_a * float(np.exp(-25.0 * m * (1.0 - rho) * rho ** -0.45)), 1.098)

import numpy as np
xs = np.logspace(np.log10(0.04), 0, 200)
frozen = [lam_2c(x, lam_a23, m23) for x in xs]
dx, dy = [], []
for x in xs:
    if x >= 0.05:
        dx.append(x)
        dy.append(lam_a23 * float(np.exp(-25.0 * m23 * (1.0 - x)
                                         * x ** (afit + bfit * np.log(x)))))

s11 = {1.0: 4.3634244072577655, 0.75: 3.7331973986803972, 0.5: 3.0078671548059313,
       0.25: 2.105135376604578, 0.1: 1.377253122500999, 0.0: 1.034402732833935}
s23 = {1.0: lam_a23}
for k, v in v8['stage2_coarse'].items():
    s23[float(k.split('=')[1])] = v['lam']
for k, v in v8['stage25_fine'].items():
    s23[float(k.split('=')[1])] = v['lam']
s23[0.0] = v8['floor']['seed23']['lam25']

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.4), constrained_layout=True,
                               gridspec_kw={'width_ratios': [1.5, 1]})
ax1.axhspan(0.95, 1.25, color='#7fbf7f', alpha=0.18, label='ветка пола [0.95, 1.25]')
ax1.plot(xs, frozen, '--', color='#8B0000', lw=1.6,
         label='закон v7: max(exp(−0.45), пол 1.098)')
ax1.plot(dx, dy, ':', color='#2e7d32', lw=1.6,
         label='дрейф-интерполяция (отклонена, E14)')
ax1.plot(sorted(s11), [s11[k] for k in sorted(s11)], 's', color='#555555', ms=9,
         markerfacecolor='none', markeredgewidth=1.6, zorder=4,
         label='измерения seed=11 (v7)')
ax1.plot(sorted(s23), [s23[k] for k in sorted(s23)], 'o', color='#1f5fa8', ms=6,
         zorder=3, label='измерения seed=23 (v8)')
ax1.annotate('промах v7\n(η=+0.215)', xy=(0.1, 1.377), xytext=(0.14, 2.1),
             fontsize=8, arrowprops=dict(arrowstyle='->', lw=0.8))
ax1.annotate('на seed=23 промаха нет:\nη=+0.126 (в критерии)', xy=(0.1, 1.351),
             xytext=(0.18, 0.85), fontsize=8,
             arrowprops=dict(arrowstyle='->', lw=0.8))
ax1.set_xscale('log')
ax1.set_yscale('log')
ax1.set_xlabel('ρ — доля наследуемого долга')
ax1.set_ylabel('λ25')
ax1.set_title('Переходная зона ρ: третье семя подтверждает закон v7 (6/6),\n'
              'локальный дрейф-закон переобучается', fontsize=11)
ax1.legend(loc='upper left', fontsize=8, frameon=False)
ax1.grid(alpha=0.2, which='both')

seeds = ['seed=11', 'seed=23']
meas = [v8['floor']['seed11']['D_over_Y'], v8['floor']['seed23']['D_over_Y']]
pred = [v8['floor']['seed11']['lamF_pred'], v8['floor']['seed23']['lamF_pred']]
x = np.arange(2)
ax2.bar(x - 0.18, meas, 0.34, color='#1f5fa8', label='D/Y измеренный (ρ=0)')
ax2.bar(x + 0.18, pred, 0.34, color='#c0392b', alpha=0.75,
        label='G·σ_flow предсказанный (без дренажа)')
for i, (mv, pv) in enumerate(zip(meas, pred)):
    ax2.text(i - 0.18, mv + 0.15, f'{mv:.2f}', ha='center', fontsize=9)
    ax2.text(i + 0.18, pv + 0.15, f'{pv:.2f}', ha='center', fontsize=9)
    ax2.text(i, 1.1, f'φ_G = {meas[i] / pred[i]:.2f}', ha='center', fontsize=10,
             color='white', fontweight='bold',
             bbox=dict(boxstyle='round,pad=0.25', fc='#555555', ec='none'))
ax2.set_xticks(x)
ax2.set_xticklabels(seeds)
ax2.set_ylabel('уровень долга D/Y при ρ=0')
ax2.set_title('Пол машины: механизм верен, дренаж ≈ 0.71 стабилен\n'
              '(промежуточные погашения; G = 72.4, SR/G ≈ 0.71)', fontsize=11)
ax2.legend(fontsize=8, frameon=False)
ax2.grid(alpha=0.2, axis='y')

fig.suptitle('КРАСНАЯ НИТЬ — v8.0: пол λ_F получил замкнутую форму и измеренный дренаж',
             fontsize=12, fontweight='bold')
fig.savefig('/home/z/my-project/download/КОЛЬЦО-1_v8_переходная_зона.png', dpi=150)
print('saved PNG')
