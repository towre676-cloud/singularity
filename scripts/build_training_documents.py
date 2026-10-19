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
    parser.add_argument('--output', type=Path)
    parser.add_argument('--confirmation', action='store_true', help='Build the 0.7.0 confirmed-advantages companion')
    args = parser.parse_args()
    name = 'confirmed_advantages' if args.confirmation else 'training_observation'
    args.output = args.output or ROOT/'output/pdf'/f'{name}.pdf'
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='singularity-training-pdf-') as temporary:
        header = Path(temporary)/'header.tex'
        header_text = HEADER
        if args.confirmation:
            header_text = header_text.replace('0.6.0', '0.7.0').replace(
                'Learning, Coordinates, and Observation', 'Confirmed Prediction and Behavioral Checks')
        header.write_text(header_text)
        command = ['pandoc', f'docs/papers/{name}.md', '--from=markdown',
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
