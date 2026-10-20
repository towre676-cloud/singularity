#!/usr/bin/env python3
"""One-time Git-object transport; never stage workflow or transport files."""
import base64
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile


def git_blob(data):
    return hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()


def safe_path(value):
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(p in ('..', '.', '.git') for p in path.parts):
        raise ValueError('Unsafe transport path')
    if path.as_posix() != value:
        raise ValueError('Noncanonical transport path')
    return path


root = Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip()).resolve()
manifest_bytes = (root/'_mimii_transport/manifest.json').read_bytes()
assert hashlib.sha256(manifest_bytes).hexdigest() == '089a1ffca6a11d0cd309627c9b00afd1c70710d3a3056fcabd7cdf4ed98e6dd9'
manifest = json.loads(manifest_bytes)
assert manifest['schema'] == 'singularity.mimii-exact-publication-transport/1'
assert manifest['parent'] == '2c37377d4af97467e6025191e20ea7a8e41656ee'
assert manifest['final_tree'] == '207148eb8874ddc11e0d628ad204a9a56adcb8f2'
assert 0 < manifest['zip_bytes'] < 128*1024*1024
subprocess.run(['git', 'diff', '--cached', '--quiet'], check=True)
encoded_chunks = []
seen_chunks = set()
for chunk in manifest['chunks']:
    path = safe_path(chunk['path'])
    assert path.parts[0] == '_mimii_transport' and chunk['path'] not in seen_chunks
    seen_chunks.add(chunk['path'])
    encoded = (root/path).read_bytes()
    assert len(encoded) == chunk['bytes'] and git_blob(encoded) == chunk['sha']
    encoded_chunks.append(base64.b64decode(encoded, validate=True))
archive = b''.join(encoded_chunks)
assert len(archive) == manifest['zip_bytes']
assert hashlib.sha256(archive).hexdigest() == manifest['zip_sha256']
expected = {}
for row in manifest['files']:
    safe_path(row['path'])
    assert row['path'] not in expected and 0 <= row['bytes'] < 128*1024*1024
    assert not row['path'].startswith('_mimii_transport/')
    expected[row['path']] = row
assert len(expected) == 51 and sum(row['bytes'] for row in expected.values()) < 256*1024*1024
payload = {}
with zipfile.ZipFile(io.BytesIO(archive)) as zipped:
    names = [entry.filename for entry in zipped.infolist()]
    assert len(names) == len(set(names)) and set(names) == set(expected)
    for entry in zipped.infolist():
        row = expected[entry.filename]
        assert not entry.is_dir() and entry.file_size == row['bytes']
        data = zipped.read(entry)
        assert len(data) == row['bytes'] and git_blob(data) == row['sha']
        # This source workflow is already available through the authenticated
        # API. GITHUB_TOKEN must never create, change or remove workflow files.
        if entry.filename.startswith('.github/'):
            continue
        destination = root/safe_path(entry.filename)
        assert destination.resolve().is_relative_to(root)
        for ancestor in [destination, *destination.parents]:
            if ancestor == root:
                break
            assert not ancestor.is_symlink()
        payload[entry.filename] = data
assert len(payload) == 50
# All source checks finish before the first worktree mutation.
for name, data in payload.items():
    destination = root/name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(data)
    destination.chmod(0o644)
subprocess.run(['git', 'add', '-f', '--', *sorted(payload)], cwd=root, check=True)
staged = subprocess.check_output(['git', 'diff', '--cached', '--name-only', '-z'], cwd=root).decode().split('\0')
assert set(filter(None, staged)) == set(payload)
for name in payload:
    actual = subprocess.check_output(['git', 'rev-parse', ':'+name], cwd=root, text=True).strip()
    assert actual == expected[name]['sha']
print(json.dumps({'verified_zip_sha256': manifest['zip_sha256'], 'verified_files': 51,
                  'staged_research_files': 50, 'workflow_files_staged': 0,
                  'expected_final_tree_for_separate_publication': manifest['final_tree']}, sort_keys=True))
