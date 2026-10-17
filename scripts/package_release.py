#!/usr/bin/env python3
"""Build a complete deterministic source/documents/results archive."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT=Path(__file__).resolve().parents[1]
EXCLUDED={'.git','tmp','releases','__pycache__','.venv','.pytest_cache'}
SUFFIXES={'.aux','.log','.out','.toc','.fls','.fdb_latexmk','.pyc','.synctex.gz'}


def main():
    source=[]
    for p in ROOT.rglob('*'):
        relative=p.relative_to(ROOT)
        if not p.is_file() or any(part in EXCLUDED or part.endswith('.egg-info') for part in relative.parts):
            continue
        if any(str(p).endswith(suffix) for suffix in SUFFIXES):
            continue
        if relative.as_posix()=='results/archive_manifest.json':
            continue
        source.append(p)
    source.sort(key=lambda p:p.relative_to(ROOT).as_posix())
    entries=[{'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in source]
    manifest={'schema':'singularity.release-manifest/1','version':'0.1.0','files':entries,'self_hash_excluded':'results/archive_manifest.json','excluded':'git object directory, earlier releases, caches, temporary and TeX auxiliary files'}
    manifest_path=ROOT/'results'/'archive_manifest.json';manifest_path.write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n')
    source.append(manifest_path)
    target=ROOT/'releases'/'Singularity-v0.1.0-complete.zip';target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as archive:
        for p in source:
            entry=zipfile.ZipInfo('singularity/'+p.relative_to(ROOT).as_posix(),date_time=(2026,10,17,0,0,0))
            entry.external_attr=0o100644<<16;entry.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(entry,p.read_bytes())
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        for item in entries:
            assert hashlib.sha256(archive.read('singularity/'+item['path'])).hexdigest()==item['sha256']
    print(json.dumps({'archive':str(target),'bytes':target.stat().st_size,'files':len(source),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2))


if __name__=='__main__':
    main()
