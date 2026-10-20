import pathlib,json,hashlib,datetime
ROOT=pathlib.Path(__file__).resolve().parent;WORK=ROOT.parents[1];DATA=WORK/'audio_data';V1=ROOT.parent
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((V1/'protocol.json').read_text());s=json.loads((V1/'selection_snapshot.json').read_text())
old=json.loads((DATA/'acquisition.json').read_text());oldnames={r['name'] for r in old['records']}
records=[]
for state,folder in [('normal','normal'),('horizontal-misalignment','horizontal-misalignment/1.5mm'),('imbalance','imbalance/6g')]:
 inv=json.loads((DATA/(state+'_inventory.json')).read_text());ms=[m for m in inv['members'] if m['name'].endswith('.csv') and '/'.join(m['name'].split('/')[:-1])==folder]
 for i,t in enumerate([17.5,22.5,27.5,32.5,37.5,42.5]):
  m=min(ms,key=lambda m:abs(float(pathlib.Path(m['name']).stem)-t))
  assert m['name'] not in oldnames
  records.append(dict(m,archive_url=inv['url'],archive_size=inv['archive_size'],state=state,speed_target_hz=t,speed_from_filename_hz=float(pathlib.Path(m['name']).stem),grid_index=i))
best=max(r['balanced_accuracy'] for r in s['all_selection_masks'] if r['cost']==1)
ties=[r['mask'] for r in s['all_selection_masks'] if r['cost']==1 and abs(r['balanced_accuracy']-best)<1e-12]
union=0
for mask in ties:union|=mask
p.update(version=2,study='Prospective new-recording confirmation of a tie-preserving MAFAULDA sensor panel',freeze_stage='after negative v1 test, before acquiring or extracting new confirmation recordings',source_acquisition='../../audio_data/acquisition_v2.json',sample_size=18,speed_targets_hz=[17.5,22.5,27.5,32.5,37.5,42.5],splits_grid_indices={'confirmation':list(range(6))},training_source='../features.npz',training_protocol_sha256=h(V1/'protocol.json'),v1_results_sha256=h(V1/'results.json'),v1_selection_snapshot_sha256=h(V1/'selection_snapshot.json'),training_rule='reuse v1 training recordings, training mean/std and nearest-neighbor models unchanged; no new fit or hyperparameter selection',confirmation_rule='all 18 new recordings form a single locked confirmation set; no selection stage',panel_rule='bitwise union of ALL singleton masks attaining the maximum balanced accuracy on original v1 selection; no use of v1 test score to choose among these tied singletons',all_development_optimal_singletons=ties,locked_panels={'original_exact':s['exact_selection']['mask'],'original_greedy':s['greedy_selection']['mask'],'original_pruned_greedy':s['pruned_greedy_selection']['mask'],'tie_preserving_union':union,'full':127,'microphone_only':64,'all_accelerometers':63},source_member_plan=records,interpretation='a new design triggered by v1 failure; confirmation does not reinterpret v1 test or claim exact outperformance over an equivalently tie-preserving greedy policy')
p['limitations']=[x for x in p['limitations'] if x!='six test recordings, two per class']+['eighteen new confirmation recordings, six per class','confirmation speed targets lie between original targets on the same machine; not independent device/session generalization','tie-union design is post-v1 and may cost more than the v1 minimum','no theorem guarantees this union will transfer']
(ROOT/'protocol.json').write_text(json.dumps(p,indent=2,sort_keys=True)+'\n')
fr={'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'protocol_sha256':h(ROOT/'protocol.json'),'all_new_recordings_unacquired_and_uninspected':True}
(ROOT/'freeze_receipt.json').write_text(json.dumps(fr,indent=2)+'\n')
(DATA/'subset_plan_v2.json').write_text(json.dumps({'records':records},indent=2))
print(json.dumps({'freeze':fr,'ties':ties,'union':union,'source_members':[r['name'] for r in records]},indent=2))
