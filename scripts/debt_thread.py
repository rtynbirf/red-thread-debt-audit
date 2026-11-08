#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Долговая нить как поток данных (Волна ×4 · П47, issue #3).

КРАСНАЯ НИТЬ: «долговая яма = рента». Витрина живёт данными:
data/debt.csv (дата/значение/источник-URL) + спарклайн в README,
регенерация — ежемесячным CI. Каждая строка csv несёт кликабельный
источник; двойная генерация идентична (детерминизм, правило E10/E14
программы: числа только из сохранённых источников).

Режимы:
  fetch    — живая выгрузка FRED GFDEBTN (Total Public Debt, млн USD,
             квартальные) → data/debt.csv; каждая строка несёт source_url
  render   — data/debt.csv → спарклайн (ASCII в README между маркерами
             + SVG data/debt_sparkline.svg); без временных меток:
             одинаковый вход → одинаковые байты
  selftest — двойная генерация идентична; схема csv: сортировка по дате,
             без дубликатов, у каждой строки источник; спарклайн из алфавита
             ▁▂▃▄▅▆▇█

Источник: https://fred.stlouisfed.org/series/GFDEBTN (Federal Reserve Bank
of St. Louis, FRED), выгрузка через открытый fredgraph.csv без ключей.
"""
import argparse
import csv
import io
import os
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_DIR = os.path.join(ROOT, "data")
CSV_PATH = os.path.join(DATA_DIR, "debt.csv")
SVG_PATH = os.path.join(DATA_DIR, "debt_sparkline.svg")
README_PATH = os.path.join(ROOT, "README.md")

SERIES_ID = "GFDEBTN"
SERIES_URL = f"https://fred.stlouisfed.org/series/{SERIES_ID}"
FETCH_URL = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={SERIES_ID}"

CSV_HEADER = ["date", "value_mln_usd", "series", "source_url"]
SPARK_CHARS = "▁▂▃▄▅▆▇█"
SPARK_WINDOW = 64  # последние 64 наблюдения (16 лет по кварталам)

BEGIN = "<!-- DEBT:BEGIN Волна ×4 · П47: генерится scripts/debt_thread.py render -->"
END = "<!-- DEBT:END -->"


# --- fetch -------------------------------------------------------------------

def fmt_value(raw: str) -> str:
    """Каноническая запись числа: целые без хвоста, дроби — 1 знак."""
    x = float(raw)
    return str(int(x)) if abs(x - round(x)) < 1e-9 else f"{x:.1f}"


def _http_get(url: str) -> bytes:
    """Живая выгрузка: сначала urllib (CI), при сбое — curl (песочницы с
    фильтрацией TLS-стека). Оба — std/системные, без ключей и зависимостей."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "red-thread-debt-audit/1.0"})
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.read()
    except OSError as e:  # timeout/SSL/прокси — пробуем системный curl
        print(f"ФАКТ: urllib не прошёл ({type(e).__name__}), фоллбек на curl", file=sys.stderr)
        import subprocess
        for attempt, extra in enumerate((["--http1.1"], []), 1):
            p = subprocess.run(["curl", "-s", "--max-time", "60", *extra, url],
                               capture_output=True)
            if p.returncode == 0 and p.stdout:
                return p.stdout
            print(f"ФАКТ: curl-попытка {attempt} rc={p.returncode}", file=sys.stderr)
        raise RuntimeError(f"выгрузка не удалась: urllib={e}")


def fetch_rows():
    """Живая выгрузка FRED → список строк csv (только валидные наблюдения)."""
    text = _http_get(FETCH_URL).decode("utf-8")
    rows = []
    for rec in csv.DictReader(io.StringIO(text)):
        val = (rec.get(SERIES_ID) or "").strip()
        date = (rec.get("observation_date") or "").strip()
        if not val or val == "." or not date:
            continue  # пропуски наблюдений не выдумываем: чего нет — нет
        rows.append((date, fmt_value(val)))
    return sorted(rows)


def write_csv(rows):
    os.makedirs(DATA_DIR, exist_ok=True)
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(CSV_HEADER)
    for date, val in rows:  # строки отсортированы; источник — у каждой
        w.writerow([date, val, SERIES_URL, SERIES_URL])
    with open(CSV_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(buf.getvalue())


# --- render ------------------------------------------------------------------

def read_csv(path=CSV_PATH):
    rows = []
    with open(path, encoding="utf-8", newline="") as f:
        for rec in csv.DictReader(f):
            if rec["date"]:
                rows.append((rec["date"], float(rec["value_mln_usd"]),
                             rec.get("source_url", "")))
    return rows


def sparkline(values, width=SPARK_WINDOW):
    """Юникод-спарклайн ▁▂▃▄▅▆▇█ по последним width наблюдениям."""
    tail = values[-width:]
    lo, hi = min(tail), max(tail)
    span = (hi - lo) or 1.0
    return "".join(SPARK_CHARS[min(7, int((v - lo) / span * 7.9999))] for v in tail)


def svg_sparkline(values, width=760, height=120):
    """SVG-полилиния спарклина (детерминированная, без шрифтов/дат-меток)."""
    tail = values[-SPARK_WINDOW:]
    lo, hi = min(tail), max(tail)
    span = (hi - lo) or 1.0
    pts = []
    n = len(tail)
    for i, v in enumerate(tail):
        x = 2 + i * (width - 4) / (n - 1)
        y = height - 6 - (v - lo) / span * (height - 12)
        pts.append(f"{x:.1f},{y:.1f}")
    last = tail[-1]
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="debt sparkline">\n'
        f'<polyline fill="none" stroke="#b91c1c" stroke-width="2" '
        f'points="{" ".join(pts)}"/>\n'
        f'<circle cx="{width - 2:.1f}" cy="{height - 6 - (last - lo) / span * (height - 12):.1f}" '
        f'r="3" fill="#b91c1c"/>\n</svg>\n'
    )


def render_readme(rows):
    """Блок README между маркерами: спарклайн + факт + источник. Без часов."""
    dates = [r[0] for r in rows]
    vals = [r[1] for r in rows]
    src = rows[-1][2] or SERIES_URL
    d0, d1 = dates[-2], dates[-1]
    v0, v1 = vals[-2], vals[-1]
    delta = v1 - v0
    lines = [
        BEGIN,
        "",
        f"**Долговая нить · {len(vals)} наблюдений · {dates[0]} → {d1}** "
        f"(Total Public Debt США, млн USD, квартал; источник каждой строки — [FRED {SERIES_ID}]({src})):",
        "",
        "```text",
        f"{d1[-7:]}  {sparkline(vals)}",
        "```",
        "",
        f"Последнее: **{v1:,.0f}** млн USD ({d1}); прирост за шаг: {delta:+,.0f} "
        f"({v0:,.0f} → {v1:,.0f}, {d0} → {d1}).",
        "",
        f"![debt sparkline](data/debt_sparkline.svg)",
        "",
        f"Данные: `data/debt.csv` ({len(vals)} строк, каждая с URL-источником); "
        f"генерация: `python3 scripts/debt_thread.py fetch && python3 scripts/debt_thread.py render`.",
        "",
        END,
    ]
    return "\n".join(lines)


def render(rows):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SVG_PATH, "w", encoding="utf-8", newline="") as f:
        f.write(svg_sparkline([r[1] for r in rows]))
    block = render_readme(rows)
    text = open(README_PATH, encoding="utf-8").read()
    if BEGIN in text and END in text:
        head = text[: text.index(BEGIN)]
        tail = text[text.index(END) + len(END):]
        text = head + block + tail
    else:
        text = text.rstrip("\n") + "\n\n" + block + "\n"
    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(text)


# --- selftest ----------------------------------------------------------------

def selftest():
    ok = True

    def need(cond, msg):
        nonlocal ok
        print(("✓ " if cond else "✗ ") + msg)
        ok = ok and bool(cond)

    rows = read_csv()
    need(len(rows) >= 24, f"csv содержит наблюдения: {len(rows)} строк")
    dates = [r[0] for r in rows]
    need(dates == sorted(dates) and len(set(dates)) == len(dates),
         "csv отсортирован по дате, без дубликатов")
    need(all(r[2].startswith("http") for r in rows),
         "каждая строка csv несёт URL-источник")
    need(all(len(r[0]) == 10 and r[0][4] == "-" for r in rows),
         "формат даты ISO (ГГГГ-ММ-ДД)")

    # двойная генерация идентична (без записи в README: чистые функции)
    b1 = render_readme(rows) + svg_sparkline([r[1] for r in rows])
    b2 = render_readme(rows) + svg_sparkline([r[1] for r in rows])
    need(b1 == b2, "двойная генерация спарклина/блока идентична байт в байт")
    sp = sparkline([r[1] for r in rows])
    need(sp and set(sp) <= set(SPARK_CHARS), "спарклайн из алфавита ▁▂▃▄▅▆▇█")
    # подмена данных меняет спарклайн (не рисуем константу); множитель на
    # всю серию не годится: min-max нормировка инвариантна к масштабу
    vals = [r[1] for r in rows]
    alt = vals[:-1] + [vals[-1] * 3]
    need(sparkline(alt) != sp, "изменение данных меняет спарклайн")
    # маркеры README на месте
    text = open(README_PATH, encoding="utf-8").read()
    need(BEGIN in text and END in text, "блок README между маркерами")
    print("SELFTEST:", "OK" if ok else "FAILED")
    return ok


def main():
    ap = argparse.ArgumentParser(description="Долговая нить как поток данных (П47)")
    ap.add_argument("mode", choices=["fetch", "render", "selftest"])
    args = ap.parse_args()
    if args.mode == "fetch":
        rows = fetch_rows()
        write_csv(rows)
        print(f"ФАКТ: data/debt.csv записан: {len(rows)} наблюдений, источник {SERIES_URL}")
        return 0
    if args.mode == "render":
        render(read_csv())
        print("ФАКТ: спарклайн SVG + блок README перегенерированы (детерминированно)")
        return 0
    return 0 if selftest() else 1


if __name__ == "__main__":
    sys.exit(main())
