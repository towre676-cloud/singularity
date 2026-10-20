#!/usr/bin/env python3
"""Reproducible 24-recording MAFAULDA channel-selection replay.

Run python run_audio_study.py --extract to verify source members/extract features,
then python run_audio_study.py. With shipped features no raw data is required.
No training/test windows from one recording are separated. No tachometer features.
"""
from __future__ import annotations
import argparse,hashlib,io,json,pathlib,time,zlib
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parent

def digest(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(name,obj):
 p=ROOT/name;p.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n');return p

def extract(protocol):
 from scipy.signal import welch
 acquisition_path=ROOT/protocol['source_acquisition']
 acq=json.loads(acquisition_path.read_text()); base=acquisition_path.parent
 features=[];ys=[];grids=[];names=[];receipts=[]
 bands=protocol['features']['bands_hz']
 for row in acq['records']:
  raw=zlib.decompress((base/row['compressed_path']).read_bytes(),-15)
  if hashlib.sha256(raw).hexdigest()!=row['raw_sha256']:raise ValueError('raw hash mismatch')
  a=np.loadtxt(io.BytesIO(raw),delimiter=',')
  if a.shape!=(250000,8):raise ValueError(f'unexpected shape {a.shape}')
  x=a[:,1:] # tachometer is column zero, never used by the diagnostic
  centered=x-x.mean(axis=0)
  rms=np.sqrt(np.mean(centered**2,axis=0));meanabs=np.mean(np.abs(centered),axis=0)
  kurt=np.mean(centered**4,axis=0)/np.maximum(rms**4,1e-20)
  crest=np.max(np.abs(centered),axis=0)/np.maximum(rms,1e-20)
  crossing=np.mean(centered[:-1]*centered[1:]<0,axis=0)
  f,p=welch(centered,fs=50000,nperseg=4096,noverlap=2048,axis=0)
  centroid=(f[:,None]*p).sum(axis=0)/np.maximum(p.sum(axis=0),1e-20)/25000
  bp=np.stack([np.log10(np.maximum(p[(f>=lo)&(f<hi)].sum(axis=0)*(f[1]-f[0]),1e-20)) for lo,hi in bands],axis=1)
  desc=np.stack([np.log10(np.maximum(rms,1e-20)),np.log10(np.maximum(meanabs,1e-20)),kurt,crest,crossing,centroid],axis=1)
  features.append(np.concatenate([desc,bp],axis=1));ys.append(protocol['states'].index(row['state']));grids.append(row['grid_index']);names.append(row['name'])
  receipts.append({k:row[k] for k in ['name','state','grid_index','speed_target_hz','speed_from_filename_hz','raw_sha256','compressed_sha256','archive_url','header','compressed','crc32']})
  print('features',row['name'],flush=True)
 np.savez_compressed(ROOT/'features.npz',X=np.array(features),y=np.array(ys),grid=np.array(grids),names=np.array(names))
 save('feature_provenance.json',{'protocol_sha256':digest(ROOT/'protocol.json'),'source_receipt_sha256':digest(acquisition_path),'shape':[24,7,14],'channels':protocol['diagnostic_channels'],'raw_member_receipts':receipts,'features_sha256':digest(ROOT/'features.npz')})

def score(y,p):
 recalls=[float(np.mean(p[y==k]==k)) for k in [0,1,2]]
 cm=[[int(np.sum((y==k)&(p==l))) for l in [0,1,2]] for k in [0,1,2]]
 return {'balanced_accuracy':float(np.mean(recalls)),'accuracy':float(np.mean(y==p)),'class_recall':recalls,'confusion_matrix':cm,'n':len(y),'correct':int(np.sum(y==p)),'predictions':p.tolist(),'labels':y.tolist()}

def rows_for(grid,inds):return np.flatnonzero(np.isin(grid,inds))
def mask_channels(mask):return [i for i in range(7) if mask>>i&1]
def predict_distances(D,ytrain,mask):
 return ytrain[np.argmin(D[:,mask_channels(mask),:].mean(axis=1),axis=1)]

def run(protocol):
 freeze=json.loads((ROOT/'freeze_receipt.json').read_text())
 assert freeze['protocol_sha256']==digest(ROOT/'protocol.json')
 data=np.load(ROOT/'features.npz',allow_pickle=False);X=data['X'];y=data['y'];grid=data['grid'];names=data['names']
 split={k:rows_for(grid,v) for k,v in protocol['splits_grid_indices'].items()}
 assert len(set(split['train'])&set(split['selection']))==0 and len(set(split['train'])&set(split['test']))==0 and len(set(split['selection'])&set(split['test']))==0
 train=split['train'];mu=X[train].mean(axis=0);sd=np.maximum(X[train].std(axis=0),1e-9)
 Z=(X-mu)/sd
 # Per-query/per-channel/per-reference distances, with no test information in fitting.
 D={k:((Z[inds,:,None,:]-Z[train].transpose(1,0,2)[None,:,:,:])**2).mean(axis=-1) for k,inds in split.items() if k!='train'}
 selection_table=[];ts=time.perf_counter()
 for mask in range(1,128):
  p=predict_distances(D['selection'],y[train],mask)
  s=score(y[split['selection']],p)
  selection_table.append(dict(mask=mask,cost=mask.bit_count(),channels=[protocol['diagnostic_channels'][i] for i in mask_channels(mask)],**s))
 full=selection_table[126];threshold=max(0.,full['balanced_accuracy']-.02)
 feasible=[r for r in selection_table if r['balanced_accuracy']>=threshold-1e-12]
 exact=min(feasible,key=lambda r:(r['cost'],r['mask']))
 g=0;steps=[]
 while not g or selection_table[g-1]['balanced_accuracy']<threshold-1e-12:
  options=[selection_table[(g|1<<i)-1] for i in range(7) if not (g>>i&1)]
  best=min(options,key=lambda r:(-r['balanced_accuracy'],r['mask']));g=best['mask'];steps.append(g)
 pruned=min([r for r in feasible if r['mask']&g==r['mask']],key=lambda r:(r['cost'],r['mask']))
 snapshot={'protocol_sha256':digest(ROOT/'protocol.json'),'features_sha256':digest(ROOT/'features.npz'),'script_sha256':digest(__file__),'training_rows':train.tolist(),'selection_rows':split['selection'].tolist(),'selection_threshold':threshold,'full_selection':full,'exact_selection':exact,'greedy_selection':selection_table[g-1],'pruned_greedy_selection':pruned,'greedy_steps':steps,'all_selection_masks':selection_table,'selection_seconds':time.perf_counter()-ts,'optimality':{'enumerated_nonempty_masks':127,'feasible_masks':len(feasible),'minimum_cost':exact['cost'],'no_lower_cost_feasible_mask':not any(r['cost']<exact['cost'] for r in feasible),'all_minimum_cost_masks':[r['mask'] for r in feasible if r['cost']==exact['cost']]},'test_metrics_not_yet_evaluated':True}
 save('selection_snapshot.json',snapshot)
 selected={'full':127,'exact':exact['mask'],'greedy':g,'pruned_greedy':pruned['mask'],'microphone_only':64,'all_accelerometers':63}
 results={name:dict(mask=m,channels=[protocol['diagnostic_channels'][i] for i in mask_channels(m)],cost=m.bit_count(),**score(y[split['test']],predict_distances(D['test'],y[train],m))) for name,m in selected.items()}
 # Exhaustive same-cardinality reference distribution is descriptive, never used to select the reported mask.
 same=[]
 for mask in range(1,128):
  if mask.bit_count()==exact['cost']:
   same.append({'mask':mask,**score(y[split['test']],predict_distances(D['test'],y[train],mask))})
 vals=np.array([r['balanced_accuracy'] for r in same])
 result={'protocol_sha256':digest(ROOT/'protocol.json'),'selection_snapshot_sha256':digest(ROOT/'selection_snapshot.json'),'features_sha256':digest(ROOT/'features.npz'),'script_sha256':digest(__file__),'source_page':protocol['source_page'],'n_recordings':len(y),'splits':{k:{'rows':v.tolist(),'recordings':names[v].tolist(),'count':len(v)} for k,v in split.items()},'selection_threshold':threshold,'results':results,'same_cardinality_unselected_reference':{'cost':exact['cost'],'number_of_masks':len(same),'min':float(vals.min()),'median':float(np.median(vals)),'mean':float(vals.mean()),'max':float(vals.max()),'all_masks':same},'channel_count_reduction_fraction':1-exact['cost']/7,'limitations':protocol['limitations']}
 save('results.json',result)
 np.savez_compressed(ROOT/'model.npz',train_rows=train,mean=mu,std=sd)
 print(json.dumps({'selection_threshold':threshold,'results':{k:{'cost':v['cost'],'balanced_accuracy':v['balanced_accuracy'],'channels':v['channels']} for k,v in results.items()}},indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--extract',action='store_true');a=p.parse_args();protocol=json.loads((ROOT/'protocol.json').read_text())
 if a.extract:extract(protocol)
 run(protocol)
