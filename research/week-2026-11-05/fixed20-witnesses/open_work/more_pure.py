import sys,json
from pathlib import Path
sys.path.insert(0,'open_work')
# Execute the pool collector definitions, retaining a separate output namespace.
s=Path('open_work/pure_search.py').read_text();s=s[:s.index("s=json.load(open('final_bundle/replay/fresh_small_witnesses.json'))")]
s=s.replace("pure_pool.jsonl","more_pool.jsonl").replace("pure_checkpoint.json","more_checkpoint.json")
exec(s)
parents=json.load(open('final_bundle/replay/fresh_small_witnesses.json'))['witnesses']
for wi in (1,2,4):
 p=next(find(parents[wi],0 if wi==4 else (2 if wi==1 else 1)))
 for side in ('A_edges','B_edges'):
  for mark,E in edge_variants(p,side):add(E,['extra_edge',wi,side,mark])
checkpoint();stream.close();print('DONE',processed,list(found),flush=True)
