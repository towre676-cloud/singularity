#!/usr/bin/env python3
"""Check research-package completeness without network or document dependencies."""
from pathlib import Path
import ast
import json
import re

ROOT=Path(__file__).resolve().parents[1]


def main():
    chapters=sorted((ROOT/'docs'/'chapters').glob('*.md'))
    assert len(chapters)==15, 'Fifteen substantive chapters required'
    words=sum(len(p.read_text().split()) for p in chapters)
    assert words>=30_000, f'Main chapters contain only {words} source words'
    definitions=[]
    for p in chapters:
        for line in p.read_text().splitlines():
            if re.match(r'\*\*(Theorem|Proposition|Corollary|Calculation) ',line):
                identifier=re.search(r'SNG-[A-Z]+[0-9]+',line)
                if identifier:
                    definitions.append(identifier.group())
        assert '\ufffd' not in p.read_text(),f'Replacement glyph in {p}'
    assert len(definitions)==len(set(definitions)), 'Duplicate declared result identifier'
    for p in list((ROOT/'src').rglob('*.py'))+list((ROOT/'scripts').glob('*.py')):
        ast.parse(p.read_text(),filename=str(p))
    required=['README.md','docs/MONOGRAPH.md','docs/monograph.tex','docs/monograph.html','docs/papers/visibility.md','docs/references.bib','docs/development/PUSHES.md','output/pdf/monograph.pdf','output/pdf/visibility_paper.pdf','output/pdf/locality_paper.pdf','docs/papers/locality.md','docs/papers/visibility_claims.md','docs/papers/locality_claims.md','formal-analysis/SingularityAnalysis/SpectralVisibility.lean','results/formal_analysis_audit.json','results/publication_release.json','results/exact_examples.json','results/small_census.json','results/transfer_benchmark.json']
    for name in required:
        p=ROOT/name
        assert p.is_file() and p.stat().st_size>0,f'Missing required file {name}'
    examples=json.loads((ROOT/'results/exact_examples.json').read_text())
    assert [examples['pairs'][name]['first_difference_volume'] for name in ['spectral','binary_census','regular_cube_mobius']]==[2,3,4]
    census=json.loads((ROOT/'results/small_census.json').read_text())
    assert [row['connected_isomorphism_classes'] for row in census['orders']]==[1,1,2,6,21,112]
    benchmark=json.loads((ROOT/'results/transfer_benchmark.json').read_text())
    # The benchmark schema is retained as authored; the independent tests also
    # verify all 96-vertex volume marginals by a closed counting formula.
    assert '2506262962660245' in json.dumps(benchmark)
    print(json.dumps({'status':'passed','main_chapter_source_words':words,'declared_result_ids':len(definitions),'chapters':len(chapters),'required_artifacts':len(required)},sort_keys=True))


if __name__=='__main__':
    main()
