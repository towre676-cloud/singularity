#!/usr/bin/env python3
"""Compile NX36 semantic theorem and print its actual Lean axiom audit."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--lean');parser.add_argument('--write',action='store_true');args=parser.parse_args()
    lean=args.lean or os.environ.get('LEAN') or shutil.which('lean')or '/tmp/singularity-lean-tools/lean-4.12.0-linux/bin/lean'
    if not Path(lean).is_file():raise SystemExit('Lean4.12 toolchain unavailable; no compiled claim')
    source=ROOT/'formal/Singularity/NXDecision.lean';audit=ROOT/'formal/NXDecisionAudit.lean'
    if re.search(r'^\s*(?:axiom|sorry|admit)\b',source.read_text(),re.M):raise SystemExit('unproved/custom axiom declaration')
    env=dict(os.environ);compat=Path('/tmp/singularity-lean-tools/self_exe_compat.so')
    if compat.is_file():env['LD_PRELOAD']=str(compat)
    with tempfile.TemporaryDirectory(prefix='nx36-lean-')as directory:
        module=Path(directory)/'Singularity';module.mkdir()
        subprocess.run([lean,'-o',str(module/'NXDecision.olean'),str(source)],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
        env['LEAN_PATH']=directory
        result=subprocess.run([lean,str(audit)],cwd=ROOT,env=env,check=True,capture_output=True,text=True)
        output=result.stdout
        if output.count('does not depend on any axioms')!=3:raise SystemExit('unexpected theorem axiom dependencies: '+output)
    version=subprocess.check_output([lean,'--version'],env=env,text=True).strip()
    if 'version 4.12.0,' not in version:raise SystemExit('the pinned Lean4.12.0 compiler is required')
    record={'schema':'nx36.formal-audit/1','lean_version':version,
        'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'audit_sha256':hashlib.sha256(audit.read_bytes()).hexdigest(),'compiled':True,'axiom_audit':output,
        'checker_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'coverage':'abstract semantic strict-gap, pair-separation and finite-catalogue optimality; not Python/parser/model calibration'}
    retained=ROOT/'results/nx36/nx36_formal_audit.json'
    if args.write:retained.write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    elif not retained.is_file()or json.loads(retained.read_text())!=record:
        raise SystemExit('stale or incompatible source-bound formal receipt; regenerate with --write')
    print(json.dumps(record,indent=2,sort_keys=True))

if __name__=='__main__':main()
