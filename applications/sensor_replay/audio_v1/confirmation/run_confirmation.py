#!/usr/bin/env python3
"""Evaluate frozen panels on 18 previously unused complete MAFAULDA recordings.
The v1 training data, feature scaling and one-nearest-neighbor classifier stay fixed.
"""
import argparse,hashlib,importlib.util,json,pathlib,numpy as np
ROOT=pathlib.Path(__file__).resolve().parent;V1=ROOT.parent
H=lambda p:hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
p=json.loads((ROOT/'protocol.json').read_text());fr=json.loads((ROOT/'freeze_receipt.json').read_text())
assert H(ROOT/'protocol.json')==fr['protocol_sha256']
assert H(V1/'protocol.json')==p['training_protocol_sha256']
assert H(V1/'selection_snapshot.json')==p['v1_selection_snapshot_sha256']
assert H(V1/'results.json')==p['v1_results_sha256']
pa=argparse.ArgumentParser();pa.add_argument('--extract',action='store_true');a=pa.parse_args()
if a.extract:
 spec=importlib.util.spec_from_file_location('original_audio_features',V1/'run_audio_study.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);m.ROOT=ROOT;m.extract(p)
orig=np.load(V1/'features.npz',allow_pickle=False);data=np.load(ROOT/'features.npz',allow_pickle=False);model=np.load(V1/'model.npz',allow_pickle=False)
assert not set(orig['names']).intersection(set(data['names']))
tr=model['train_rows'];mu=model['mean'];sd=model['std']
assert np.array_equal(mu,orig['X'][tr].mean(axis=0)) and np.array_equal(sd,np.maximum(orig['X'][tr].std(axis=0),1e-9))
T=(orig['X'][tr]-mu)/sd;Q=(data['X']-mu)/sd
truth=data['y'];result={}
for label,mask in p['locked_panels'].items():
 cs=[i for i in range(7) if mask>>i&1];tf=T[:,cs,:].reshape(len(tr),-1);qf=Q[:,cs,:].reshape(len(truth),-1)
 pred=orig['y'][tr][np.argmin(((qf[:,None,:]-tf[None,:,:])**2).sum(axis=-1),axis=1)]
 recalls=[float(np.mean(pred[truth==k]==k)) for k in range(3)]
 result[label]={'mask':mask,'channels':[p['diagnostic_channels'][i] for i in cs],'cost':len(cs),'balanced_accuracy':float(np.mean(recalls)),'class_recall':recalls,'correct':int(np.sum(pred==truth)),'n':len(truth),'predictions':pred.tolist(),'labels':truth.tolist(),'confusion_matrix':[[int(np.sum((truth==k)&(pred==l))) for l in range(3)] for k in range(3)]}
r={'protocol_sha256':H(ROOT/'protocol.json'),'freeze_receipt_sha256':H(ROOT/'freeze_receipt.json'),'original_model_sha256':H(V1/'model.npz'),'features_sha256':H(ROOT/'features.npz'),'script_sha256':H(__file__),'records':data['names'].tolist(),'n_confirmation_recordings':len(truth),'original_recording_overlap':0,'panels_fixed_before_new_data':True,'training_unchanged':True,'results':result,'tie_union_minus_full_balanced_accuracy':result['tie_preserving_union']['balanced_accuracy']-result['full']['balanced_accuracy'],'channel_count_reduction_fraction':1-result['tie_preserving_union']['cost']/7,'limitations':p['limitations']}
(ROOT/'results.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:{'cost':v['cost'],'balanced_accuracy':v['balanced_accuracy'],'correct':v['correct'],'n':v['n']} for k,v in result.items()},indent=2))
