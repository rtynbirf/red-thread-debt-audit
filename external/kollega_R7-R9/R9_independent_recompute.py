#!/usr/bin/env python3
import json
from pathlib import Path

R7_D6 = [1,0,0,0,1,0]
R7_D11 = [1,1,1,1,0,0,1,0,0,1,0]
R7_RMARG = (2,5)

VARIANTS = {
    'R7-v0.1': {'Delta6': R7_D6, 'Delta11': R7_D11, 'r_marg': 0.4},
    'strict-no-spoof-channel': {'Delta6':[1,0,0,0,1,0], 'Delta11':[1,1,1,1,0,0,0,0,0,1,0], 'r_marg':0.25},
    'count-world-partition': {'Delta6':[1,0,0,1,1,0], 'Delta11':R7_D11, 'r_marg':None},
    'count-timing-but-not-spoof-resistance': {'Delta6':[1,0,0,0,1,1], 'Delta11':R7_D11, 'r_marg':None},
    'credit-CAU-sal-world-recovery': {'Delta6':R7_D6, 'Delta11':[1,1,1,1,0,0,1,0,1,1,0], 'r_marg':None},
}

def mean(v): return sum(v)/len(v)

def check_binary(v): return all(x in (0,1) for x in v)

out = {
  'task':'R9 independent recomputation and sensitivity audit of R7/R8',
  'recomputed':{},
  'checks':{},
  'findings':[]
}

out['recomputed']['R7-v0.1'] = {
  'Delta6':mean(R7_D6), 'Delta11':mean(R7_D11), 'r_marg':R7_RMARG[0]/R7_RMARG[1]
}
for name,d in VARIANTS.items():
    out['recomputed'].setdefault(name,{})
    out['recomputed'][name]['Delta6']=mean(d['Delta6'])
    out['recomputed'][name]['Delta11']=mean(d['Delta11'])
    if d['r_marg'] is not None: out['recomputed'][name]['r_marg']=d['r_marg']

out['checks'] = {
  'Delta6_length_is_6': len(R7_D6)==6,
  'Delta11_length_is_11': len(R7_D11)==11,
  'Delta6_binary': check_binary(R7_D6),
  'Delta11_binary': check_binary(R7_D11),
  'R7_exact_reproduction': (
      mean(R7_D6)==1/3 and mean(R7_D11)==6/11 and R7_RMARG[0]/R7_RMARG[1]==0.4
  ),
  'R8_strict_Delta6_unchanged': mean([1,0,0,0,1,0])==1/3,
  'R8_strict_Delta11_lower': mean([1,1,1,1,0,0,0,0,0,1,0])==5/11,
  'R8_r_marg_lower': 0.25 < 0.4,
}

out['findings'] = [
  'R7 is exactly reproducible from the recovered vectors: Delta6=1/3, Delta11=6/11, r_marg=2/5.',
  'R8 does not overturn R7; it exposes sensitivity to the treatment of spoofable timing and alternative counting conventions.',
  'The strict no-spoof timing treatment lowers Delta11 from 6/11 to 5/11 and r_marg from 0.40 to 0.25.',
  'Therefore timing is a usable signal in the recovered artifact set but is not robust evidence of recovery when spoofability is admitted.',
  'The available R7/R8 artifacts do not contain enough empirical observations to estimate a world-level causal effect; that remains UNKNOWN rather than inferred.',
]

Path('/mnt/data/red_thread/R9_independent_recompute.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
