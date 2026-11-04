#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R10 plot: матрица переходов + strict-штраф по слоям (красная нить)."""
import csv
import json
import matplotlib.pyplot as plt
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False

BASE = '/home/z/my-project/download/'
rows = list(csv.DictReader(open(BASE + 'RED_THREAD_матрица_переходов.csv')))
summ = json.load(open(BASE + 'RED_THREAD_матрица_переходов.json'))

B50, B90 = 1.77, 2.73
COL = {'мир': '#7fbf7f', 'шум': '#e6c229', 'событие': '#c0392b'}

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5.6), constrained_layout=True,
                               gridspec_kw={'width_ratios': [1.45, 1]})

# ---------- панель 1: ShockResponse vs ΔD ----------
ax1.axvspan(-B50, B50, color='#7fbf7f', alpha=0.10)
ax1.axvspan(-B90, -B50, color='#e6c229', alpha=0.10)
ax1.axvspan(B50, B90, color='#e6c229', alpha=0.10)
ax1.axvline(B90, color='#c0392b', lw=0.8, ls='--')
ax1.axvline(-B90, color='#c0392b', lw=0.8, ls='--')
for band in ('мир', 'шум', 'событие'):
    pts = [(float(r['ShockResponse_pp']), float(r['delta_D_pp']))
           for r in rows if r['band_v06'] == band and r['delta_D_pp']]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    ax1.scatter(xs, ys, s=14, c=COL[band], alpha=0.55, label=band, edgecolors='none')
sp = [(float(r['ShockResponse_pp']), float(r['delta_D_pp']))
      for r in rows if r['spoof_year'] == 'True' and r['delta_D_pp']]
ax1.scatter([p[0] for p in sp], [p[1] for p in sp], s=95, facecolors='none',
            edgecolors='#1a1a1a', linewidths=1.4, label='спуф-годы (неплатёж)')
ax1.set_xlabel('ShockResponse: одношаговый SFA-оператор, п.п. ВВП')
ax1.set_ylabel('ΔD: изменение долга/ВВП, п.п.')
ax1.set_title('Матрица переходов R10: 10 кейсов × 2001–2023 (230 строк)\n'
              'полоса v0.6: мир ≤1.77 / шум ≤2.73 / событие >2.73', fontsize=11)
ax1.legend(loc='upper left', bbox_to_anchor=(1.01, 1.0), fontsize=8, frameon=False)
ax1.set_ylim(-45, 145)
ax1.grid(alpha=0.15)

# ---------- панель 2: strict-штраф по слоям ----------
labels = ['Δ11 коллеги\n(единицы цепи)', 'r_marg коллеги\n(марг. восстановления)',
          'Σie реального слоя\n(% ВВП·год в спуф-окнах)']
vals = [16.7, 37.5, 5.37]
bars = ax2.barh(labels, vals, color=['#4a6fa5', '#4a6fa5', '#c0392b'], alpha=0.85)
for b, v in zip(bars, vals):
    ax2.text(b.get_width() + 0.7, b.get_y() + b.get_height() / 2, f'−{v:.1f}%',
             va='center', fontsize=10)
ax2.set_xlabel('Доля доказательств, теряющая статус при строгом режиме')
ax2.set_title('Strict-штраф: один механизм в двух слоях\n'
              '«канал, управляемый стороной, — сигнал, не доказательство»', fontsize=11)
ax2.set_xlim(0, 46)
ax2.grid(alpha=0.15, axis='x')

fig.suptitle('КРАСНАЯ НИТЬ — РАУНД 10 / R10: строгий режим не опровергает — перемещает',
             fontsize=12, fontweight='bold')
fig.savefig(BASE + 'RED_THREAD_R10_матрица_переходов.png', dpi=150)
print('saved PNG')
