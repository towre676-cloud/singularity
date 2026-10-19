#!/usr/bin/env python3
"""Package the complete implemented source and PDFs without caches or history."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT.parent / 'deliverables/nx36-complete/Singularity-NX36-complete.zip')
    args = parser.parse_args()
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    dirty = subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip()
    if dirty:
        raise SystemExit('Commit validated source before packaging: working tree is dirty')
    roadmap = json.loads((ROOT / 'handoff/nx36/roadmap.json').read_text())
    complete = sum(u['status'] == 'complete' for t in roadmap['tracks'] for u in t['pushes'])
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    files = []
    for name in names:
        if not name or name.startswith(('releases/', 'tmp/', '.git/')):
            continue
        if name.endswith(('.zip', '.bundle', '.pyc')) or '/.lake/' in name or '/__pycache__/' in name:
            continue
        if (ROOT / name).is_file():
            files.append(name)
    files.sort()
    required = ('output/pdf/nx36_implementation.pdf', 'docs/NX36_MANUSCRIPT.md',
                'results/nx36_validation.json', 'handoff/nx36/roadmap.json')
    if any(name not in files for name in required):
        raise SystemExit('Complete source/PDF/evidence files are required')
    hashes = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in files}
    manifest = {'schema': 'singularity.nx36-archive/1', 'source_commit': commit,
                'accepted_units': complete, 'total_units': 108,
                'files': hashes,
                'excluded': ['Git history', 'Git bundles', 'build caches', 'older release ZIPs',
                             'restricted raw athlete rows'],
                'empirical_nfl_scope': 'owned-source execution aggregate and provenance; public raw rerun excluded'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    prefix = 'Singularity-NX36/'
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in files:
            archive.write(ROOT / name, prefix + name)
        archive.writestr(prefix + 'ARCHIVE_MANIFEST.json', json.dumps(manifest, sort_keys=True, indent=2) + '\n')
    with zipfile.ZipFile(args.output) as archive:
        if archive.testzip() is not None:
            raise SystemExit('ZIP CRC failure')
        for name, digest in hashes.items():
            if hashlib.sha256(archive.read(prefix + name)).hexdigest() != digest:
                raise SystemExit('ZIP SHA256 mismatch: ' + name)
    report = {'archive': str(args.output.resolve()), 'source_commit': commit,
              'accepted_units': complete, 'files': len(files),
              'bytes': args.output.stat().st_size,
              'sha256': hashlib.sha256(args.output.read_bytes()).hexdigest(),
              'all_members_verified': True}
    args.output.with_suffix('.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(json.dumps(report, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
