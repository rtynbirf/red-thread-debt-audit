#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
РАУНД 14 / R10 — БЛОК A: независимая верификация входа коллеги (R7/R8/R9).
Вердикт-рамка объявлена ДО прогона (см. отчёт раунда):

  VA1  R7 воспроизводим бит в бит из сохранённых векторов:
       Delta6 = 1/3, Delta11 = 6/11, r_marg = 2/5.
  VA2  ПОЛНЫЙ перебор вариантов R8 (коллега в R9 пересчитал только strict):
       Delta6: R7-v0.1=1/3, strict=1/3, count-world-partition=1/2,
               count-timing-but-not-spoof-resistance=1/2
       Delta11: R7=6/11, strict=5/11, credit_CAU_sal_world_recovery=7/11
       r_marg: 0.40 / 0.25.
  VA3  Кросс-согласованность R7<->R8: каждое source_facts бьётся битом chain11:
       axes_survive=3 <-> биты[1:4]=1,1,1
       contact_content=0 <-> бит[4]=0;  contact_perfect_probe=0 <-> бит[5]=0
       contact_timing=1 <-> бит[6]=1;   timing_spoofable=1 <-> бит[7]=0
       causal_foreign_coverage=0 <-> бит[8]=0; law_partition=1 <-> бит[9]=1
       coherence_self_recovery=0 <-> бит[10]=0
       strict-вариант обязан гасить именно бит[6] (timing channel) и ничего более.
  VA4  strict-штраф измерим: доля потерянных единиц доказательства
       Delta11: (6-5)/6 = 16.7%; r_marg: (0.40-0.25)/0.40 = 37.5%.
       (перенос в реальный слой — Блок B: DebtService strict vs номинал)

Дисциплина: числа только из сохранённых JSON коллеги; ничего не выдумывается;
канонические обозначения слотов Delta6 в корпусе ОТСУТСТВУЮТ (canonical_notation_found
= false) — семантика слотов помечается UNKNOWN, арифметика верифицируется как есть.
"""
import json
import hashlib
from fractions import Fraction
from pathlib import Path

SRC = Path('/home/z/my-project/upload/zip_extract/r7r8r9')
OUT = Path('/home/z/my-project/download/R10_верификация_R7R8R9.json')

def sha256(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

r7 = json.loads((SRC / 'R7_delta_audit.json').read_text(encoding='utf-8'))
r8 = json.loads((SRC / 'R8_robustness_audit.json').read_text(encoding='utf-8'))
r9 = json.loads((SRC / 'R9_independent_recompute.json').read_text(encoding='utf-8'))

res = {
    'task': 'R10 cross-layer verification of colleague R7/R8/R9',
    'inputs': {
        'R7_delta_audit.json': sha256(SRC / 'R7_delta_audit.json'),
        'R8_robustness_audit.json': sha256(SRC / 'R8_robustness_audit.json'),
        'R9_independent_recompute.json': sha256(SRC / 'R9_independent_recompute.json'),
        'r7_delta_audit.py': sha256(SRC / 'r7_delta_audit.py'),
        'R9_independent_recompute.py': sha256(SRC / 'R9_independent_recompute.py'),
        'archive_zip': sha256('/home/z/my-project/upload/RED_THREAD_R7_R8_R9_AUDIT.zip'),
        'R9_REPORT_md': sha256('/home/z/my-project/upload/R9_REPORT.md'),
    },
    'verdicts': {},
    'details': {},
}

# ---------- VA1: R7 бит в бит ----------
d6 = r7['Delta6']['vector']
d11 = r7['Delta11']['vector']
rm = r7['r_marg']
va1 = (Fraction(sum(d6), len(d6)) == Fraction(1, 3)
       and Fraction(sum(d11), len(d11)) == Fraction(6, 11)
       and Fraction(rm['numerator'], rm['denominator']) == Fraction(2, 5)
       and len(d6) == 6 and len(d11) == 11
       and all(x in (0, 1) for x in d6 + d11))
res['verdicts']['VA1_R7_exact'] = 'ПОДТВЕРЖДЕНА' if va1 else 'ОТКЛОНЕНА'
res['details']['VA1'] = {'Delta6': str(Fraction(sum(d6), len(d6))),
                         'Delta11': str(Fraction(sum(d11), len(d11))),
                         'r_marg': f"{rm['numerator']}/{rm['denominator']}"}

# ---------- VA2: полный перебор R8 ----------
exp6 = {'R7-v0.1': Fraction(1, 3), 'strict-no-spoof-channel': Fraction(1, 3),
        'count-world-partition': Fraction(1, 2),
        'count-timing-but-not-spoof-resistance': Fraction(1, 2)}
exp11 = {'R7-v0.1': Fraction(6, 11), 'strict_no_spoofable_timing': Fraction(5, 11),
         'credit_CAU_sal_world_recovery': Fraction(7, 11)}
# E12: повторяющиеся десятичные (6/11 и пр.) нельзя сверять через округление до 1e9 —
# только точная дробь вектора + допуск 1e-9 к записанному float.
def close(frac, val, tol=1e-9):
    return abs(float(frac) - float(val)) < tol

ok2, det2 = True, {'Delta6': {}, 'Delta11': {}, 'r_marg': {}}
for name, vec in r8['Delta6_variants'].items():
    got = Fraction(sum(vec['vector']), len(vec['vector']))
    det2['Delta6'][name] = str(got)
    ok2 &= (got == exp6[name] and close(got, vec['value']))
for name, vec in r8['Delta11'].items():
    got = Fraction(sum(vec['vector']), len(vec['vector']))
    det2['Delta11'][name] = str(got)
    ok2 &= (got == exp11[name] and close(got, vec['value']))
rm8 = r8['r_marg']
ok2 &= close(Fraction(2, 5), rm8['R7-v0.1'])
ok2 &= close(Fraction(1, 4), rm8['strict_non_spoofable'])
det2['r_marg'] = {'R7-v0.1': '2/5', 'strict_non_spoofable': '1/4'}
res['verdicts']['VA2_R8_full_enumeration'] = 'ПОДТВЕРЖДЕНА' if ok2 else 'ОТКЛОНЕНА'
res['details']['VA2'] = det2

# ---------- VA3: кросс-согласованность R7<->R8 ----------
c11 = r7['chain11']
bits = [b for _, b in c11]
maps = [
    ('axes_survive=3', sum(bits[1:4]) == 3),
    ('contact_content=0', bits[4] == 0),
    ('contact_perfect_probe=0', bits[5] == 0),
    ('contact_timing=1', bits[6] == 1),
    ('timing_spoofable=1 (resistance failed)', bits[7] == 0),
    ('causal_foreign_coverage=0', bits[8] == 0),
    ('causal_law_partition=1', bits[9] == 1),
    ('coherence_self_recovery=0', bits[10] == 0),
]
strict = r8['Delta11']['strict_no_spoofable_timing']['vector']
only_timing_died = all(strict[i] == bits[i] for i in range(len(bits)) if i != 6) and strict[6] == 0
va3 = all(v for _, v in maps) and only_timing_died and len(c11) == 11
res['verdicts']['VA3_cross_consistency'] = 'ПОДТВЕРЖДЕНА' if va3 else 'ОТКЛОНЕНА'
res['details']['VA3'] = {'mappings': {k: v for k, v in maps},
                         'strict_kills_only_bit6_timing_channel': only_timing_died}

# ---------- VA4: strict-штраф ----------
p11 = Fraction(6, 11)  # не используется в штрафе; штраф = по числу единиц
lost11 = Fraction(6 - 5, 6)
lostrm = Fraction(40 - 25, 40)
res['details']['VA4'] = {
    'strict_penalty_Delta11_ones': f'{lost11} = {float(lost11):.4f}',
    'strict_penalty_r_marg': f'{lostrm} = {float(lostrm):.4f}',
    'note': 'spoofable-канал несёт 1 из 6 единиц Delta11 и 1 из 2 маргинальных восстановлений r_marg',
}
res['verdicts']['VA4_strict_penalty_measured'] = 'ЗАФИКСИРОВАН'

# ---------- VA5: согласованность с R9 коллеги ----------
r9rep = r9['recomputed']['R7-v0.1']
va5 = (abs(r9rep['Delta6'] - 1/3) < 1e-12 and abs(r9rep['Delta11'] - 6/11) < 1e-12
       and abs(r9rep['r_marg'] - 0.4) < 1e-12)
res['verdicts']['VA5_colleague_R9_reproduction'] = 'ПОДТВЕРЖДЕНА' if va5 else 'ОТКЛОНЕНА'

# ---------- эпистемический статус ----------
res['error_register_E12'] = ('сравнение повторяющихся десятичных дробей через round(x*1e9) '
                             'ложно роняет VA2; инструмент верификации обязан сверять точную '
                             'дробь с допуском 1e-9 (первый прогон дал ложное ОТКЛОНЕНА — '
                             'исправлено до публикации выводов, промах инструмента ≠ промах данных)')

res['epistemic'] = {
    'FACT': 'сохранённые векторы/JSON коллеги, их арифметика, 9 кросс-отображений',
    'CALCULATED': 'strict-штраф: Delta11 -1/6 единиц, r_marg -37.5%',
    'MODEL': ('топологический перенос: spoofable timing (коллега) ~ фиктивная ie в дефолте '
              '(v0.2) — канал даёт сигнал, не является доказательством при управляемости'),
    'UNKNOWN': ('семантика слотов Delta6 (canonical_notation_found=false); '
                'general_minimality (согласовано с R8); мировая причинность (0/8)'),
}

OUT.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(res['verdicts'], ensure_ascii=False, indent=2))
print('saved:', OUT)
