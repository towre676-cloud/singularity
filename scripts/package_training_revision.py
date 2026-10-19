#!/usr/bin/env python3
"""Package committed Singularity source, publications and measured training evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT.parent/'deliverables/Singularity-v0.6.0-training.zip')
    args = parser.parse_args()
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT).strip():
        raise SystemExit('Commit validated source before packaging: working tree is dirty')
    commit = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    analysis = json.loads((ROOT/'applications/training_lab/results/analysis.json').read_text())
    validation = json.loads((ROOT/'applications/training_lab/results/validation.json').read_text())
    if not analysis['complete'] or not analysis['overall_audit_passed']:
        raise SystemExit('Complete passing training analysis required')
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    files = sorted(name for name in names if name and (ROOT/name).is_file()
                   and not name.startswith(('releases/', 'tmp/', '.git/'))
                   and not name.endswith(('.zip', '.bundle', '.pyc', 'metrics.jsonl'))
                   and '/.lake/' not in name and '/__pycache__/' not in name)
    required = ['output/pdf/training_observation.pdf', 'docs/papers/training_observation.md',
                'applications/training_lab/README.md',
                'applications/training_lab/results/engine_source_snapshot/manifest.json',
                'applications/training_lab/results/integrity_replays.json',
                'applications/training_lab/results/validation.json']
    if any(name not in files for name in required):
        raise SystemExit('Source, publication, and complete evidence are required')
    hashes = {name: sha((ROOT/name).read_bytes()) for name in files}
    manifest = {'schema': 'singularity.training-archive/1', 'source_commit': commit,
                'version': '0.6.0', 'files': hashes, 'compute': analysis['compute'],
                'validation_receipt_sha256': hashes['applications/training_lab/results/validation.json'],
                'excluded': ['git history', 'build caches', 'older nested release ZIPs',
                             'uncompressed copies of retained gzip logs',
                             'external WikiText source text; use pinned download script',
                             'restricted raw athlete rows'],
                'scope': '63 planned training runs plus documented integrity repeats; no grokking demonstrated'}
    # Read the receipt here so a corrupt JSON validation file fails before writing.
    if not isinstance(validation, dict) or validation.get('status') != 'passed':
        raise SystemExit('Passing validation receipt required')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    prefix = 'Singularity-v0.6.0/'
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name in files:
            archive.write(ROOT/name, prefix+name)
        archive.writestr(prefix+'ARCHIVE_MANIFEST.json', json.dumps(manifest, indent=2, sort_keys=True)+'\n')
    with zipfile.ZipFile(args.output) as archive:
        if archive.testzip() is not None:
            raise SystemExit('ZIP CRC failure')
        for name, digest in hashes.items():
            if sha(archive.read(prefix+name)) != digest:
                raise SystemExit('ZIP SHA256 mismatch: '+name)
    report = {'source_commit': commit, 'files': len(files), 'bytes': args.output.stat().st_size,
              'sha256': sha(args.output.read_bytes()), 'all_members_verified': True,
              'archive': str(args.output.resolve())}
    args.output.with_suffix('.json').write_text(json.dumps(report, indent=2, sort_keys=True)+'\n')
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
