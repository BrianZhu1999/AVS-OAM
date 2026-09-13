"""Verify scientific correspondences and local asset links before publishing."""
import csv
import hashlib
import itertools
import json
import re
from pathlib import Path

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/'docs'; DATA=SITE/'data'
OBS=['pressure_only','pressure_plus_vx_vy','pressure_plus_vx_vy_vz']
checks={}
manifest=json.loads((DATA/'source_manifest.json').read_text())
for name,sha in manifest['public_checksums'].items():
    assert hashlib.sha256((DATA/name).read_bytes()).hexdigest()==sha,name
checks['data_checksums']=len(manifest['public_checksums'])
source_rows=0
for name in ['snr','offset_nominal','offset_calibrated','distance','pilots','hardware']:
    rows=list(csv.DictReader((DATA/f'{name}.csv').open(encoding='utf-8-sig')))
    exported=json.loads((DATA/f'{name}.json').read_text())
    assert len(rows)==len(exported)
    for r,web in zip(rows,exported):
        for k,v in r.items():
            try: expected=float(v)
            except ValueError:expected=v
            assert expected==web[k],(name,k)
        nstreams=2 if r['active_set_id']=='two_stream_pm1' else 4
        denom=float(r['bit_total']) if 'bit_total' in r else float(r['n_data_frames_per_repeat'])*nstreams
        errors=float(r.get('bit_errors',r.get('n_bit_errors')))
        assert abs(errors/denom-float(r['BER']))<1e-12,(name,r)
        assert float(r['BER'])==0 or float(r['BER'])>=1e-6
    source_rows+=len(rows)
checks['performance_rows_match_csv_and_error_rates']=source_rows
raw=np.load(DATA/'receiver_matrix.npz')['raw']
symbols=np.array(list(itertools.product([-1,1],repeat=4)))
archived=json.loads((DATA/'codewords.json').read_text())
maxerr=0
for k,n in enumerate([1,3,4]):
    a=raw[:n*5].copy();a/=np.linalg.norm(a,axis=0);a[5:]*=np.sqrt(3)
    words=symbols@a.T
    d2=np.sum(abs(words[:,None]-words[None,:])**2,axis=2)
    err=np.max(abs(d2-np.array(archived['views'][k]['d2'])))
    assert err<1e-10,err
    maxerr=max(maxerr,float(err))
checks['max_full_space_distance_error']=maxerr
payload=np.load(DATA/'payload.npz');metrics=list(csv.DictReader((DATA/'payload_metrics.csv').open(encoding='utf-8-sig')))
counts=[]
for obs in OBS:
    err=payload[obs]!=payload['original'];r=next(r for r in metrics if r['observation_mode']==obs)
    assert int(err.sum())==int(r['bit_errors'])
    assert abs(float(err.mean())-float(r['BER']))<1e-14
    counts.append(int(err.sum()))
checks['payload_bit_errors']=counts
html=(SITE/'index.html').read_text(encoding='utf-8')
assert '<html lang="en">' in html
assert not re.search('[\u4e00-\u9fff]',html)
for link in re.findall(r'(?:href|src)="([^"]+)"',html):
    if link.startswith(('https:','#')):continue
    assert (SITE/link).is_file(),link
gallery=json.loads((DATA/'gallery.json').read_text())
assert len(gallery)==15
for r in gallery:assert (SITE/r['image']).is_file()
checks['gallery_figures']=len(gallery)
print(json.dumps(checks,indent=2))
