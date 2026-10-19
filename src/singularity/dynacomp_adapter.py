"""Optional, byte-pinned DynaComp loading; the core has no upstream dependency."""
from __future__ import annotations
import hashlib
import importlib
import importlib.util
from pathlib import Path
import sys
from fractions import Fraction


def exact(value):
    if isinstance(value, bool) or not isinstance(value, (int, Fraction)):
        raise TypeError('int or Fraction required; floats and numeric strings are not public exact values')
    return Fraction(value)


def source_digest(root):
    root = Path(root)
    if (root / 'src' / 'dynacomp').is_dir():
        root = root / 'src' / 'dynacomp'
    if not (root / 'generating.py').is_file():
        raise ValueError('DynaComp package source directory required')
    digest = hashlib.sha256()
    for path in sorted(root.glob('*.py')):
        digest.update(path.name.encode() + b'\0' + path.read_bytes() + b'\0')
    return root, digest.hexdigest()


class DynaCompAdapter:
    """Load an explicitly chosen source tree under an isolated package name.

    The digest covers every Python module, not just a user-controlled label.
    Receipts retain it and replay refuses any subsequent byte mismatch.
    """
    def __init__(self, root, expected_digest=None):
        self.root, self.digest = source_digest(root)
        if expected_digest is not None and expected_digest != self.digest:
            raise ValueError('DynaComp source digest mismatch')
        self.package = '_singularity_dynacomp_' + self.digest[:20]
        if self.package not in sys.modules:
            spec = importlib.util.spec_from_file_location(self.package, self.root / '__init__.py', submodule_search_locations=[str(self.root)])
            module = importlib.util.module_from_spec(spec)
            sys.modules[self.package] = module
            spec.loader.exec_module(module)

    def module(self, name):
        if source_digest(self.root)[1] != self.digest:
            raise ValueError('DynaComp source changed since binding')
        if name not in ('generating', 'uniform', 'machine', 'binary64', 'native', 'rational', 'thermal', 'stability', 'fastforward'):
            raise ValueError('Unsupported upstream adapter module')
        return importlib.import_module('.' + name, self.package)

    def binding(self):
        return {'adapter': 'singularity.dynacomp-source/1', 'sha256': self.digest,
                'modules': sorted(p.name for p in self.root.glob('*.py')),
                'scope': 'source bytes, not physical calibration'}


def bundled_adapter():
    path = Path(__file__).resolve().parents[2] / 'handoff/nx36/companion_sources/dynacomp'
    return DynaCompAdapter(path)
