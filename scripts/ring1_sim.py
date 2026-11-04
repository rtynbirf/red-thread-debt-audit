#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
КОЛЬЦО-1: минимальная модель замкнутого воспроизводства требований.
Исполнение шага 12 Чамберлена: включатели/выключатели операторов вместо риторики.

Дизайн (честно, G-статус):
- N голов; каждая: возраст, срок жизни, горб продуктивности, заявка d (долг), имущество s.
- Кредиторов-индивидуумов НЕТ: служба долга уходит в общий пул-реестр,
  пул выплачивает доход пропорционально имуществу (запись + правило, без лица).
- Кредит sigma: заём на прожиточный минимум (единственный источник долга в игрушке).
- Наследование rho: A = полный рекурс (d и s переходят); B = non-recourse
  (актив несёт обязательство: ребёнок получает max(s-d,0), заявка гасится активом);
  C = полный сброс (ребёнок стартует с подъёмных g0).
- Юбилей: обнуление d каждые K тиков (падёж по закону).
- phi: доля собранного пула, реинвестируемая в продуктивность (переключатель режима A6).
- Принуждение и реестр в игрушке НЕЯВНЫ (взыскание всегда успешно, запись d/s
  существует по построению) - честно помечено, отдельные выключатели = следующий шаг.
- Смертность встроена (срок жизни 48-78), рост = phi-канал.

Метрики: lambda25 = средний темп роста суммарной заявки за 25 тиков (~поколение)
там, где D>50; D/Y в конце; число кризисных тиков (доля несостоятельных >20%);
первый кризис; Gini имущества; доля top10% имущества; средний рост Y;
корреляция dY/dt с пулом (знак dY/dR - тест режимности A6).
"""
import numpy as np


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


def run(rho='A', sigma=True, phi=0.0, jubilee=0, N=200, T=300,
        i_rate=0.06, seed=7, subsist=70.0, stress=0.5, g0=15.0, ymax=8.0):
    rng = np.random.default_rng(seed)
    age = rng.uniform(18.0, 50.0, N)
    life = 18.0 + rng.uniform(30.0, 60.0, N)          # смерть в 48-78
    life = np.maximum(life, age + 2.0)
    d = np.zeros(N)
    s = rng.uniform(0.0, 20.0, N)
    y_mult = 1.0
    D = np.zeros(T); Y = np.zeros(T); POOL = np.zeros(T)
    DEFR = np.zeros(T); GS = np.zeros(T); TOP = np.zeros(T)

    for t in range(T):
        y_base = 100.0 * y_mult * np.minimum(age / 25.0, 1.0) \
                 * np.clip(1.0 - (age - 55.0) / 30.0, 0.3, 1.0)
        # A6-каноника: заявка давит продуктивность (стресс долга)
        y_eff = y_base * (1.0 - stress * np.clip(d / np.maximum(3.0 * y_base, 1.0), 0.0, 1.0))
        d *= (1.0 + i_rate)
        cons = np.maximum(subsist, 0.6 * y_eff)
        shortfall = np.maximum(cons - y_eff, 0.0)
        if sigma:
            d += shortfall                             # заём на прожиточный минимум
        else:
            s = np.maximum(s - shortfall, 0.0)         # проедание имущества
        inc_pay = np.minimum(np.maximum(y_eff - cons, 0.0), d)
        liq = np.minimum(s, d - inc_pay)
        s -= liq
        d -= (inc_pay + liq)
        pool = float((inc_pay + liq).sum())
        tot_s = float(s.sum())
        if tot_s > 0:
            s += pool * (s / tot_s)                    # рента пула - имущим, пропорционально
        if phi > 0:
            y_mult = min(y_mult * (1.0 + phi * pool / max(float(y_eff.sum()), 1.0)), ymax)
        if jubilee and (t + 1) % jubilee == 0:
            d[:] = 0.0                                 # юбилей = падёж по закону
        # смерть и перенос через границу поколения (единственное место встречи D и H)
        dead = age >= life
        k = int(dead.sum())
        if k:
            dp, sp = d[dead].copy(), s[dead].copy()
            if rho == 'A':
                d_new, s_new = dp.copy(), sp.copy()
            elif rho == 'B':
                s_new = np.maximum(sp - dp, 0.0); d_new = np.zeros(k)
            else:
                s_new = np.zeros(k); d_new = np.zeros(k)
            s_new += g0
            d[dead], s[dead] = d_new, s_new
            age[dead] = 18.0
            life[dead] = 18.0 + rng.uniform(30.0, 60.0, k)
        age += 1.0

        D[t], Y[t], POOL[t] = float(d.sum()), float(y_eff.sum()), pool
        DEFR[t] = float(np.mean(d > 5.0 * np.maximum(y_base, 1.0)))
        GS[t], TOP[t] = gini(s), top_share(s)

    # метрики
    # тренд переноса: exp(25 * наклон log(D+1)) - устойчив к юбилейным пилам и сбросам
    tt = np.arange(T, dtype=float)
    slope = float(np.polyfit(tt, np.log(D + 1.0), 1)[0])
    lam = float(np.exp(25.0 * slope))
    crises = np.where(DEFR > 0.2)[0]
    dY = np.diff(Y[50:]) / np.maximum(Y[50:-1], 1.0)
    corr = float('nan')
    if np.std(dY) > 0 and np.std(POOL[50:-1]) > 0:
        corr = float(np.corrcoef(dY, POOL[50:-1])[0, 1])
    return dict(rho=rho, sigma=sigma, phi=phi, jubilee=jubilee,
                lam=lam, D_over_Y=float(D[-1] / max(Y[-1], 1.0)),
                n_crisis=int(crises.size),
                first_crisis=int(crises[0]) if crises.size else -1,
                defr_end=float(DEFR[-1]), gini=float(GS[-1]), top=float(TOP[-1]),
                Y_growth=float(np.mean(dY)) * 100.0, corr_dY_R=corr,
                D=D, GS=GS)


if __name__ == '__main__':
    configs = [
        ('A',            dict(rho='A')),
        ('B',            dict(rho='B')),
        ('C',            dict(rho='C')),
        ('A,sigma=выкл', dict(rho='A', sigma=False)),
        ('A,юбилей30',   dict(rho='A', jubilee=30)),
        ('A,phi=0.25',   dict(rho='A', phi=0.25)),
    ]
    results = []
    hdr = (f"{'конфигурация':<16}{'λ25':>7}{'D/Y':>12}{'криз.':>6}{'1й кр.':>7}"
           f"{'деф.кон':>8}{'Gini(s)':>8}{'top10%':>7}{'ростY%':>8}{'corr(dY,R)':>11}")
    print(hdr)
    print('-' * len(hdr))
    for name, kw in configs:
        r = run(**kw)
        results.append((name, r))
        lam = f"{r['lam']:.2f}" if r['lam'] == r['lam'] else '—'
        fc = str(r['first_crisis']) if r['first_crisis'] >= 0 else '—'
        cor = f"{r['corr_dY_R']:+.2f}" if r['corr_dY_R'] == r['corr_dY_R'] else '—'
        print(f"{name:<16}{lam:>7}{r['D_over_Y']:>12.1f}{r['n_crisis']:>6}{fc:>7}"
              f"{r['defr_end']:>8.2f}{r['gini']:>8.2f}{r['top']:>7.2f}"
              f"{r['Y_growth']:>8.2f}{cor:>11}")

    # PNG: D(t) log + Gini(t)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams['font.family'] = 'DejaVu Sans'   # полная кириллица
    plt.rcParams['axes.unicode_minus'] = False

    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), constrained_layout=True)
    show = [('A', 'ρ=A (полный рекурс)'),
            ('B', 'ρ=B (актив несёт долг)'),
            ('C', 'ρ=C (сброс)'),
            ('A,юбилей30', 'ρ=A + юбилей 30')]
    for ax, key, title, ylab in (
            (axes[0], 'D', 'Суммарная заявка ΣD(t), log-шкала', 'ΣD'),
            (axes[1], 'GS', 'Концентрация имущества Gini(s)(t)', 'Gini(s)')):
        for name, r in results:
            if name not in [n for n, _ in show]:
                continue
            label = dict(show)[name]
            y = r[key].copy()
            if key == 'D':
                y[y <= 0] = np.nan
            ax.plot(y, lw=1.6, label=label)
        ax.set_title(title, fontsize=10.5)
        ax.set_xlabel('тики (годы)', fontsize=9.5)
        ax.set_ylabel(ylab, fontsize=9.5)
        ax.grid(alpha=0.3)
        if key == 'D':
            ax.set_yscale('log')
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc='outside lower center', ncols=4, fontsize=8.6)
    fig.suptitle('КОЛЬЦО-1: одна модель, разный перенос через смерть носителя '
                 '(N=200, T=300, σ=вкл, i=6%)', fontsize=11)
    out = '/home/z/my-project/download/КОЛЬЦО-1_результаты.png'
    fig.savefig(out, dpi=150)
    print(f"\nPNG сохранён: {out}")
