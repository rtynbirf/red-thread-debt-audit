#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RTA v0.2 — график: факт vs замороженный граф + SFA операторов."""
import csv
import os

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

DATA = '/home/z/my-project/scripts/rta_v0_2_out/results.csv'
PNG = '/home/z/my-project/download/Red_Thread_Audit_v0_2.png'

rows = list(csv.DictReader(open(DATA)))
ser = {}
for r in rows:
    ser.setdefault(r['country'], []).append(r)

NAMES = {'GRC': 'Греция', 'ARG': 'Аргентина', 'ZMB': 'Замбия',
         'LKA': 'Шри-Ланка', 'DEU': 'Германия (контроль)'}
EVENTS = {
    'GRC': [(2010.42, 'доступ'), (2012.21, 'PSI')],
    'ARG': [(2001.96, 'дефолт'), (2005.42, 'обмен'), (2020.58, 'обмен')],
    'ZMB': [(2005.29, 'HIPC'), (2020.87, 'дефолт'), (2024.21, 'сделка')],
    'LKA': [(2022.29, 'мораторий'), (2024.70, 'сделка')],
    'DEU': [],
}
SFA_BARS = [
    ('ARG 2002\nдевальвация', 90.9),
    ('ARG 2023\nдевальвация', 145.7),
    ('LKA 2022\nдефолт+курс', 33.5),
    ('ZMB 2020\nдефолт', 35.9),
    ('DEU 2010\nбанки', 8.1),
    ('GRC 2012\nPSI', -31.2),
    ('ARG 2005\nобмен', -24.5),
    ('ZMB 2005\nHIPC', -30.1),
]

plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False
fig, axes = plt.subplots(2, 3, figsize=(15.0, 8.2),
                         constrained_layout=True)

for ax, c in zip([axes[0][0], axes[0][1], axes[0][2],
                  axes[1][0], axes[1][1]], ['GRC', 'ARG', 'ZMB', 'LKA', 'DEU']):
    rs = ser[c]
    yrs = [int(r['year']) for r in rs if r['d_actual'] != '']
    da = [float(r['d_actual']) for r in rs if r['d_actual'] != '']
    yp = [int(r['year']) for r in rs]
    dp = [float(r['d_pred']) for r in rs]
    ax.plot(yrs, da, 'o-', ms=3, lw=1.6, color='#1f4e79', label='факт (IMF WEO)')
    ax.plot(yp, dp, '--', lw=1.6, color='#C00000',
            label='замороженный граф v0.1')
    for y, lab in EVENTS[c]:
        ax.axvline(y, color='#B8860B', ls=':', lw=1.2)
        ax.text(y, ax.get_ylim()[1] * 0.97, ' ' + lab, rotation=90,
                va='top', fontsize=7, color='#B8860B')
    ax.set_title(f"{NAMES[c]}: долг/ВВП", fontsize=10.5)
    ax.set_ylabel('% ВВП', fontsize=9)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8, loc='upper left')

ax = axes[1][2]
vals = [v for _, v in SFA_BARS]
labs = [k for k, _ in SFA_BARS]
colors = ['#C00000' if v > 0 else '#1f4e79' for v in vals]
bars = ax.bar(range(len(vals)), vals, color=colors)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2,
            v + (3 if v > 0 else -9), f'{v:+.0f}', ha='center', fontsize=8)
ax.set_xticks(range(len(labs)))
ax.set_xticklabels(labs, fontsize=6.5)
ax.axhline(0, color='black', lw=0.8)
ax.set_title('SFA-операторы, которых нет в графе v0.1\n'
             '(переоценка стока, п.п. ВВП)', fontsize=10.5)
ax.set_ylabel('п.п. ВВП', fontsize=9)
ax.grid(alpha=0.3, axis='y')

fig.suptitle('RED THREAD AUDIT v0.2: реальные данные через замороженный граф '
             'v0.1 (d[t+1]=((1+r)/(1+g))d−pb). Модель не подгонялась.',
             fontsize=11.5)
fig.savefig(PNG, dpi=150)
print(f'PNG: {PNG}')
