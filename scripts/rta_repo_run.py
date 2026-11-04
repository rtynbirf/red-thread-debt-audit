#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
rta_repo_run.py — мост запуска опубликованных скриптов Красной Нити из клона репо.

Опубликованные скрипты (download/*.py, scripts/rta_*.py, scripts/r10_crosslayer_verify.py)
не модифицируются — генеалогия вербатим. Они были написаны в песочнице с корнем
/home/z/my-project; этот мост читает целевой скрипт, ЯВНО подставляет корень репо
(и пути входов коллег из external/), компилирует в памяти и исполняет.

Использование:
    python3 scripts/rta_repo_run.py scripts/rta_r10_matrix.py [аргументы…]
    python3 scripts/rta_repo_run.py download/КОЛЬЦО-1_v8_переходная_зона.py

Идемпотентность: перезапись выходов в download/ ожидаема и безопасна.
"""
import pathlib
import re
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
SANDBOX = '/home/z/my-project'

# Явная карта подстановок: частные случаи (входы коллег) длиннее общего корня
# и потому выигрывают в однопроходной альтернации; двойная подстановка невозможна.
_REPLACEMENTS = [
    (f'{SANDBOX}/upload/zip_extract/r7r8r9', str(REPO / 'external' / 'kollega_R7-R9')),
    (f'{SANDBOX}/upload/RED_THREAD_R7_R8_R9_AUDIT.zip',
     str(REPO / 'external' / 'origin' / 'RED_THREAD_R7_R8_R9_AUDIT.zip')),
    (f'{SANDBOX}/upload/R9_REPORT.md', str(REPO / 'external' / 'kollega_R7-R9' / 'R9_REPORT.md')),
    (SANDBOX, str(REPO)),
]
_RE = re.compile('|'.join(re.escape(old) for old, _ in _REPLACEMENTS))
_MAP = dict(_REPLACEMENTS)


def _substitute(text: str) -> str:
    return _RE.sub(lambda m: _MAP[m.group(0)], text)


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    target = (REPO / sys.argv[1]).resolve()
    if not target.is_file():
        print(f'НЕТ ФАЙЛА: {target}')
        return 2
    if REPO not in target.parents and target.parent != REPO:
        print(f'Цель вне репо: {target}')
        return 2
    src = target.read_text(encoding='utf-8')
    src = _substitute(src)
    code = compile(src, str(target), 'exec')
    glob = {'__name__': '__main__', '__file__': str(target)}
    sys.argv = [str(target)] + sys.argv[2:]
    try:
        exec(code, glob)  # noqa: S102 — исполнение вербатим-скрипта с явной подстановкой корня
    except SystemExit as e:  # скрипты могут вызывать sys.exit
        return int(e.code or 0)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
