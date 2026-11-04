#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RED THREAD AUDIT v0.4 — график (4 траектории + Δ-матрица + периметр +
walk-forward). Шрифт: Noto Sans SC + DejaVu Sans (кириллица)."""
import json
import csv
import matplotlib.font_manager as fm
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
fm.fontManager.addfont('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

OUT = '/home/z/my-project/scripts/rta_v0_4_out'
S = json.load(open(f'{OUT}/summary.json', encoding='utf-8'))

TERR = ['RUS', 'USA', 'CHN', 'EUR']
NAMES = {'RUS': 'Россия', 'USA': 'США', 'CHN': 'Китай', 'EUR': 'Еврозона'}
C = {'act': '#1a1a2e', 'imf': '#e07a5f', 'op': '#3d5a80', 'lin': '#81b29a'}

rows = list(csv.DictReader(open(f'{OUT}/results.csv', encoding='utf-8')))
ser = {}
for r in rows:
    t = r['territory']
    ser.setdefault(t, {})
    for k in ('d_actual', 'd_imf_path', 'd_op3y'):
        if r[k] != '':
            ser[t].setdefault(k, {})[int(r['year'])] = float(r[k])

fig = plt.figure(figsize=(16.5, 9.2), constrained_layout=True)
gs = fig.add_gridspec(2, 4)

# --- ряд 1: траектории ---
for i, t in enumerate(TERR):
    ax = fig.add_subplot(gs[0, i])
    s = ser[t]
    ya = sorted(s.get('d_actual', {}))
    ax.plot(ya, [s['d_actual'][y] for y in ya], color=C['act'], lw=1.8,
            label='факт (WEO)')
    yi = sorted(y for y in s.get('d_imf_path', {}) if y >= 2025)
    ax.plot(yi, [s['d_imf_path'][y] for y in yi], color=C['imf'], lw=2.0,
            ls='--', marker='o', ms=3, label='путь IMF 2025→31')
    yo = sorted(s.get('d_op3y', {}))
    ax.plot(yo, [s['d_op3y'][y] for y in yo], color=C['op'], lw=2.0,
            ls='-.', label='оператор (θ 22–24)')
    lin31 = S['diff2031'][t]['lin31']
    imf31 = S['diff2031'][t]['imf31']
    op31 = S['diff2031'][t]['op31']
    ax.plot([2031], [lin31], marker='D', ms=7, color=C['lin'],
            ls='none', label='линейный контроль')
    ax.fill_between([2030.6, 2031.4], min(op31, imf31), max(op31, imf31),
                    color=C['imf'], alpha=0.18)
    top = max(max(s['d_actual'].values()), lin31, imf31, op31) * 1.24
    ax.set_ylim(0, top)
    ax.annotate(f'Δлин {S["diff2031"][t]["lin"]:+.1f}',
                xy=(2001, top * 0.965), fontsize=9.5, color=C['lin'],
                fontweight='bold', va='top')
    ax.annotate(f'Δоп {S["diff2031"][t]["op3y"]:+.1f}',
                xy=(2001, top * 0.875), fontsize=9.5, color=C['op'],
                fontweight='bold', va='top')
    ax.set_title(f'{NAMES[t]}: долг, % ВВП', fontsize=11, fontweight='bold')
    ax.grid(alpha=0.3)
    ax.set_xlim(2000, 2032.5)
    if i == 0:
        ax.legend(fontsize=7.5, loc='center left', bbox_to_anchor=(0.02, 0.62))
    ax.text(0.02, 0.02, f'θ: r={S["theta"][t]["r3"]:.2f}  g='
            f'{S["theta"][t]["g3"]:.2f}  pb={S["theta"][t]["p3"]:.2f}',
            transform=ax.transAxes, fontsize=7.5, color='#555')

# --- ряд 2: Δ-матрица / периметр / walk-forward ---
axh = fig.add_subplot(gs[1, 0])
import numpy as np
D = S['r7_distances']
M = np.zeros((4, 4))
for a in range(4):
    for b in range(4):
        if a == b:
            M[a, b] = 0
        else:
            M[a, b] = D.get(f'{TERR[a]}-{TERR[b]}',
                            D.get(f'{TERR[b]}-{TERR[a]}', 0))
im = axh.imshow(M, cmap='RdYlGn_r', vmin=0, vmax=2.2)
axh.set_xticks(range(4), TERR, fontsize=9)
axh.set_yticks(range(4), TERR, fontsize=9)
for a in range(4):
    for b in range(4):
        axh.text(b, a, f'{M[a,b]:.2f}', ha='center', va='center',
                 fontsize=8.5, fontweight='bold')
axh.set_title('R7: попарные Δ графов\n(норм. признаки, 0..1)', fontsize=10)

axp = fig.add_subplot(gs[1, 1:3])
x = np.arange(4)
w = 0.38
core = [S['perimeter'][t]['core'] for t in TERR]
priv = [S['perimeter'][t]['priv'] or 0 for t in TERR]
b1 = axp.bar(x - w / 2, core, w, color=C['op'], label='публичное ядро (WEO/FM)')
b2 = axp.bar(x + w / 2, priv, w, color=C['lin'], label='частный кредит (WB)')
for xi, (c, p) in enumerate(zip(core, priv)):
    rt = S['perimeter'][TERR[xi]]['ratio']
    axp.text(xi - w / 2, c + 3, f'{c:.0f}', ha='center', fontsize=9)
    axp.text(xi + w / 2, p + 3, f'{p:.0f}', ha='center', fontsize=9)
    axp.text(xi, max(c, p) + 18, f'×{rt:.2f}', ha='center', fontsize=10,
             fontweight='bold', color='#833')
axp.set_xticks(x, [f'{NAMES[t]}\n(год {S["perimeter"][t]["year"]})'
                   for t in TERR], fontsize=9)
axp.set_ylabel('% ВВП')
axp.set_title('Периметр: ядро vs частный слой; ×N — частное/ядро '
              '(РФ 3.31 — максимум)', fontsize=10)
axp.legend(fontsize=8.5)
axp.grid(alpha=0.3, axis='y')
axp.set_ylim(0, 260)

axw = fig.add_subplot(gs[1, 3])
wfo = [S['walkforward'][t]['rmse_op'] for t in TERR]
wfn = [S['walkforward'][t]['rmse_na'] for t in TERR]
axw.bar(x - w / 2, wfo, w, color=C['op'], label='оператор')
axw.bar(x + w / 2, wfn, w, color='#aaa', label='наивный (d[t−1])')
for xi, (o, n) in enumerate(zip(wfo, wfn)):
    axw.text(xi - w / 2, o + 0.1, f'{o:.1f}', ha='center', fontsize=8.5)
    axw.text(xi + w / 2, n + 0.1, f'{n:.1f}', ha='center', fontsize=8.5)
axw.set_xticks(x, TERR, fontsize=9)
axw.set_title('Walk-forward 2005–25:\nRMSE, п.п. (наивный везде лучше)',
              fontsize=10)
axw.legend(fontsize=8.5)
axw.grid(alpha=0.3, axis='y')

fig.suptitle('RED THREAD AUDIT v0.4 — периметр, идентификация θ, R7-инвариантность '
             '(RUS/USA/CHN/EUR; IMF datamapper + WB, 2026-09-08; граф не подгонялся)',
             fontsize=12.5, fontweight='bold')
fig.savefig('/home/z/my-project/download/Red_Thread_Audit_v0_4.png', dpi=150)
print('PNG сохранён')
