#!/usr/bin/env python3
"""Build the measured-training companion with Pandoc and XeLaTeX."""
import argparse
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
HEADER = r"""
\usepackage{xcolor}
\definecolor{ink}{HTML}{182A45}
\definecolor{accent}{HTML}{087F8C}
\usepackage{fancyhdr}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small\sffamily\color{ink} SINGULARITY / RESEARCH COMPANION}
\fancyhead[R]{\small\sffamily 0.6.0}
\fancyfoot[L]{\small\sffamily Learning, Coordinates, and Observation}
\fancyfoot[R]{\small\sffamily\thepage}
\renewcommand{\headrulewidth}{0.3pt}
\setlength{\headheight}{14pt}
\usepackage{titlesec}
\titleformat{\section}{\Large\sffamily\bfseries\color{ink}}{\thesection}{1em}{}
\titleformat{\subsection}{\large\sffamily\bfseries\color{accent}}{\thesubsection}{1em}{}
\setlength{\emergencystretch}{3em}
\usepackage{needspace}
\let\oldsection\section
\renewcommand{\section}{\Needspace{7\baselineskip}\oldsection}
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'output/pdf/training_observation.pdf')
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='singularity-training-pdf-') as temporary:
        header = Path(temporary)/'header.tex'
        header.write_text(HEADER)
        command = ['pandoc', 'docs/papers/training_observation.md', '--from=markdown',
                   '--pdf-engine=xelatex', '--resource-path=docs/papers:.',
                   '--include-in-header='+str(header)]
        for setting in ('documentclass=article', 'fontsize=10.5pt', 'mainfont=DejaVu Serif',
                        'sansfont=DejaVu Sans', 'monofont=DejaVu Sans Mono',
                        'geometry:margin=0.85in', 'colorlinks=true',
                        'linkcolor=accent', 'urlcolor=accent'):
            command.extend(['-V', setting])
        subprocess.run(command+['-o', str(args.output.resolve())], cwd=ROOT, check=True)
    print(args.output.resolve())


if __name__ == '__main__':
    main()
