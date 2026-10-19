"""Versioned local OEIS snapshots: two acquisition adapters, one parser.

The compiler never talks to the live site.  It reads a **versioned local snapshot** through one of
two adapters, and everything downstream (parser, matching, Lean links) is identical:

* `GitExport`: the official export `https://github.com/oeis/oeisdata.git`, cloned shallow,
  blobless and sparse with `GIT_LFS_SKIP_SMUDGE=1` (the supporting b-files live in Git LFS and are
  not needed).  Its version is the export commit and its `time.txt`.  Entries are added to the
  sparse checkout on demand, so only the candidates are downloaded.
* `SeqDir`: a directory of `.seq` files supplied by hand (for example the PerfectPower handoff
  corpus), laid out as `seq/A123/A123456.seq` or flat; its version is its `manifest.json` if any.

`parse_seq` reads the OEIS internal format (https://oeis.org/eishelp1.html): `%S %T %U` terms,
`%N` name, `%O` offset, `%F` formulas, `%C` comments, `%Y` cross-references, `%K` keywords.
`load_global_index` reads a TSV `id, offset, name, initial_terms` for discovery across every
entry; definitions and offsets are always taken from the full `.seq` text.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

OEISDATA_URL = 'https://github.com/oeis/oeisdata.git'


def seq_path(aid: str) -> str:
    """`A123456` -> `seq/A123/A123456.seq`."""
    return f'seq/{aid[:4]}/{aid}.seq'


@dataclass
class Entry:
    id: str
    offset: int
    terms: list[int]
    name: str
    formulas: list[str] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    xrefs: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    text: str = ''

    def term(self, n: int) -> int:
        """a(n) in the entry's own indexing."""
        return self.terms[n - self.offset]

    def indexed(self) -> list[tuple[int, int]]:
        return [(self.offset + i, t) for i, t in enumerate(self.terms)]


def parse_seq(text: str) -> Entry:
    lines: dict[str, list[str]] = {}
    aid = None
    for line in text.splitlines():
        m = re.match(r'%(\w) (A\d{6}) ?(.*)$', line)
        if not m:
            continue
        tag, aid, rest = m.groups()
        lines.setdefault(tag, []).append(rest)
    if aid is None:
        raise ValueError('not an OEIS entry')
    raw = ''.join(lines.get('S', []) + lines.get('T', []) + lines.get('U', []))
    terms = [int(t) for t in raw.replace(' ', '').strip(',').split(',') if t]
    off = int(lines['O'][0].split(',')[0]) if 'O' in lines else 0
    return Entry(id=aid, offset=off, terms=terms, name=' '.join(lines.get('N', [''])),
                 formulas=lines.get('F', []), comments=lines.get('C', []),
                 xrefs=lines.get('Y', []), keywords=','.join(lines.get('K', [''])).split(','),
                 text=text)


def load_global_index(path) -> dict[str, tuple[int, str, list[int]]]:
    """`id  offset  name  initial_terms` (TSV) -> {id: (offset, name, terms)}."""
    out = {}
    with open(path, encoding='utf-8', errors='replace') as f:
        next(f, None)
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) < 4:
                continue
            aid, off, name, terms = parts[:4]
            try:
                parts_t = [t for t in terms.split(',') if t]
                if parts_t and not terms.endswith(','):
                    parts_t = parts_t[:-1]          # the index truncates its term strings
                ts = [int(t) for t in parts_t]
                o = int(off.split(',')[0])
            except ValueError:
                continue
            out[aid] = (o, name, ts)
    return out


class SeqDir:
    """A hand-supplied directory of `.seq` files."""

    def __init__(self, root):
        self.root = Path(root)

    def version(self) -> dict:
        m = self.root / 'manifest.json'
        info = json.loads(m.read_text()) if m.exists() else {}
        return {'adapter': 'SeqDir', **{k: v for k, v in info.items() if k != 'files'}}

    def text(self, aid: str) -> str | None:
        for p in (self.root / seq_path(aid), self.root / f'{aid}.seq'):
            if p.exists():
                return p.read_text(encoding='utf-8')
        return None

    def ensure(self, ids) -> None:
        pass


class GitExport:
    """A shallow, blobless, sparse clone of the official export."""

    def __init__(self, root, url: str = OEISDATA_URL):
        self.root = Path(root)
        self.url = url

    def _git(self, *args, check=True):
        env = {**os.environ, 'GIT_LFS_SKIP_SMUDGE': '1'}
        return subprocess.run(['git', *args], cwd=self.root, env=env, capture_output=True,
                              text=True, check=check)

    def clone(self) -> None:
        if (self.root / '.git').exists():
            return
        self.root.parent.mkdir(parents=True, exist_ok=True)
        env = {**os.environ, 'GIT_LFS_SKIP_SMUDGE': '1'}
        subprocess.run(['git', 'clone', '--depth', '1', '--filter=blob:none', '--sparse', self.url,
                        str(self.root)], env=env, check=True, capture_output=True, text=True)
        self._git('sparse-checkout', 'set', '--no-cone', '/time.txt', '/README.md', '/LICENSE')

    def ensure(self, ids) -> None:
        missing = [seq_path(a) for a in ids if not (self.root / seq_path(a)).exists()]
        if missing:
            self._git('sparse-checkout', 'add', *['/' + m for m in missing])

    def version(self) -> dict:
        commit = self._git('rev-parse', 'HEAD').stdout.strip()
        date = self._git('log', '-1', '--format=%cI').stdout.strip()
        t = (self.root / 'time.txt')
        return {'adapter': 'GitExport', 'url': self.url, 'commit': commit, 'commit_date': date,
                'time_txt': t.read_text().strip() if t.exists() else None}

    def text(self, aid: str) -> str | None:
        p = self.root / seq_path(aid)
        return p.read_text(encoding='utf-8') if p.exists() else None
