#!/usr/bin/env python3
"""Build a deterministic source/documents/results archive of one Git commit.

The archive holds exactly the tracked files of the named commit (default HEAD), read from
Git objects, so untracked build products and uncommitted edits never enter it. Earlier
archives under releases/ are excluded and never overwritten: the label names a new file.
The historical v0.1.0 archive was built by an earlier working-tree version of this script.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, check=True, capture_output=True).stdout


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('label', help='archive label, e.g. 0.1.0-p35; must not name an existing archive')
    parser.add_argument('--commit', default='HEAD')
    parser.add_argument('--date', default=None, help='zip entry date YYYY-MM-DD (default: commit date)')
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9A-Za-z][0-9A-Za-z.+-]*', args.label):
        parser.error('label may contain only letters, digits, ".", "+" and "-"')
    commit = git('rev-parse', '--verify', args.commit + '^{commit}').decode().strip()
    date = args.date or git('show', '-s', '--format=%cs', commit).decode().strip()
    stamp = tuple(int(v) for v in date.split('-')) + (0, 0, 0)
    target = ROOT / 'releases' / f'Singularity-v{args.label}-complete.zip'
    manifest_path = ROOT / 'releases' / f'Singularity-v{args.label}-manifest.json'
    if target.exists() or manifest_path.exists():
        parser.error(f'{target.name} or its manifest already exists; choose a new label')
    listing = git('ls-tree', '-r', '-z', commit).split(b'\0')
    blobs = []
    for row in filter(None, listing):
        meta, path = row.decode().split('\t', 1)
        mode, kind, obj = meta.split()
        if kind == 'blob' and not path.startswith('releases/'):
            blobs.append((path, mode, obj))
    blobs.sort()
    entries, members = [], []
    for path, mode, obj in blobs:
        data = git('cat-file', 'blob', obj)
        entries.append({'path': path, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
        members.append((path, mode, data))
    manifest = {'schema': 'singularity.release-manifest/1', 'label': args.label, 'source_commit': commit,
                'files': entries, 'excluded': 'releases/ (earlier archives); untracked and uncommitted files'}
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode()
    target.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, mode, data in members + [('RELEASE_MANIFEST.json', '100644', manifest_bytes)]:
            entry = zipfile.ZipInfo('singularity/' + path, date_time=stamp)
            entry.external_attr = (0o100755 if mode == '100755' else 0o100644) << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data)
    with zipfile.ZipFile(target) as archive:
        assert archive.testzip() is None
        for item in entries:
            assert hashlib.sha256(archive.read('singularity/' + item['path'])).hexdigest() == item['sha256']
    manifest_path.write_bytes(manifest_bytes)
    print(json.dumps({'archive': str(target.relative_to(ROOT)), 'source_commit': commit, 'bytes': target.stat().st_size,
                      'files': len(entries) + 1, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}, indent=2))


if __name__ == '__main__':
    main()
