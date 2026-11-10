"""Restore byte-identical large evidence files; --check verifies stored bytes only."""
import argparse,gzip,hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--check',action='store_true');a=p.parse_args()
records=json.loads((root/'COMPRESSED_EVIDENCE.json').read_text())
for r in records:
    stored=root/r['stored_path'];raw=gzip.decompress(stored.read_bytes())
    if len(raw)!=r['original_size'] or hashlib.sha256(raw).hexdigest()!=r['original_sha256']:raise SystemExit('Evidence mismatch: '+r['path'])
    target=root/r['path']
    if not a.check:
        if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest()!=r['original_sha256']:raise SystemExit('Refusing to replace changed file: '+r['path'])
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
print('Verified '+str(len(records))+' lossless evidence objects'+(' (stored bytes only)' if a.check else '; restored originals'))
