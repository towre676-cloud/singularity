#!/usr/bin/env python3
"""Independent replay of saved hydraulic evidence; imports no study code.

Checks finite accuracy-table optimality with fractions.Fraction, frozen groups,
selected-panel scores, all published test metrics, and evidence digests.
Does not independently reproduce training from raw time series.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import numpy as np

CHANNELS = ('PS1','PS2','PS3','PS4','PS5','PS6','EPS1','FS1','FS2','TS1','TS2','TS3','TS4','VS1')
RATES = (100,100,100,100,100,100,100,10,10,1,1,1,1,1)
TARGETS = ('cooler','valve','pump','accumulator')
HEALTHY = (100,100,0,130)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def objective(mask):
    return (sum(bool(mask & (1 << j)) for j in range(14)),
            sum(60 * RATES[j] for j in range(14) if mask & (1 << j)), mask)

def score_metrics(labels, predictions):
    tasks=[]
    for j,name in enumerate(TARGETS):
        levels=sorted(set(map(int,labels[:,j])))
        recalls=[float(np.count_nonzero(predictions[labels[:,j]==v,j]==v)/np.count_nonzero(labels[:,j]==v)) for v in levels]
        h=labels[:,j]==HEALTHY[j]
        confusion=[[int(np.count_nonzero((labels[:,j]==v)&(predictions[:,j]==w))) for w in levels] for v in levels]
        tasks.append(dict(task=name,balanced_accuracy=float(sum(recalls)/len(recalls)),
            accuracy=float(np.count_nonzero(predictions[:,j]==labels[:,j])/len(labels)),
            classes=levels,recalls=recalls,confusion=confusion,
            healthy_false_alarm_rate=float(np.count_nonzero(predictions[h,j]!=HEALTHY[j])/np.count_nonzero(h)) if h.any() else None,
            healthy_cycles=int(np.count_nonzero(h))))
    return dict(tasks=tasks,macro_balanced_accuracy=float(sum(t['balanced_accuracy'] for t in tasks)/4),
                joint_exact_match=float(np.count_nonzero(np.all(predictions==labels[:,:4],axis=1))/len(labels)),cycles=len(labels))

def same(actual,expected,path='result'):
    if isinstance(expected,dict):
        assert actual.keys()==expected.keys(), (path,'keys')
        for key,value in expected.items(): same(actual[key],value,path+'.'+key)
    elif isinstance(expected,list):
        assert len(actual)==len(expected),(path,'length')
        for j,(a,b) in enumerate(zip(actual,expected)): same(a,b,path+f'[{j}]')
    elif isinstance(expected,float):
        assert abs(float(actual)-expected)<1e-12,(path,actual,expected)
    else:
        assert actual==expected,(path,actual,expected)

def predict(scores,levels,mask):
    selected=[j for j in range(14) if mask & (1<<j)]
    outputs=[]
    for j in range(4):
        # Sequential additions give an explicit independent score reconstruction.
        total=np.zeros_like(scores[j][0])
        for s in selected: total=total+scores[j][s]
        outputs.append(levels[j][np.argmax(total,axis=1)])
    return np.stack(outputs,axis=1)

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('directory',type=Path)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args();root=args.directory
    protocol=json.loads((root/'protocol.json').read_text())
    panels=json.loads((root/'selected_panels.json').read_text())
    results=json.loads((root/'results.json').read_text())
    receipt=json.loads((root/'freeze_receipt.json').read_text())
    assert sha(root/'protocol.json')==receipt['protocol_sha256']==results['protocol_sha256']==panels['protocol_sha256']
    assert sha(root/'selected_panels.json')==results['selected_panels_sha256']
    assert sha(root/'selection_table.npz')==panels['selection_table_sha256']
    for name,wanted in results['evidence_sha256'].items(): assert sha(root/name)==wanted,name
    splits=np.load(root/'split.npz');labels=splits['labels'];partition=splits['split']
    tuples=sorted(set(map(tuple,labels[:,:4].tolist())),key=lambda x:hashlib.sha256(('hydraulic-v1|'+','.join(map(str,x))).encode()).hexdigest())
    a=int(.6*len(tuples));b=a+int(.2*len(tuples))
    group_map={t:0 if i<a else 1 if i<b else 2 for i,t in enumerate(tuples)}
    expected=np.array([group_map[tuple(row)] for row in labels[:,:4]])
    assert np.array_equal(partition,expected)
    for j,name in enumerate(('train','selection','test')):
        assert int(np.count_nonzero(partition==j))==protocol['cycles'][name]
        assert sum(v==j for v in group_map.values())==protocol['group_counts'][name]
        for t in range(4): assert set(labels[partition==j,t])==set(labels[:,t])
    all_levels=[np.unique(labels[:,j]) for j in range(4)]
    loaded=np.load(root/'selection_table.npz');table={key:loaded[key] for key in loaded.files};sel_labels=labels[partition==1]
    counts=[table[f'correct_{j}'] for j in range(4)]
    frequencies=[[(sel_labels[:,j]==v).sum().item() for v in all_levels[j]] for j in range(4)]
    # Independently rebuild EVERY mask's predictions from saved per-sensor
    # log scores. This is a batched direct sum, not the runner's dynamic table.
    for j in range(4):
        scores=table[f'scores_{j}']
        for start in range(0,1<<14,256):
            masks=np.arange(start,min(start+256,1<<14))
            total=np.zeros((len(masks),scores.shape[1],scores.shape[2]),dtype=np.float64)
            for sensor in range(14):
                active=(masks & (1<<sensor))!=0
                total[active]=total[active]+scores[sensor]
            pred=total.argmax(axis=2)
            rebuilt=np.column_stack([(pred[:,sel_labels[:,j]==v]==c).sum(axis=1)
                                     for c,v in enumerate(all_levels[j])])
            assert np.array_equal(rebuilt,counts[j][start:start+len(masks)]),('all-mask score replay',j,start)
    accuracies=[]
    for j in range(4):
        rows=[]
        for mask in range(1<<14):
            value=sum((Fraction(int(k),n) for k,n in zip(counts[j][mask],frequencies[j])),Fraction())/len(frequencies[j])
            assert value==Fraction(int(table['numerators'][mask,j]),int(table['denominators'][j]))
            rows.append(value)
        accuracies.append(rows)
    thresholds=[a[-1]-Fraction(1,50) for a in accuracies]
    feasible=[mask>0 and all(accuracies[j][mask]>=thresholds[j] for j in range(4)) for mask in range(1<<14)]
    assert np.array_equal(feasible,table['feasible'])
    chosen=min((m for m,v in enumerate(feasible) if v),key=objective)
    assert chosen==panels['exact']
    greedy=panels['greedy']
    assert feasible[greedy]
    restricted=min((m for m,v in enumerate(feasible) if v and (m|greedy)==greedy),key=objective)
    assert restricted==panels['pruned_greedy']
    robust=[feasible[m] and all(feasible[m ^ (1<<s)] for s in range(14) if m & (1<<s)) for m in range(1<<14)]
    assert np.array_equal(robust,table['robust_feasible'])
    robust_choices=[m for m,v in enumerate(robust) if v]
    assert (min(robust_choices,key=objective) if robust_choices else None)==panels['robust']
    assert sum(feasible)==results['feasible_mask_count']
    assert sum(robust)==results['robust_feasible_mask_count']
    sc=[table[f'scores_{j}'] for j in range(4)]
    for name in ('exact','greedy','pruned_greedy','full','robust'):
        m=panels[name]
        if m is None: continue
        preds=predict(sc,all_levels,m)
        for j in range(4):
            got=[int(np.count_nonzero(preds[sel_labels[:,j]==v,j]==v)) for v in all_levels[j]]
            assert np.array_equal(got,counts[j][m]),(name,'selection-counts',j)
    test=np.load(root/'test_evidence.npz');yt=test['labels']
    assert np.array_equal(yt,labels[partition==2])
    group_rows=[tuple(row) for row in yt[:,:4].tolist()]
    group_list=sorted(set(group_rows));expected_groups=np.array([group_list.index(t) for t in group_rows])
    assert np.array_equal(test['groups'],expected_groups)
    ts=[test[f'scores_{j}'] for j in range(4)]
    checked=[]
    for name in ('exact','greedy','pruned_greedy','full','robust'):
        m=panels[name]
        if m is None: continue
        preds=predict(ts,all_levels,m)
        assert np.array_equal(preds,test[f'prediction_{name}']),(name,'prediction')
        published=results['panels'][name]
        same(score_metrics(yt,preds),published['test'],name+'.test')
        for flag,subname in ((0,'stable'),(1,'transient')):
            use=yt[:,4]==flag
            if use.any(): same(score_metrics(yt[use],preds[use]),published[subname],name+'.'+subname)
        if name=='robust':
            for s in range(14):
                if m & (1<<s): same(score_metrics(yt,predict(ts,all_levels,m^(1<<s))),published['single_sensor_erasure_test'][CHANNELS[s]],'erasure.'+CHANNELS[s])
        checked.append(name)
    for row in results['random_same_cardinality']['panels']:
        m=row['mask'];assert objective(m)[0]==objective(chosen)[0]
        met=score_metrics(yt,predict(ts,all_levels,m))
        same(met['macro_balanced_accuracy'],row['macro_balanced_accuracy'],'random.ba')
        same(met['joint_exact_match'],row['joint_exact_match'],'random.joint')
    same(score_metrics(yt,test['reference_predictions']),results['all_sensor_stronger_reference'],'reference')
    output=dict(status='PASS',independent_implementation=True,uses_study_imports=False,
        masks_checked=1<<14,all_mask_predictions_independently_rebuilt=True,rational_task_entries_checked=4*(1<<14),exact_mask=chosen,
        pruned_greedy_mask=restricted,robust_mask=panels['robust'],
        feasible_masks=sum(feasible),robust_feasible_masks=sum(robust),
        test_panels_checked=checked,random_panels_checked=len(results['random_same_cardinality']['panels']),
        source_hash_matches_frozen=(sha(root.parent/'run_hydraulic.py')==receipt['source_sha256']),
        scope='Independent exact finite-table optimum and saved-score metric replay; training, bootstrap interval generation and physical transfer not independently reproduced.',
        verifier_sha256=sha(Path(__file__)))
    text=json.dumps(output,indent=2,sort_keys=True)+'\n'
    if args.output: args.output.write_text(text)
    print(text)

if __name__=='__main__': main()
