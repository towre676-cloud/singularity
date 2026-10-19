#!/usr/bin/env python3
"""Build the implemented NX36 mathematical companion from accepted evidence."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_documents as builder


def source_paths():
    roadmap = json.loads((ROOT / 'handoff/nx36/roadmap.json').read_text())
    names = ['docs/research/NX36_IMPLEMENTATION.md']
    for track in roadmap['tracks']:
        for unit in track['pushes']:
            for name in unit.get('evidence', {}).get('artifacts', []):
                if name.startswith('docs/research/') and name.endswith('.md') and name not in names:
                    names.append(name)
    names += ['handoff/nx36/recovery/INDEPENDENT_REVIEW.md',
              'handoff/nx36/recovery/CLAUDE_AUDIT.md']
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-pdf', action='store_true')
    args = parser.parse_args()
    names = source_paths()
    if len(names) < 25:
        raise SystemExit('Expected accepted mathematical notes across all NX36 groups')
    counts = {}; hashes = {}; parts = []
    for name in names:
        path = ROOT / name
        text = path.read_text()
        if '\ufffd' in text:
            raise SystemExit('Replacement glyph in ' + name)
        counts[name] = len(text.split())
        hashes[name] = hashlib.sha256(path.read_bytes()).hexdigest()
        # Preserve authored sources. Some historical notes use mathematical
        # Unicode in prose; supply the missing print glyphs as actual math.
        text = text.replace('⪰', r'\(\succeq\)').replace('∎', r'\(\square\)')
        text = text.replace('Source: src/singularity/forecast_targets.py.',
                            'Source: `src/singularity/forecast_targets.py`.')
        text = re.sub(r'\\rm\s+([A-Za-z]+)', r'\\mathrm{\1}', text)
        text = re.sub(r'(?<![`\w])([0-9a-f]{64})(?![`\w])', r'`\1`', text)
        text = re.sub(r'(?<=\s)(https?://[^\s)>`]+)', lambda m:
                      '<' + m.group(1).rstrip('.,;') + '>'
                      + m.group(1)[len(m.group(1).rstrip('.,;')):], text)
        parts.append(builder.assembled_links(text, path))
    source = ROOT / 'docs/NX36_MANUSCRIPT.md'
    source.write_text('\n\n'.join(part.strip() for part in parts) + '\n')
    builder.HEADER = builder.HEADER.replace(
        'Singularity: Relational Heights and Arithmetic Visibility',
        'Singularity: Certified Experiments and Observable States')
    builder.HEADER += '\n' + r'\usepackage{adjustbox}' + '\n'
    original_run = builder.run
    def fitted_run(command, log):
        result = original_run(command, log)
        if command[0] == 'pandoc' and '--to=latex' in command:
            tex = ROOT / 'docs/nx36_implementation.tex'
            body = tex.read_text().replace(r'\^{}', r'\textasciicircum{}')
            body = body.replace(r'\begin{split}', r'\begin{aligned}').replace(
                r'\end{split}', r'\end{aligned}')
            # Preserve long formulas while shrinking only those wider than
            # the text block. Short equations retain the ordinary font size.
            body = re.sub(r'\\\[(.*?)\\\]', lambda m:
                          '\\begin{center}\n\\begin{adjustbox}{max width=\\linewidth}\n'
                          '$\\displaystyle ' + m.group(1) + '$\n'
                          '\\end{adjustbox}\n\\end{center}', body, flags=re.S)
            tex.write_text('\n'.join(line.rstrip() for line in body.splitlines()) + '\n')
        return result

    builder.run = fitted_run
    builder.render(source, 'nx36_implementation',
                   'Singularity: Certified Experiments and Observable States',
                   'NX36 implementation companion: proofs, contracts, pilots and limits',
                   book=True, pdf=not args.no_pdf, date='19 October 2026')
    report = {'schema': 'singularity.nx36-manuscript/1',
              'source_word_counts': counts, 'source_sha256': hashes,
              'source_words': sum(counts.values()),
              'count_method': 'whitespace-delimited source words; mathematics included',
              'baseline_monograph_modified': False}
    (ROOT / 'results/nx36_manuscript.json').write_text(
        json.dumps(report, sort_keys=True, indent=2) + '\n')
    print(json.dumps({'sources': len(names), 'words': report['source_words']}))


if __name__ == '__main__':
    main()
