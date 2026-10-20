#!/usr/bin/env python3
"""Independent decomposed-channel replay of all locked confirmation panels."""
import hashlib,json,pathlib,numpy as np
ROOT=pathlib.Path(__file__).resolve().parent;V1=ROOT.parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((ROOT/'protocol.json').read_text());f=json.loads((ROOT/'freeze_receipt.json').read_text());r=json.loads((ROOT/'results.json').read_text());s=json.loads((V1/'selection_snapshot.json').read_text())
assert H(ROOT/'protocol.json')==f['protocol_sha256']==r['protocol_sha256']
assert H(V1/'results.json')==p['v1_results_sha256'] and H(V1/'selection_snapshot.json')==p['v1_selection_snapshot_sha256']
assert H(ROOT/'features.npz')==r['features_sha256']
old=np.load(V1/'features.npz',allow_pickle=False);new=np.load(ROOT/'features.npz',allow_pickle=False)
assert len(new['y'])==18 and not set(old['names']).intersection(set(new['names']))
tr=np.array([i for i,g in enumerate(old['grid']) if int(g) in [0,2,4,6]])
mu=old['X'][tr].mean(axis=0);sd=np.maximum(old['X'][tr].std(axis=0),1e-9)
zt=(old['X'][tr]-mu)/sd;zq=(new['X']-mu)/sd
best=max(v['balanced_accuracy'] for v in s['all_selection_masks'] if v['cost']==1)
ties=[v['mask'] for v in s['all_selection_masks'] if v['cost']==1 and abs(v['balanced_accuracy']-best)<1e-12]
union=0
for m in ties:union|=m
assert union==p['locked_panels']['tie_preserving_union'] and ties==p['all_development_optimal_singletons']
D=np.zeros((len(zq),7,len(tr)))
for i in range(len(zq)):
 for ch in range(7):
  for j in range(len(tr)):D[i,ch,j]=np.mean((zq[i,ch]-zt[j,ch])**2)
for name,mask in p['locked_panels'].items():
 cs=[i for i in range(7) if mask>>i&1]
 pred=old['y'][tr][np.argmin(np.mean(D[:,cs,:],axis=1),axis=1)]
 assert pred.tolist()==r['results'][name]['predictions']
 truth=new['y'];cm=[[int(np.sum((truth==k)&(pred==l))) for l in range(3)] for k in range(3)]
 assert cm==r['results'][name]['confusion_matrix']
report={'passed':True,'all_frozen_panel_predictions_reproduced':True,'original_train_only_scaling_recomputed':True,'new_recording_disjointness_checked':True,'tie_union_rule_independently_recomputed':True,'protocol_sha256':H(ROOT/'protocol.json'),'features_sha256':H(ROOT/'features.npz'),'method':'triple-loop per-channel squared distances; no import of either study runner'}
(ROOT/'independent_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
