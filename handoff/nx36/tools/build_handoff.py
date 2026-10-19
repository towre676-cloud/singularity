#!/usr/bin/env python3
"""Build the NX36 planning ledger, readable handbook, and complete source ZIP.

Core assembly and packaging use the standard library. PDF/HTML rendering needs
Pandoc and XeLaTeX; the PDF build deliberately fails on malformed mathematics.
"""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parent.parent
BASELINE = "438ed423d7d389a1a483c61e0b50eca6a9fc0827"
BASE_TREE = "47a88f7b9ebf4fc24bf2c8cf589ebd9ed3ab87b0"
IDS = [f"NX{i:02d}" for i in range(1, 37)]
SOFTEN = {"NX20": ["NX19"], "NX21": ["NX07", "NX13"],
          "NX22": ["NX14"], "NX24": ["NX13", "NX14"], "NX32": ["NX31"]}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(command, *, cwd=REPO):
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True)
    if result.returncode:
        raise RuntimeError("Command failed: " + " ".join(map(str, command)) + "\n" + result.stdout[-2500:] + result.stderr[-6500:])
    return result

def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

def mathematical_code(text):
    """Typeset the packets' short ASCII mathematical code as actual equations.

    Source paths and API names stay code. Only inline spans containing a
    power symbol are converted; code fences remain unchanged.
    """
    def replace(match):
        value = match.group(1)
        if "^" not in value:
            return match.group(0)
        fixed = {"W_b^0=span_Q{L_bj}": r"W_b^0=\operatorname{span}_{\mathbb Q}\{L_{bj}\}",
                 "||p||^2=c^T G c": r"\lVert p\rVert^2=c^{\mathsf T}Gc"}
        if value in fixed:
            return "\\(" + fixed[value] + "\\)"
        for old, new in [("epsilon", r"\epsilon"), ("eta", r"\eta"), ("Delta", r"\Delta"),
                         ("sum_h", r"\sum_h"), ("binom(j,c)", r"\binom{j}{c}"),
                         ("|h|", r"\lvert h\rvert"), ("|D|", r"\lvert D\rvert"),
                         ("Q^", r"\mathbb Q^"), ("R0", "R_0"), ("A0", "A_0"),
                         ("x0", "x_0"), ("F1", "F_1"), ("F0", "F_0"),
                         ("<=", r"\le"), ("^T", r"^{\mathsf T}")]:
            value = value.replace(old, new)
        value = re.sub(r"\blog\b", lambda _: r"\log", value)
        value = re.sub(r"\^(-?\d+)", lambda m: "^{" + m.group(1) + "}", value)
        return "\\(" + value + "\\)"
    return re.sub(r"(?<!`)`([^`\n]+)`(?!`)", replace, text)

def portable_source_paths(text):
    """Wrap bare source paths, without corrupting existing code spans."""
    parts = re.split(r"(```[\s\S]*?```|`[^`\n]*`)", text)
    pattern = r"(?<![A-Za-z0-9_/:])((?:src|tests|docs|formal|scripts|handoff)/[A-Za-z0-9_./-]+\.(?:py|md|json|lean))"
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(pattern, r"`\1`", parts[i])
    return "".join(parts)

def assemble():
    tracks = []
    for group in "abcdef":
        source = HERE / "packets" / f"group_{group}.json"
        records = json.loads(source.read_text(encoding="utf-8"))
        if not isinstance(records, list) or len(records) != 6:
            raise ValueError(f"Six records required in {source}")
        tracks.extend(records)
    if sorted(t["id"] for t in tracks) != IDS:
        raise ValueError("Exactly NX01..NX36 required")
    tracks.sort(key=lambda t: t["id"])
    for t in tracks:
        t["status"] = "proposed"
        t["packet"] = f"packets/{t['id']}.md"
        t["execution_rank"] = IDS.index(t["id"]) + 1
        t["supporting_tracks"] = SOFTEN.get(t["id"], [])
        t["depends_on"] = [d for d in t.get("depends_on", []) if d not in t["supporting_tracks"]]
        for field in ("existing_sources", "proposed_sources", "acceptance"):
            t[field] = list(t.get(field, []))
        t["priority"] = str(t.get("priority", "P2"))
        for i, u in enumerate(t["pushes"]):
            u["status"] = "proposed"
            if isinstance(u.get("acceptance"), str):
                u["acceptance"] = [u["acceptance"]]
            u["depends_on"] = ([d + "-C" for d in t["depends_on"]] if i == 0 else [t["pushes"][i-1]["id"]])
    roadmap = {"schema": "singularity.nx-roadmap/1", "baseline_commit": BASELINE,
               "planning_only": True, "tracks": tracks,
               "dependency_note": "Hard dependencies are executable prerequisites. Supporting tracks are useful integrations, not blockers for a narrow first result. All shipped units are proposed."}
    # Do not silently erase future implementation evidence by rerunning assembly.
    target = HERE / "roadmap.json"
    if target.exists():
        old = json.loads(target.read_text())
        if any(t.get("status") != "proposed" or any(u.get("status") != "proposed" for u in t.get("pushes", [])) for t in old.get("tracks", [])):
            raise RuntimeError("Refusing to reset a progressed roadmap; preserve its evidence and regenerate documents separately")
    write_json(target, roadmap)
    with (HERE / "ROADMAP.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["id", "title", "priority", "status", "hard_dependencies", "supporting_tracks", "packet", "pushes"])
        for t in tracks:
            writer.writerow([t["id"], t["title"], t["priority"], t["status"], ";".join(t["depends_on"]), ";".join(t["supporting_tracks"]), t["packet"], ";".join(u["id"] for u in t["pushes"])])
    with (HERE / "PUSHES.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.writer(stream)
        writer.writerow(["unit", "track", "title", "status", "dependencies", "acceptance"])
        for t in tracks:
            for u in t["pushes"]:
                writer.writerow([u["id"], t["id"], u["title"], u["status"], ";".join(u["depends_on"]), "\n".join(u["acceptance"])])
    api = []
    for source in sorted((REPO / "src/singularity").glob("*.py")):
        tree = ast.parse(source.read_text())
        names = []
        for node in tree.body:
            if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and not node.name.startswith("_"):
                item = {"kind": type(node).__name__, "name": node.name, "line": node.lineno}
                if isinstance(node, ast.ClassDef):
                    item["methods"] = [n.name for n in node.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
                names.append(item)
        api.append({"path": source.relative_to(REPO).as_posix(), "sha256": digest(source), "symbols": names})
    write_json(HERE / "provenance/SOURCE_API_INDEX.json", {"scope": "AST inventory, not an API correctness proof", "modules": api})
    table = ["# Execution map\n", "The ledger is authoritative for hard dependencies. Historical or packet prose links can be supporting connections. All 108 units initially remain proposed.\n", "| Track | Design | Hard prerequisites | Supporting tracks | Units |", "|---|---|---|---|---|"]
    for t in tracks:
        table.append(f"| {t['id']} | {t['title']} | {', '.join(t['depends_on']) or 'None'} | {', '.join(t['supporting_tracks']) or 'None'} | A / B / C |")
    (HERE / "EXECUTION_MAP.md").write_text("\n".join(table) + "\n")
    files = [HERE / "START_HERE.md", HERE / "CLAUDE_START_PROMPT.md",
             HERE / "architecture/PROGRAM_DESIGN.md", HERE / "architecture/SOURCE_REUSE.md",
             HERE / "architecture/INTERCHANGE_CONTRACT.md", HERE / "EXECUTION_MAP.md"]
    files += [HERE / f"packets/{id}.md" for id in IDS]
    files += [HERE / "provenance/HISTORICAL_BRIDGES.md", HERE / "architecture/RECOVERY_AND_RELEASE.md",
              HERE / "validation/PACKET_MATH_REVIEW.md", HERE / "validation/CROSS_TRACK_REVIEW.md"]
    parts = ["# Reading guide {.unnumbered}\n\nThis is the enriched Claude Code implementation handoff for 36 new expansion tracks and 108 acceptance units. It supplies mathematical designs, conceptual explanations, worked examples, source reuse and bounded implementation gates. Proposed results are not presented as completed work. The complete executable baseline and companion selections travel with the archive.\n"]
    for f in files:
        text = f.read_text(encoding="utf-8")
        text = text.replace("\\( ", "\\(").replace(" \\)", "\\)")
        text = portable_source_paths(text).translate(str.maketrans({"—": "-", "–": "-", "‑": "-"}))
        parts.append(mathematical_code(text))
    book = "\n\n".join(parts)
    (HERE / "HANDBOOK.md").write_text(book, encoding="utf-8")
    counts = {id: len(re.findall(r"\S+", (HERE / f"packets/{id}.md").read_text())) for id in IDS}
    report = {"schema": "singularity.nx-build/1", "tracks": len(tracks), "push_units": sum(len(t["pushes"]) for t in tracks),
              "packet_words": counts, "packet_words_total": sum(counts.values()), "handbook_words": len(re.findall(r"\S+", book)),
              "baseline_commit": BASELINE, "baseline_tree": BASE_TREE, "status": "planning package, all NX units proposed"}
    write_json(HERE / "BUILD_REPORT.json", report)
    print(json.dumps(report, indent=2))

HEADER = r"""\usepackage{amsmath,amssymb,booktabs,longtable,array,etoolbox,xurl,fvextra,seqsplit,fancyhdr}
\let\nxtexttt\texttt
\renewcommand{\texttt}[1]{\nxtexttt{\seqsplit{#1}}}
\pagestyle{fancy}
\fancyhf{}
\fancyhead[L]{\small Singularity | NX36 Expansion Handbook}
\fancyhead[R]{\small Claude Code handoff}
\fancyfoot[C]{\thepage}
\setlength{\headheight}{15pt}
\setlength{\emergencystretch}{4em}
\setlength{\tabcolsep}{3pt}
\renewcommand{\arraystretch}{1.12}
\AtBeginEnvironment{longtable}{\footnotesize\everymath{\scriptstyle}}
\fvset{breaklines=true,breakanywhere=true}
\allowdisplaybreaks
\makeatletter
\renewcommand*\@pnumwidth{2.8em}
\renewcommand*\@tocrmarg{3.8em}
\makeatother
\AtBeginDocument{\hypersetup{colorlinks=true,linkcolor=teal,urlcolor=teal}}
""".replace("\\+", "")

STYLE = """body{margin:0;padding:4vw 7vw;background:#f5f1e9;color:#1e303c;font:18px/1.65 Georgia,serif}body>*{max-width:1120px;margin-left:auto;margin-right:auto}h1,h2,h3{font-family:system-ui,sans-serif;color:#174658;line-height:1.25}h1{margin-top:3em;border-bottom:2px solid #c6a878;padding-bottom:.4em}table{border-collapse:collapse;font-size:.83em;background:#fffdf8}td,th{border:1px solid #c8d1cf;vertical-align:top;padding:.6em}th{background:#dfeae7}code{font-size:.84em;overflow-wrap:anywhere}pre{background:#e7ece8;padding:1em;overflow:auto}.math.display{display:block;overflow:auto;padding:.5em 0}#TOC{border-left:4px solid #b59a6b;background:#e7e9df;padding:1em 2em;columns:2;font-size:.82em}a{color:#116281}@media(max-width:760px){body{padding:18px;font-size:17px}table{display:block;overflow:auto}#TOC{columns:1}}"""

def render():
    output = HERE / "output"
    output.mkdir(exist_ok=True)
    work = REPO / "tmp/nx36-build"
    work.mkdir(parents=True, exist_ok=True)
    header = work / "header.tex"
    header.write_text(HEADER)
    source = HERE / "HANDBOOK.md"
    common = ["pandoc", str(source), "--from=markdown+tex_math_single_backslash+tex_math_dollars+pipe_tables",
              "--standalone", "--toc", "--toc-depth=1", "--metadata", "title=Singularity: The Next 36 Expansions",
              "--metadata", "subtitle=Equation-rich designs and 108 implementation pushes for Claude Code",
              "--metadata", "author=Singularity project", "--metadata", "date=19 October 2026"]
    tex = output / "HANDBOOK.tex"
    result = run(common + ["--to=latex", "--top-level-division=chapter", "-V", "documentclass=report",
                          "-V", "fontsize=11pt", "-V", "papersize=a4", "-V", "geometry:margin=22mm",
                          "-V", "mainfont=DejaVu Serif", "-V", "sansfont=DejaVu Sans", "-V", "monofont=DejaVu Sans Mono",
                          "--include-in-header", str(header), "-o", str(tex)])
    logs = [result.stderr]
    for suffix in (".aux", ".toc", ".out"):
        (work / ("HANDBOOK" + suffix)).unlink(missing_ok=True)
    for _ in range(2):
        result = run(["xelatex", "-no-pdf", "-interaction=nonstopmode", "-halt-on-error", "-output-directory", str(work), str(tex)])
        logs.append(result.stdout + result.stderr)
    run(["xdvipdfmx", "-o", str(HERE / "HANDBOOK.pdf"), str(work / "HANDBOOK.xdv")])
    (HERE / "validation/PDF_BUILD.log").write_text("\n".join(logs))
    html = run(common + ["--to=html5", "--mathml"]).stdout
    if "</html>" not in html or "NX36" not in html:
        raise RuntimeError("Incomplete handbook HTML")
    html = html.replace("</head>", "<style>" + STYLE + "</style></head>")
    (HERE / "HANDBOOK.html").write_text(html, encoding="utf-8")
    info = run(["pdfinfo", str(HERE / "HANDBOOK.pdf")]).stdout
    report = json.loads((HERE / "BUILD_REPORT.json").read_text())
    report["pdf_pages"] = int(re.search(r"^Pages:\s+(\d+)", info, re.M).group(1))
    report["pdf_sha256"] = digest(HERE / "HANDBOOK.pdf")
    report["pdf_bytes"] = (HERE / "HANDBOOK.pdf").stat().st_size
    write_json(HERE / "BUILD_REPORT.json", report)
    print(info)

def package(output, bundle):
    output = Path(output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    bundle = Path(bundle).resolve()
    if not bundle.is_file():
        raise RuntimeError("A complete baseline Git bundle is required")
    entries = {}
    tracked = run(["git", "ls-files", "-z"]).stdout.split("\0")
    for rel in tracked:
        if not rel or rel.startswith(("releases/", "handoff/nx36/")):
            continue
        p = REPO / rel
        if p.is_file():
            entries["repository/" + rel] = p
    for p in HERE.rglob("*"):
        if not p.is_file() or any(v in p.parts for v in ("__pycache__", ".pytest_cache")) or p.name in ("_github_records.json", "_dynacomp_records.json"):
            continue
        entries["repository/" + p.relative_to(REPO).as_posix()] = p
    entries["baseline/Singularity-v040-baseline.bundle"] = bundle
    entries["Singularity-NX36-Expansion-Handbook.pdf"] = HERE / "HANDBOOK.pdf"
    entries["CLAUDE_START_PROMPT.md"] = HERE / "CLAUDE_START_PROMPT.md"
    entries["START.py"] = HERE / "tools/start_handoff.py"
    entries["Start-Handoff.ps1"] = HERE / "tools/Start-Handoff.ps1"
    outer = ("# Singularity NX36 Claude Code handoff\n\nOpen `repository/` in Claude Code, then read `handoff/nx36/START_HERE.md`. "
             "Paste `CLAUDE_START_PROMPT.md` into the session. This ZIP includes all 36 enriched packets, 108 proposed acceptance units, "
             "the complete baseline source snapshot, pinned companion reference code, the rendered handbook, and an offline baseline Git bundle.\n\n"
             "The baseline monograph is `repository/output/pdf/monograph.pdf`. The new expansion handbook is `Singularity-NX36-Expansion-Handbook.pdf`. "
             "All future NX work is proposed; its designs are not claims of implementation.\n\n"
             "Run `python repository/handoff/nx36/tools/handoff.py verify` from this outer folder. "
             "For offline Git recovery see `repository/handoff/nx36/architecture/RECOVERY_AND_RELEASE.md`. "
             "Never overwrite or force-push a newer checkout.\n")
    payloads = {"START_HERE.md": outer.encode()}
    manifest = {"schema": "singularity.nx-package/1", "baseline_commit": BASELINE,
                "baseline_tree": BASE_TREE, "tracks": 36, "push_units": 108, "files": []}
    for name, p in sorted(entries.items()):
        manifest["files"].append({"path": name, "bytes": p.stat().st_size, "sha256": digest(p)})
    for name, b in payloads.items():
        manifest["files"].append({"path": name, "bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()})
    payloads["PACKAGE_MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()
    prefix = "Singularity-NX36-Claude-Handoff/"
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as z:
        for name, p in sorted(entries.items()):
            z.write(p, prefix + name)
        for name, data in payloads.items():
            z.writestr(prefix + name, data)
    with zipfile.ZipFile(output) as z:
        if z.testzip() is not None:
            raise RuntimeError("ZIP CRC failure")
        for item in manifest["files"]:
            b = z.read(prefix + item["path"])
            if len(b) != item["bytes"] or hashlib.sha256(b).hexdigest() != item["sha256"]:
                raise RuntimeError("Archived hash mismatch: " + item["path"])
    report = {"archive": str(output), "bytes": output.stat().st_size, "sha256": digest(output),
              "members": len(entries) + len(payloads), "manifest_entries": len(manifest["files"])}
    write_json(output.with_suffix(".report.json"), report)
    print(json.dumps(report, indent=2))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("assemble", "render", "package"))
    parser.add_argument("--output")
    parser.add_argument("--bundle")
    args = parser.parse_args()
    if args.command == "assemble":
        assemble()
    elif args.command == "render":
        render()
    else:
        if not args.output or not args.bundle:
            parser.error("package needs --output and --bundle")
        package(args.output, args.bundle)

if __name__ == "__main__":
    main()
