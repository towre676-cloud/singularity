#!/usr/bin/env python3
"""Assemble the monograph, article, HTML and mathematical PDFs with Pandoc."""
import base64
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]

STYLE='''
body{margin:0;background:#f3f0e8;color:#212c34;font:18px/1.7 Georgia,serif}main,body>section,body>header{max-width:1100px;margin:auto}body{padding:4vw 7vw}h1,h2,h3{font-family:system-ui,sans-serif;line-height:1.25;color:#183c50}h1{margin-top:3em;border-bottom:2px solid #bea16d;padding-bottom:.4em}h2{margin-top:2.2em}p{max-width:92ch}a{color:#126084}table{border-collapse:collapse;width:100%;font-size:.87em;line-height:1.45;margin:2em 0;background:#fffdf7}th{background:#e1e9e8;text-align:left}td,th{border:1px solid #bdc9c7;padding:10px;vertical-align:top}pre{overflow:auto;background:#e7ebea;padding:1em;font-size:.8em}code{font-size:.88em}.math.display{display:block;overflow:auto;padding:.6em 0}#TOC{background:#e6e9e2;border-left:4px solid #b2945d;padding:1em 2em;columns:2;font-size:.85em}#TOC ul{break-inside:avoid}img{max-width:100%;height:auto}header p{font-family:system-ui,sans-serif}blockquote{border-left:3px solid #b2945d;padding-left:1em}@media(max-width:800px){body{padding:20px;font-size:17px}#TOC{columns:1}table{display:block;overflow:auto}}@media print{body{background:white;padding:0;font-size:11pt}#TOC{columns:1}h1,h2,h3{break-after:avoid}tr{break-inside:avoid}}
'''

HEADER=r'''
\usepackage{amsmath,amssymb,booktabs,longtable,array,etoolbox,xurl,fvextra,graphicx}
\graphicspath{{docs/}}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small Singularity: Relational Heights and Arithmetic Visibility}
\fancyfoot[C]{\thepage}
\setlength{\headheight}{15pt}
\setlength{\emergencystretch}{3em}
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.12}
\AtBeginEnvironment{longtable}{\footnotesize\everymath{\scriptstyle}}
\fvset{breaklines=true,breakanywhere=true}
\allowdisplaybreaks
\makeatletter
\renewcommand*\l@section{\@dottedtocline{1}{1.5em}{3.6em}}
\renewcommand*\l@subsection{\@dottedtocline{2}{3.8em}{4em}}
\renewcommand*\@pnumwidth{2.5em}
\renewcommand*\@tocrmarg{3.5em}
\makeatother
\AtBeginDocument{\hypersetup{colorlinks=true,linkcolor=teal,urlcolor=teal}}
'''


def run(command,log):
    result=subprocess.run(command,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    log.write_text(log.read_text()+result.stdout if log.exists() else result.stdout)
    if result.returncode:
        raise RuntimeError('Document build failed: '+' '.join(command)+'\n'+result.stdout[-9000:])


def normalize_headings(text):
    return re.sub(r'^(#{1,6})\s+\d+(?:\.\d+)*\.?\s+',r'\1 ',text,flags=re.M)


def render(source,stem,title,subtitle,book=False,pdf=True):
    tmp=ROOT/'tmp'/'build';tmp.mkdir(parents=True,exist_ok=True)
    output=ROOT/'output'/'pdf';output.mkdir(parents=True,exist_ok=True)
    header=tmp/'header.tex';header.write_text(HEADER)
    css=tmp/'style.css';css.write_text(STYLE)
    log=tmp/(stem+'.log');log.write_text('')
    if not book:
        article=source.read_text()
        article=article[article.index('## Abstract'):]
        article=normalize_headings(article)
        article=re.sub(r'^## ', '# ',article,flags=re.M)
        article=article.replace('# Abstract\n','# Abstract {.unnumbered}\n').replace('# References\n','# References {.unnumbered}\n')
        source=tmp/'article.md';source.write_text(article)
    common=['pandoc',str(source),'--from=markdown+tex_math_single_backslash+tex_math_dollars+pipe_tables','--standalone','--number-sections','--resource-path=.:docs:docs/assets','--metadata','title='+title,'--metadata','subtitle='+subtitle,'--metadata','author=Singularity project contributors','--metadata','date=17 October 2026']
    if book:
        common+=['--toc','--toc-depth=2']
    tex=ROOT/'docs'/(stem+'.tex')
    run(common+['--to=latex','--top-level-division='+('chapter' if book else 'section'),'-V','documentclass='+('report' if book else 'article'),'-V','fontsize=11pt','-V','papersize=a4','-V','geometry:margin=22mm','-V','mainfont=DejaVu Serif','-V','sansfont=DejaVu Sans','-V','monofont=DejaVu Sans Mono','--include-in-header',str(header),'-o',str(tex)],log)
    for _ in range(2 if pdf else 0):
        run(['xelatex','-interaction=nonstopmode','-halt-on-error','-output-directory',str(output),str(tex)],log)
    html=ROOT/'docs'/(stem+'.html')
    run(common+['--to=html5','--mathml','--css',str(css),'-o',str(html)],log)
    content=html.read_text()
    content=re.sub(r'<link rel="stylesheet" href="[^"]*style.css"\s*/?>','<style>'+STYLE+'</style>',content)
    for image_path in (ROOT/'docs'/'assets').glob('*.png'):
        data='data:image/png;base64,'+base64.b64encode(image_path.read_bytes()).decode()
        content=content.replace('src="docs/assets/'+image_path.name+'"','src="'+data+'"').replace('src="assets/'+image_path.name+'"','src="'+data+'"')
    html.write_text(content)
    print(f'Built {stem}: '+(str(output/(stem+'.pdf')) if pdf else 'LaTeX and HTML only; PDF left unchanged'),flush=True)


def main():
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-pdf',action='store_true',help='regenerate Markdown, LaTeX and HTML without XeLaTeX; retained PDFs become stale')
    pdf=not parser.parse_args().no_pdf
    chapters=sorted((ROOT/'docs'/'chapters').glob('*.md'))
    if len(chapters)!=14:
        raise ValueError('Exactly fourteen authored chapters required')
    preface='''# Reading guide {.unnumbered}

This monograph develops a precise question: how much of a relation structure can be recovered from integer-height populations, and where does its first hidden difference appear in arithmetic? Chapters 1-4 establish the objects and finite observation hierarchy. Chapters 5-8 develop primewise assembly, local analytic comparison and singular synchronization. Chapters 9-11 give exact examples, inverse questions and the bridges to earlier work. Chapters 12-14 develop computational methodology, the research program and the literature. The implementation appendix states what version 0.1.0 actually executes. The final roadmap defines thirty-six subsequent development pushes.

The central distinction is between an observation and the correspondence it forgets. A binary census can agree for every subset size and boundary size while a nested-height census differs. The arithmetic lift retains these local distinctions and turns the first discrepancy into a controlled ratio singularity. It adds analytic structure rather than new graph information. The full marked hierarchy explicitly contains the binary sector; complete graph reconstruction remains a research question.

Definitions and theorems are supplied with hypotheses and proofs. Finite graph calculations have explicit inputs and independently replayable outputs. Established antecedents are attributed in the literature chapter and bibliography. The book is a research foundation and executable companion, not a claim of a completed priority search or unrestricted reconstruction.

![Exact reference graphs. Top: equal Laplacian spectra. Bottom: equal complete binary cut-volume census. Vertex labels remain original.](assets/graph_pairs.png)

'''
    parts=[preface]+[normalize_headings(p.read_text()) for p in chapters]
    parts += [normalize_headings((ROOT/'docs'/'IMPLEMENTATION.md').read_text()),normalize_headings((ROOT/'docs'/'development'/'PUSHES.md').read_text())]
    manuscript=ROOT/'docs'/'MONOGRAPH.md';manuscript.write_text('\n\n'.join(part.strip() for part in parts)+'\n')
    counts={str(p.relative_to(ROOT)):len(p.read_text().split()) for p in chapters}
    counts['docs/IMPLEMENTATION.md']=len((ROOT/'docs'/'IMPLEMENTATION.md').read_text().split())
    counts['docs/development/PUSHES.md']=len((ROOT/'docs'/'development'/'PUSHES.md').read_text().split())
    report={'schema':'singularity.manuscript-count/1','count_method':'whitespace-delimited source words; equations and tables included','source_word_counts':counts,'source_total':sum(counts.values()),'assembled_monograph_words':len(manuscript.read_text().split()),'companion_article_words':len((ROOT/'docs'/'papers'/'visibility.md').read_text().split())}
    (ROOT/'results'/'manuscript_counts.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    render(manuscript,'monograph','Singularity','Relational Heights and Arithmetic Visibility - Research Monograph',book=True,pdf=pdf)
    render(ROOT/'docs'/'papers'/'visibility.md','visibility_paper','Relational Height Populations and Arithmetic Visibility','Exact examples, nested boundaries, and primewise singularities',pdf=pdf)
    print('Monograph source words:',report['assembled_monograph_words'])


if __name__=='__main__':
    main()
