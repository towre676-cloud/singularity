#!/usr/bin/env python3
"""Independent feature-level replay using masked flattened Euclidean vectors.
Does not call the study's decomposed-distance classifier or optimization functions.
"""
import hashlib,itertools,json,pathlib,numpy as np
ROOT=pathlib.Path(__file__).resolve().parent
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(name):return json.loads((ROOT/name).read_text())
p=load('protocol.json');fr=load('freeze_receipt.json');snap=load('selection_snapshot.json');r=load('results.json');prov=load('feature_provenance.json')
assert H(ROOT/'protocol.json')==fr['protocol_sha256']==snap['protocol_sha256']==r['protocol_sha256']==prov['protocol_sha256']
assert H(ROOT/'features.npz')==snap['features_sha256']==r['features_sha256']==prov['features_sha256']
assert H(ROOT/'selection_snapshot.json')==r['selection_snapshot_sha256']
a=np.load(ROOT/'features.npz',allow_pickle=False);X=a['X'];y=a['y'];grid=a['grid']
inds={k:np.array([i for i,g in enumerate(grid) if int(g) in gs]) for k,gs in p['splits_grid_indices'].items()}
assert all(not set(inds[k]).intersection(inds[l]) for k,l in itertools.combinations(inds,2))
mean=X[inds['train']].mean(axis=0);std=np.maximum(X[inds['train']].std(axis=0),1e-9);Z=(X-mean)/std

def independent(mask,key):
 channels=[i for i in range(7) if (mask>>i)&1]
 tr=Z[inds['train']][:,channels,:].reshape(len(inds['train']),-1)
 predictions=[]
 for row in Z[inds[key]][:,channels,:].reshape(len(inds[key]),-1):
  distances=np.array([np.dot(row-ref,row-ref) for ref in tr]);j=int(np.argmin(distances));predictions.append(int(y[inds['train'][j]]))
 return predictions
rows=[]
for k in range(1,8):
 for comb in itertools.combinations(range(7),k):
  mask=sum(1<<i for i in comb);pred=np.array(independent(mask,'selection'));truth=y[inds['selection']]
  ba=np.mean([np.mean(pred[truth==c]==c) for c in range(3)])
  saved=snap['all_selection_masks'][mask-1]
  assert saved['mask']==mask and saved['predictions']==pred.tolist() and abs(saved['balanced_accuracy']-ba)<1e-12
  if ba>=r['selection_threshold']-1e-12:rows.append((k,mask))
assert min(rows)==(snap['exact_selection']['cost'],snap['exact_selection']['mask'])
for name,z in r['results'].items():assert z['predictions']==independent(z['mask'],'test')
report={'passed':True,'all_127_selection_masks_recomputed':True,'minimum_cost_independently_reproduced':True,'all_reported_test_predictions_recomputed':True,'split_disjointness':True,'protocol_sha256':H(ROOT/'protocol.json'),'features_sha256':H(ROOT/'features.npz'),'independent_method':'masked flattened training-standardized Euclidean vectors; itertools combinations; no import from run_audio_study'}
(ROOT/'independent_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
