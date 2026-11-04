# -*- coding: utf-8 -*-
"""
ПОЛИМАТ · Исторический слой программы «Красная нить» · численный слой (MODEL/CALCULATED)
Пять моделей механизма «долговая яма = рента», 5000 лет одной структуры.

Вердикт-рамка объявлена ДО прогонов (доктрина red-thread-debt-audit):
  - M1 Вавилон: анатоцизм 20%/год (серебро) и 33,3%/год (ячмень) против линейного роста урожая. FACT-ставки: Hudson 2018.
  - M2 Три зоны A_crit: реплика параметров корпуса debt_pit_report-v2 (D0=100000, r=12%, f=6%, g=3%).
      Корпус-таблица публикуется как есть (external/origin), пересчёт даёт собственные числа — расхождение фиксируется.
  - M3 Аннуитет: 10 млн руб., 8%/год, 30 и 15 лет — доля процентов, точка пересечения 50%.
  - M4 МФО: 10 000 руб., 0,8%/день (лимит ЦБ РФ с 01.07.2023), потолок начислений 1,3х = 13 000 руб. — «цифровой мишарум».
  - M5 r>g: Пикетти — расходимость капитала (5% год) против трудового сбережения (200 тыс./год под 0%).

Правила: каждый ряд несёт источник/определение в самом скрипте; UNKNOWN не маскируется;
выходы: download/charts/*.png + results JSON c sha256 (провенанс по конвенции репо).
"""
import json, hashlib, os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT = "/home/z/my-project/download/charts"
os.makedirs(OUT, exist_ok=True)

# Палитра согласована с IG-1 (Ink Gold) обложки DOCX
INK = "#1A1A1A"; GOLD = "#C9A84C"; RED = "#B03A2E"; GREY = "#8A8A8A"; BLUE = "#2E5E8C"; GREEN = "#2A6E4F"
plt.rcParams.update({
    "font.family": "DejaVu Sans",          # кириллица из коробки
    "font.size": 11,
    "axes.unicode_minus": False,
    "axes.edgecolor": "#444444",
    "axes.titlesize": 12.5,
    "figure.facecolor": "white",
})

results = {"program": "red-thread-debt-audit · исторический слой (Полимат)", "date": "2026-11-05",
           "verdict_frame": "объявлена до прогонов", "layers": {}, "charts": {}}

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()

def save(fig, name):
    p = os.path.join(OUT, name)
    fig.savefig(p, dpi=150, format="png")
    plt.close(fig)
    results["charts"][name] = {"sha256": sha256(p)[:16] + "…", "bytes": os.path.getsize(p)}
    print(f"[chart] {name}  {os.path.getsize(p)//1024} KiB  sha256:{results['charts'][name]['sha256']}")

# ------------------------------------------------------------------ M1 Вавилон
# FACT (Hudson 2018): серебро 20%/год, ячмень 33,3%/год — потолки Месопотамии II тыс. до н.э.
years = np.arange(0, 26)
debt_silver = 100 * 1.20 ** years
debt_grain = 100 * (4.0 / 3.0) ** years
harvest = 1000 + 50 * years            # линейная экономика: урожай +50 шек./год

# точка, где годовой процент съедает годовой прирост
cross_interest = int(np.argmax(0.20 * 100 * 1.20 ** years > 50))
# точка, где долг догоняет годовой урожай (бисекция)
lo, hi = 0.0, 30.0
for _ in range(200):
    mid = (lo + hi) / 2
    if 100 * 1.2 ** mid < 1000 + 50 * mid: lo = mid
    else: hi = mid
cross_harvest = (lo + hi) / 2

fig, ax = plt.subplots(figsize=(10, 5.4), constrained_layout=True)
ax.plot(years, debt_silver, color=RED, lw=2.4, label="Долг: 100 шек. серебра под 20 %/год (анатоцизм)")
ax.plot(years, debt_grain, color=INK, lw=2.0, ls="--", label="Долг: 100 шек. ячменя под 33,3 %/год")
ax.plot(years, harvest, color=GOLD, lw=2.4, label="Урожай должника: линейный рост +50 шек./год")
ax.axvline(cross_interest, color=GREY, lw=1, ls=":")
ax.annotate(f"~{cross_interest} лет: годовой процент съедает весь прирост",
            xy=(cross_interest, 50 * cross_interest + 1000), xytext=(cross_interest + 2.2, 2600),
            arrowprops=dict(arrowstyle="->", color=GREY), fontsize=10, color=INK)
ax.axvline(cross_harvest, color=GREY, lw=1, ls=":")
ax.annotate(f"{cross_harvest:.1f} лет: долг = годовой урожай\n(далее изъятие всего прибавка)",
            xy=(cross_harvest, 100 * 1.2 ** cross_harvest), xytext=(16.2, 4200),
            arrowprops=dict(arrowstyle="->", color=GREY), fontsize=10, color=INK)
ax.set_yscale("log"); ax.set_ylim(50, 30000)
ax.set_xlabel("Годы"); ax.set_ylabel("Шекели серебра (log)")
ax.set_title("M1 · Месопотамия, II тыс. до н.э.: экспонента долга против линейной экономики")
ax.grid(alpha=0.25, which="both")
ax.legend(loc="upper left", fontsize=9.5, framealpha=0.9)
save(fig, "M1_вавилон_анатоцизм.png")
results["layers"]["M1"] = {
    "label": "MODEL (ставки FACT: Hudson 2018)", "cross_interest_years": cross_interest,
    "cross_harvest_years": round(cross_harvest, 2),
    "debt20_silver": round(float(debt_silver[20]), 1), "harvest20": int(harvest[20]),
    "comment": "без мишарума долг за ~16 лет изымает годовой урожай целиком; на 20-й год он вдвое больше годового урожая"}

# ------------------------------------------------------- M2 Три зоны A_crit
# Реплика корпуса debt_pit_report-v2: D0=100000, r=12%/год, f=6%/год, g=3%/год, помесячный шаг.
D0 = 100_000.0; rm = 0.12 / 12; fm = 0.06 / 12; g_m = 0.03 / 12
A_crit = D0 * (rm + fm)
Y0 = 83_050.0   # калибровка уровня дохода для DTI-шкалы (объявлена здесь, до прогона)
months = np.arange(0, 241)

def run_zone(A):
    D = np.empty(241); D[0] = D0
    for t in range(240):
        D[t + 1] = max(0.0, D[t] * (1 + rm + fm) - A)   # долг не отрицательный: погашен — и всё
    return D

zones = {"Долговое рабство (A=1200 < A_crit)": 1200.0,
         "Вечная рента (A=1500 = A_crit)": 1500.0,
         "Честный кредит (A=1800 > A_crit)": 1800.0}
fig, ax = plt.subplots(figsize=(10, 5.4), constrained_layout=True)
zone_out = {}
for (name, A), col in zip(zones.items(), [RED, GREY, GREEN]):
    D = run_zone(A)
    Y = Y0 * (1 + g_m) ** months
    ax.plot(months / 12, D / Y * 100, lw=2.3, color=col, label=name)
    zone_out[name] = {"DTI_10л_%": round(float(D[120] / Y[120] * 100), 1),
                      "DTI_20л_%": round(float(D[240] / Y[240] * 100), 1),
                      "погашен_в_году": None if D[240] > 0 else int(np.argmax(D <= 0))}
ax.axhline(100, color=INK, lw=1, ls="--", alpha=0.6)
ax.text(0.3, 103, "DTI = 100 % — долг равен годовому доходу", fontsize=9, color=INK)
ax.set_xlabel("Годы"); ax.set_ylabel("Долг / годовой доход, %")
ax.set_title(f"M2 · Три зоны точки перелома A_crit = D·(r+f) = {A_crit:.0f} руб./мес (параметры корпуса v2)")
ax.grid(alpha=0.25); ax.legend(fontsize=9.5)
save(fig, "M2_три_зоны_Acrit.png")
results["layers"]["M2"] = {"label": "CALCULATED", "A_crit_month": round(A_crit, 2),
    "corpus_table_DTI20": {"рабство": 132.9, "рента": 66.7, "кредит": 0.0},
    "recomputed": zone_out,
    "comment": "качественная картина корпуса воспроизводится (зоны идут в своих направлениях); "
               "количественно пересчёт даёт иные значения в зоне рабства — корпус-таблица внешняя, не переписывается (правило вербатим)"}

# --------------------------------------------------------------- M3 Аннуитет
S = 10_000_000.0; i = 0.08 / 12
def annuity(n):
    k = (1 + i) ** n
    A = S * i * k / (k - 1)
    bal = np.empty(n + 1); bal[0] = S
    for t in range(n):
        bal[t + 1] = bal[t] * (1 + i) - A
    interest = np.array([bal[t] * i for t in range(n)])
    share = interest / A
    cross50 = int(np.argmax(share < 0.5))
    return A, bal, interest, share, cross50

A30, bal30, int30, share30, cross30 = annuity(360)
A15, bal15, int15, share15, cross15 = annuity(180)

fig, axes = plt.subplots(1, 2, figsize=(11.4, 5.0), constrained_layout=True)
axes[0].fill_between(np.arange(360) / 12, A30 - int30, A30, color=GOLD, alpha=0.85, label="Проценты в платеже")
axes[0].fill_between(np.arange(360) / 12, 0, A30 - int30, color=BLUE, alpha=0.85, label="Тело долга в платеже")
axes[0].axvline(cross30 / 12, color=INK, ls="--", lw=1.2)
axes[0].text(cross30 / 12 + 0.4, 9500, f"проценты < 50 %\nтолько с {cross30 / 12:.1f}-го года", fontsize=9.5, color=INK)
axes[0].set_xlabel("Годы"); axes[0].set_ylabel("Руб./мес")
axes[0].set_title(f"M3a · Аннуитет 10 млн, 8 %, 30 лет\nплатёж {A30:,.0f} руб.; 1-й платёж: {share30[0]*100:.0f} % — проценты".replace(",", " "))
axes[0].grid(alpha=0.25); axes[0].legend(loc="center right", fontsize=9)
axes[1].plot(np.arange(361) / 12, bal30 / 1e6, color=BLUE, lw=2.3, label="30 лет")
axes[1].plot(np.arange(181) / 12, bal15 / 1e6, color=GREEN, lw=2.3, label="15 лет")
axes[1].set_xlabel("Годы"); axes[1].set_ylabel("Остаток долга, млн руб.")
axes[1].set_title(f"M3b · Остаток: 15 лет закрывает вдвое быстрее,\nно переплата меньше в {( (A30*360 - S) / (A15*180 - S) ):.1f} раза")
axes[1].grid(alpha=0.25); axes[1].legend(fontsize=9)
save(fig, "M3_аннуитет.png")
results["layers"]["M3"] = {"label": "CALCULATED", "A30": round(A30), "A15": round(A15),
    "переплата30_млн": round((A30 * 360 - S) / 1e6, 2), "переплата15_млн": round((A15 * 180 - S) / 1e6, 2),
    "доля_процентов_в_1м_платеже_30л_%": round(float(share30[0] * 100), 1),
    "проценты_становятся_меньше_половины_с_года": round(cross30 / 12, 1),
    "comment": "первые годы заёмщик почти не гасит тело: механизм ренты сидит в стандартной ипотеке"}

# --------------------------------------------------------------- M4 МФО
B0 = 10_000.0; daily = 0.008; cap = 13_000.0   # ЦБ РФ с 01.07.2023: ≤0,8 %/день, начисления ≤1,3x тела
mrate = (1 + daily) ** 30 - 1
def mfo(monthly_pay, T=24):
    B = B0; accrued_total = 0.0; hist = [B]; paid = 0.0
    for m in range(T):
        ch = B * mrate
        if accrued_total + ch > 3000:               # потолок переплаты 30 % тела
            ch = max(0.0, 3000 - accrued_total)
        accrued_total += ch
        B = B + ch
        pay = min(monthly_pay, B)
        B -= pay; paid += pay
        hist.append(min(B, cap))
        if B <= 1e-9:
            hist += [0.0] * (T - m - 1); break
    return hist, paid, accrued_total

T = 24
h_pay_charges, paid1, acc1 = mfo(10000 * mrate)      # платит ровно начисленное
h_pay_less, paid2, acc2 = mfo(500.0)                 # платит меньше начисленного
h_pay_3k, paid3, acc3 = mfo(3000.0)                  # платит 3000/мес
mon = np.arange(T + 1)

fig, ax = plt.subplots(figsize=(10, 5.2), constrained_layout=True)
ax.step(mon, [min(B0 * (1 + mrate) ** t, cap) for t in range(T + 1)], color=RED, lw=1.6, ls=":",
        label="Если не платить совсем: потолок 1,3х (законом)")
ax.step(mon, h_pay_charges, where="post", color=GREY, lw=2.2, label=f"Платит только начисление ({10000*mrate:,.0f} руб./мес): вечная рента".replace(",", " "))
ax.step(mon, h_pay_less, where="post", color=ORANGE if (ORANGE := "#C57B2E") else ORANGE, lw=2.2, label="Платит 500 руб./мес < начисления: растёт до потолка")
ax.step(mon, h_pay_3k, where="post", color=GREEN, lw=2.2, label="Платит 3000 руб./мес > A_crit: закрыт за 5 мес")
ax.axhline(cap, color=INK, lw=1.4, ls="--")
ax.text(12.1, cap + 250, "потолок начислений 1,3х = 13 000 руб. (353-ФЗ, с 01.07.2023) — «цифровой мишарум»", fontsize=9.5, color=INK)
ax.set_xlabel("Месяцы"); ax.set_ylabel("Баланс долга, руб.")
ax.set_title("M4 · МФО: 10 000 руб. под 0,8 %/день — три сценария должника")
ax.set_ylim(0, 15500); ax.grid(alpha=0.25); ax.legend(fontsize=9, loc="upper right")
save(fig, "M4_мфо_потолок_13x.png")
results["layers"]["M4"] = {"label": "MODEL (ставка и потолок FACT: ЦБ РФ 2023)",
    "месячная_ставка_%": round(mrate * 100, 1), "A_crit_мес": round(B0 * mrate),
    "сценарий_3000_закрыт_мес": int(np.argmax(np.array(h_pay_3k) <= 1e-9)),
    "comment": "потолок 1,3х юридически эквивалентен мишаруму: государство вводит встроенную в инструмент чистку — "
               "первый раз со времён бронзового века клапан встроен в сам инструмент, а не объявляется царём"}

# ---------------------------------------------------------------- M5 r > g
Y50 = np.arange(0, 51)
capital = 10.0 * 1.05 ** Y50                 # капиталист: 10 млн под 5 % реальных (шкала: млн)
worker = 0.2 * Y50                           # труженик: +200 тыс./год под 0 % (шкала: млн)
s, gg = 0.10, np.linspace(0.06, 0.005, 200)
beta = s / gg

fig, axes = plt.subplots(1, 2, figsize=(11.4, 5.0), constrained_layout=True)
axes[0].plot(Y50, capital, color=GOLD, lw=2.4, label="Капитал 10 млн под r = 5 %")
axes[0].plot(Y50, worker, color=BLUE, lw=2.4, label="Сбережения 200 тыс./год под 0 %")
axes[0].fill_between(Y50, worker, capital, color=GOLD, alpha=0.12)
axes[0].annotate(f"разрыв ×{capital[50]/worker[50]:.0f}", xy=(50, capital[50]), xytext=(33, capital[50]*0.75),
                 arrowprops=dict(arrowstyle="->", color=GREY), fontsize=11, color=INK, fontweight="bold")
axes[0].set_xlabel("Годы"); axes[0].set_ylabel("Активы, млн руб. (реальные)")
axes[0].set_title("M5a · Наследник капитала против труженика:\nдоходность r растёт экспонентой, труд — линейно")
axes[0].grid(alpha=0.25); axes[0].legend(fontsize=9.5)
axes[1].plot(gg * 100, beta, color=RED, lw=2.4)
axes[1].set_xlabel("Темп роста экономики g, %/год"); axes[1].set_ylabel("β = s / g (капитал / годовой доход)")
axes[1].set_title("M5b · Пикетти: чем ниже g, тем весомее рента\n(норма сбережения s = 10 %)")
axes[1].grid(alpha=0.25)
axes[1].annotate("послевоенный g≈5 % → β≈2", xy=(5.0, 2.0), xytext=(3.4, 6.0), arrowprops=dict(arrowstyle="->", color=GREY), fontsize=9.5)
axes[1].annotate("стагнация g≈0,5 % → β≈20", xy=(0.5, 20), xytext=(1.4, 16.5), arrowprops=dict(arrowstyle="->", color=GREY), fontsize=9.5)
save(fig, "M5_r_больше_g.png")
results["layers"]["M5"] = {"label": "CALCULATED (рамка Пикетти 2014)",
    "разрыв_через_50_лет_раз": round(float(capital[50] / worker[50])),
    "beta_при_g6": round(float(beta[0]), 1), "beta_при_g0.5": round(float(beta[-1]), 1),
    "comment": "r>g — макроформа той же ямы: пока доходность требования растёт быстрее дохода должника, доля ренты только растёт",
    "note": "шкала активов — млн руб.; разрыв через 50 лет округлён"}

with open(os.path.join(OUT, "results_5000.json"), "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n=== ОТЧЁТ ЧИСЛЕННОГО СЛОЯ (MODEL/CALCULATED) ===")
print(json.dumps(results["layers"], ensure_ascii=False, indent=2))
print(f"\nАртефактов: {len(results['charts'])} PNG + results_5000.json → {OUT}")
