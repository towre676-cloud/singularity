#!/usr/bin/env python3
"""Re-extract fixed features from verified source signals in temporary files.
Preserves frozen protocols, feature files, selection snapshots and results.
"""
import importlib.util,json,pathlib,tempfile,numpy as np
ROOT=pathlib.Path(__file__).resolve().parent;DATA=ROOT.parent/'audio_data'
spec=importlib.util.spec_from_file_location('frozen_extraction',ROOT/'run_audio_study.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
for phase,source in [(ROOT,'acquisition.json'),(ROOT/'confirmation','acquisition_v2.json')]:
 p=json.loads((phase/'protocol.json').read_text());p['source_acquisition']=str(DATA/source)
 with tempfile.TemporaryDirectory(prefix='mafaulda_feature_replay_') as tmp:
  m.ROOT=pathlib.Path(tmp);(m.ROOT/'protocol.json').write_bytes((phase/'protocol.json').read_bytes());m.extract(p)
  a=np.load(phase/'features.npz',allow_pickle=False);b=np.load(m.ROOT/'features.npz',allow_pickle=False)
  for key in a.files:
   if a[key].dtype.kind in 'fc':np.testing.assert_allclose(a[key],b[key],rtol=1e-12,atol=1e-12)
   else:assert np.array_equal(a[key],b[key])
  print('RAW FEATURE REPLAY PASSED',phase.name,flush=True)
