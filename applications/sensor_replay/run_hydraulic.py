#!/usr/bin/env python3
"""Frozen, group-held-out sensor replay; optional numpy/scikit-learn dependencies.

Exact selection is over a fixed classifier's finite selection-set accuracy table.
It is not a proof of physical observability, intervention benefit or field accuracy.
"""
from __future__ import annotations
import argparse, hashlib, itertools, json, math, os, platform, sys, time, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
import numpy as np

SENSORS = ['PS1','PS2','PS3','PS4','PS5','PS6','EPS1','FS1','FS2','TS1','TS2','TS3','TS4','VS1']
RATES = [100]*7+[10]*2+[1]*5
TASKS = ['cooler','valve','pump','accumulator']
URL = 'https://archive.ics.uci.edu/static/public/447/condition+monitoring+of+hydraulic+systems.zip'
ARCHIVE_SHA256 = '24128aad2ee45eea7e6b63ebbd9992cdf25d0483a2cebefbfc13bc69079af1f2'
SEED = 20261019

def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path, value):
    Path(path).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
def stamp(): return datetime.now(timezone.utc).isoformat()
def ids(mask): return [i for i in range(14) if mask>>i&1]
def cost(mask): return (int(mask).bit_count(), sum(60*RATES[i] for i in ids(mask)), int(mask))
def names(mask): return [SENSORS[i] for i in ids(mask)]

def download(path):
    if not path.exists():
        path.parent.mkdir(parents=True,exist_ok=True)
        with urllib.request.urlopen(URL,timeout=120) as r, path.open('wb') as f:
            while b:=r.read(1024*1024): f.write(b)
    if digest(path)!=ARCHIVE_SHA256: raise ValueError('Official archive digest changed; freeze a separate study.')

def freeze(archive, out):
    with zipfile.ZipFile(archive) as z:
        y=np.loadtxt(z.open('profile.txt'),dtype=int)
        description=z.read('description.txt').decode('utf8',errors='replace')
        (out/'source_description.txt').write_text(description)
    tuples=sorted(set(map(tuple,y[:,:4].tolist())),key=lambda t:hashlib.sha256(('hydraulic-v1|'+','.join(map(str,t))).encode()).hexdigest())
    n=len(tuples); ntrain=int(.6*n); nselect=int(.2*n)
    mapping={t:0 if j<ntrain else 1 if j<ntrain+nselect else 2 for j,t in enumerate(tuples)}
    split=np.array([mapping[tuple(t)] for t in y[:,:4]],dtype=np.int8)
    for part in range(3):
        for t in range(4):
            if set(y[split==part,t])!=set(y[:,t]): raise ValueError('Missing severity in split; do not silently resplit.')
    protocol={
        'schema':'singularity.sensor-replay.protocol/1','frozen_utc':stamp(),'dataset':URL,
        'archive_sha256':ARCHIVE_SHA256,'source_doi':'10.24432/C5CW21','license':'CC BY 4.0',
        'scope':'New combinations of familiar component severities on one measured hydraulic rig; no new-machine claim.',
        'targets':TASKS,'physical_sensors':SENSORS,'excluded':['CE','CP','SE','stability flag as predictor'],
        'split_rule':'All cycles sharing the same 4-component tuple stay together; SHA256 hydraulic-v1|comma-separated-tuple; first floor(.6G) training, next floor(.2G) selection, remainder test.',
        'groups':[{ 'condition':list(t),'partition':['train','selection','test'][mapping[t]]} for t in tuples],
        'cycles':{p:int((split==i).sum()) for i,p in enumerate(['train','selection','test'])},
        'group_counts':{p:sum(v==i for v in mapping.values()) for i,p in enumerate(['train','selection','test'])},
        'features':'Per full 60-second cycle: mean,std,min,max,q10,median,q90, six fixed 10-second means and six fixed 10-second stds (19 per sensor).',
        'classifier':{'type':'Per-sensor, per-task ExtraTreesClassifier; uniform-prior class balancing; sum clipped log probabilities across selected sensors', 'n_estimators':96,'max_features':1.0,'min_samples_leaf':2,'class_weight':'balanced','seed':SEED,'n_jobs':1,'probability_clip':1e-6},
        'selection_requirement':'For EACH of four tasks, balanced accuracy >= full-sensor selection balanced accuracy minus exactly 1/50. Integer/rational comparison, no test values used.',
        'objective':['fewest installed sensors','fewest logged scalar samples per 60-second cycle','smallest integer mask'],
        'logging_cost':'Sum of original channel sample counts; not price, energy, acquisition time or wall-clock speed.',
        'comparators':['all 14 sensors','forward greedy minimizing normalized constraint deficit','exact optimal pruning of greedy output','up to 256 seeded random panels at exact-selected cardinality'],
        'robust_secondary':'Same selection threshold after any one selected sensor is erased; report infeasible when no panel qualifies.',
        'strong_reference':'All-sensor ExtraTreesClassifier,256 trees,min_samples_leaf2,class_weight balanced,max_features sqrt,seed20261019; context only, not used for subset selection.',
        'uncertainty':'2000 paired bootstrap replicates resampling entire test fault-combination groups; missing classes omitted within replicate and counted.',
        'phase_order':['freeze labels/splits/protocol','extract measurements','fit training only','enumerate selection and freeze panels','evaluate held-out test once'],
        'limitations':['Same rig; unknown acquisition-session identifiers.','Grouping is by fault tuple, not independent machine or recovered session.','Temperature/history confounding can transfer imperfectly.','Finite selection optimum for fixed classifier, not universal sensor sufficiency.','No stimulus or location interventions absent from dataset.','Source task is supervised severity classification, not unsupervised unknown-fault discovery.']}
    write(out/'protocol.json',protocol)
    write(out/'freeze_receipt.json',{'protocol_sha256':digest(out/'protocol.json'),'frozen_utc':protocol['frozen_utc'],'source_sha256':digest(__file__)})
    np.savez_compressed(out/'split.npz',labels=y,split=split)
    print('Frozen',protocol['cycles'],protocol['group_counts'],flush=True)
    return y,split

def extract(archive, dest):
    X=[]
    with zipfile.ZipFile(archive) as z:
        for sensor in SENSORS:
            a=np.loadtxt(z.open(sensor+'.txt'),dtype=np.float64)
            n,m=a.shape
            b=a.reshape(n,6,m//6)
            q=np.quantile(a,[.1,.5,.9],axis=1).T
            x=np.column_stack([a.mean(1),a.std(1),a.min(1),a.max(1),q,b.mean(2),b.std(2)])
            if x.shape!=(2205,19) or not np.isfinite(x).all(): raise ValueError('Invalid physical measurements.')
            X.append(x)
            print('Extracted',sensor,a.shape,flush=True)
    X=np.stack(X,axis=1)
    np.savez_compressed(dest,features=X)
    return X

def fit_scores(X,y,split,out):
    import sklearn
    from sklearn.ensemble import ExtraTreesClassifier
    train=split==0; selection=split==1
    classes=[np.unique(y[:,t]) for t in range(4)]
    scores=[]; models=[]
    for t in range(4):
        task=[]; taskmodels=[]
        for s in range(14):
            model=ExtraTreesClassifier(n_estimators=96,max_features=1.0,min_samples_leaf=2,class_weight='balanced',random_state=SEED+100*t+s,n_jobs=1)
            model.fit(X[train,s],y[train,t])
            if not np.array_equal(model.classes_,classes[t]): raise ValueError('Training classes mismatch.')
            # Final-test values are not read here. Evaluate only train/selection.
            prob=model.predict_proba(X[selection,s])
            task.append(np.log(np.maximum(prob,1e-6)))
            taskmodels.append(model)
        scores.append(np.stack(task)); models.append(taskmodels)
        print('Fitted target',TASKS[t],flush=True)
    write(out/'environment.json',{'python':sys.version,'platform':platform.platform(),'numpy':np.__version__,'sklearn':sklearn.__version__,'threads':{k:os.environ.get(k) for k in ['OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS']}})
    return scores,models,classes

def enumerate_accuracy(scores,y,classes):
    # Dynamic sums produce all 2**14 scores; classification is floating point,
    # while constraints and costs below are exact integer/rational operations.
    ntotal=1<<14; counts=[]; denoms=[]; numerators=[]
    for t,sc in enumerate(scores):
        N,K=sc.shape[1:]; sums=np.zeros((ntotal,N,K),dtype=np.float64)
        for s in range(14):
            p=1<<s
            sums[p:2*p]=sums[:p]+sc[s]
        pred=sums.argmax(2)
        cc=np.stack([(pred[:,y[:,t]==label]==c).sum(1) for c,label in enumerate(classes[t])],axis=1).astype(np.int32)
        sizes=np.array([(y[:,t]==label).sum() for label in classes[t]],dtype=np.int64)
        L=math.lcm(*map(int,sizes)); D=K*L
        if D>2**55: raise ValueError('Integer comparison budget exceeded.')
        nums=cc@np.array([L//int(n) for n in sizes],dtype=np.int64)
        counts.append(cc);denoms.append(D);numerators.append(nums)
        del sums,pred
    return counts,np.stack(numerators,axis=1),np.array(denoms,dtype=np.int64)

def select(nums,denoms):
    full=(1<<14)-1
    feasible=np.all(50*(nums-nums[full])+denoms>=0,axis=1)
    feasible[0]=False
    candidates=np.flatnonzero(feasible).tolist()
    exact=min(candidates,key=cost)
    deficit=np.maximum(0,(nums[full]-nums)/denoms-0.02).sum(1)
    greedy=0; trace=[]
    while not feasible[greedy]:
        nxt=min((greedy|1<<s for s in range(14) if not greedy>>s&1),key=lambda m:(float(deficit[m]),cost(m)))
        trace.append({'mask':nxt,'deficit':float(deficit[nxt])});greedy=nxt
    pruned=min((m for m in candidates if m&greedy==m),key=cost)
    robust=feasible.copy()
    for s in range(14):
        masks=np.arange(1<<14); selected=(masks>>s&1).astype(bool)
        robust[selected]&=feasible[masks[selected]^(1<<s)]
    rc=np.flatnonzero(robust).tolist()
    robustmask=min(rc,key=cost) if rc else None
    # Freeze random comparator masks independent of test measurements.
    same=[m for m in range(1,1<<14) if m.bit_count()==exact.bit_count()]
    rng=np.random.default_rng(SEED)
    random_masks=sorted(map(int,rng.choice(same,size=min(256,len(same)),replace=False)))
    return {'exact':exact,'greedy':greedy,'pruned_greedy':pruned,'full':full,'robust':robustmask,'random_masks':random_masks,'greedy_trace':trace},feasible,robust

def metric(y,p):
    from sklearn.metrics import confusion_matrix
    task=[]
    for t in range(4):
        labels=np.unique(y[:,t]); recalls=[float(np.mean(p[y[:,t]==v,t]==v)) for v in labels]
        healthy=[100,100,0,130][t]
        h=y[:,t]==healthy
        task.append({'task':TASKS[t],'balanced_accuracy':float(np.mean(recalls)),'accuracy':float(np.mean(p[:,t]==y[:,t])), 'classes':labels.tolist(),'recalls':recalls,'confusion':confusion_matrix(y[:,t],p[:,t],labels=labels).tolist(),'healthy_false_alarm_rate':float(np.mean(p[h,t]!=healthy)) if h.any() else None,'healthy_cycles':int(h.sum())})
    return {'tasks':task,'macro_balanced_accuracy':float(np.mean([x['balanced_accuracy'] for x in task])),'joint_exact_match':float(np.mean(np.all(p==y[:,:4],axis=1))),'cycles':len(y)}

def predict(sc,classes,mask):
    return np.column_stack([classes[t][np.sum(task[ids(mask)],axis=0).argmax(1)] for t,task in enumerate(sc)])

def bootstrap(y,p,ref,groups):
    unique=np.unique(groups); indices=[np.flatnonzero(groups==g) for g in unique]
    rng=np.random.default_rng(SEED+1); vals=[]; missing=0
    levels=[np.unique(y[:,t]) for t in range(4)]
    for _ in range(2000):
        ix=np.concatenate([indices[j] for j in rng.integers(len(indices),size=len(indices))])
        row=[]
        for t in range(4):
            rr=[]
            for label in levels[t]:
                at=ix[y[ix,t]==label]
                if not len(at): missing+=1;continue
                rr.append(np.mean(p[at,t]==label)-np.mean(ref[at,t]==label))
            row.append(np.mean(rr))
        vals.append(row+[np.mean(np.all(p[ix]==y[ix,:4],axis=1))-np.mean(np.all(ref[ix]==y[ix,:4],axis=1))])
    a=np.array(vals)
    return {'replicates':2000,'groups':len(unique),'missing_class_events':missing,'task_balanced_accuracy_difference_95pct':np.quantile(a[:,:4],[.025,.975],axis=0).T.tolist(),'joint_match_difference_95pct':np.quantile(a[:,4],[.025,.975]).tolist()}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--output',type=Path,required=True)
    a=ap.parse_args();out=a.output;out.mkdir(parents=True,exist_ok=True)
    if (out/'protocol.json').exists(): raise ValueError('Refuse to overwrite frozen study. Use a new output directory.')
    download(a.archive); y,split=freeze(a.archive,out)
    X=extract(a.archive,out/'features.npz')
    selection_scores,models,classes=fit_scores(X,y,split,out)
    counts,nums,denoms=enumerate_accuracy(selection_scores,y[split==1],classes)
    chosen,feasible,robust=select(nums,denoms)
    np.savez_compressed(out/'selection_table.npz',numerators=nums,denominators=denoms,feasible=feasible,robust_feasible=robust,**{f'correct_{t}':c for t,c in enumerate(counts)},**{f'scores_{t}':s for t,s in enumerate(selection_scores)})
    chosen['frozen_utc']=stamp();chosen['protocol_sha256']=digest(out/'protocol.json');chosen['selection_table_sha256']=digest(out/'selection_table.npz')
    write(out/'selected_panels.json',chosen)
    print('Panels frozen',{k:names(v) if isinstance(v,int) else v for k,v in chosen.items() if k in ['exact','greedy','pruned_greedy','full','robust']},flush=True)
    # Only after this checkpoint is held-out measurement performance evaluated.
    test=split==2; yt=y[test]; sc=[]
    for t in range(4):
        sc.append(np.stack([np.log(np.maximum(models[t][s].predict_proba(X[test,s]),1e-6)) for s in range(14)]))
    results={'schema':'singularity.sensor-replay.result/1','evaluated_utc':stamp(),'protocol_sha256':digest(out/'protocol.json'),'selected_panels_sha256':digest(out/'selected_panels.json'),'selection_threshold_balanced_accuracy':(nums[-1]/denoms-.02).tolist(),'feasible_mask_count':int(feasible.sum()),'robust_feasible_mask_count':int(robust.sum()),'panels':{},'limitations':json.loads((out/'protocol.json').read_text())['limitations']}
    predictions={}
    group_keys=[tuple(v) for v in yt[:,:4].tolist()]; group_list=sorted(set(group_keys));groups=np.array([group_list.index(v) for v in group_keys])
    fullpred=predict(sc,classes,chosen['full'])
    for label in ['exact','greedy','pruned_greedy','full','robust']:
        mask=chosen[label]
        if mask is None:results['panels'][label]={'status':'selection-infeasible'};continue
        p=predict(sc,classes,mask);predictions[label]=p
        r={'mask':mask,'sensors':names(mask),'sensor_count':mask.bit_count(),'logged_scalars':cost(mask)[1],'selection_balanced_accuracy':(nums[mask]/denoms).tolist(),'test':metric(yt,p),'paired_group_bootstrap_vs_full':bootstrap(yt,p,fullpred,groups)}
        for flag,name in [(0,'stable'),(1,'transient')]:
            take=yt[:,4]==flag;r[name]=metric(yt[take],p[take]) if take.any() else None
        if label=='robust':
            r['single_sensor_erasure_test']={SENSORS[s]:metric(yt,predict(sc,classes,mask^(1<<s))) for s in ids(mask)}
        results['panels'][label]=r
    random=[]
    for mask in chosen['random_masks']:
        p=predict(sc,classes,mask)
        r=metric(yt,p);random.append({'mask':mask,'macro_balanced_accuracy':r['macro_balanced_accuracy'],'joint_exact_match':r['joint_exact_match']})
    results['random_same_cardinality']={'count':len(random),'macro_balanced_accuracy_quantiles':np.quantile([r['macro_balanced_accuracy'] for r in random],[0,.25,.5,.75,1]).tolist(),'joint_exact_match_quantiles':np.quantile([r['joint_exact_match'] for r in random],[0,.25,.5,.75,1]).tolist(),'panels':random}
    from sklearn.ensemble import ExtraTreesClassifier
    refpred=[]
    for t in range(4):
        model=ExtraTreesClassifier(n_estimators=256,min_samples_leaf=2,max_features='sqrt',class_weight='balanced',random_state=SEED,n_jobs=1)
        model.fit(X[split==0].reshape((split==0).sum(),-1),y[split==0,t]);refpred.append(model.predict(X[test].reshape(test.sum(),-1)))
    results['all_sensor_stronger_reference']=metric(yt,np.column_stack(refpred))
    np.savez_compressed(out/'test_evidence.npz',labels=yt,groups=groups,**{f'scores_{t}':s for t,s in enumerate(sc)},**{f'prediction_{k}':p for k,p in predictions.items()},reference_predictions=np.column_stack(refpred))
    results['evidence_sha256']={p.name:digest(p) for p in [out/'protocol.json',out/'split.npz',out/'features.npz',out/'selected_panels.json',out/'selection_table.npz',out/'test_evidence.npz']}
    write(out/'results.json',results)
    print(json.dumps({k:{'sensors':v.get('sensors'),'test':v.get('test')} for k,v in results['panels'].items()},indent=2),flush=True)
if __name__=='__main__':main()
