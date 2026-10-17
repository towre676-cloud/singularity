#!/usr/bin/env python3
"""Generate a stable identifier index of manuscript result declarations."""
from pathlib import Path
import json
import re

root=Path(__file__).resolve().parents[1]
records=[]
for path in sorted((root/'docs'/'chapters').glob('*.md')):
    for line_number,line in enumerate(path.read_text().splitlines(),1):
        if re.match(r'\*\*(Theorem|Proposition|Corollary|Calculation) ',line):
            for identifier in re.findall(r'SNG-[A-Z]+[0-9]+',line)[:1]:
                records.append({'id':identifier,'declaration':line.replace('**',''),'file':str(path.relative_to(root)),'line':line_number})
assert len({r['id'] for r in records})==len(records)
(root/'results'/'theorem_index.json').write_text(json.dumps({'schema':'singularity.result-index/1','scope':'human-readable theorem/proposition/calculation declarations; not proof-assistant coverage','results':records},indent=2)+'\n')
text='# Result index\n\nStable identifiers connect subsequent development pushes to the precise statements and hypotheses in the authored chapters. A listed proof is mathematical exposition; this index makes no proof-assistant claim.\n\n| Identifier | Declaration | Source |\n|---|---|---|\n'
for record in records:
    text+='| '+record['id']+' | '+record['declaration'].replace('|','\\|')+' | ['+record['file'].split('/')[-1]+']('+record['file'].replace('docs/','',1)+') |\n'
(root/'docs'/'THEOREM_INDEX.md').write_text(text)
print(len(records),'stable declared results indexed')
