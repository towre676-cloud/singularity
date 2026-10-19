"""Private rebuild and axiom audit for explicitly selected proved-family sources."""
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .resources import runtime_root


def check_rebuilt(expected, modules, audits, *, lean=None, lean_path=None, timeout=120):
    if type(timeout) not in (int,float) or not 0 < timeout <= 600:
        raise ValueError('timeout must be positive and at most 600 seconds')
    binary=lean or os.environ.get('PERFECTPOWER_LEAN') or shutil.which('lean')
    external=lean_path if lean_path is not None else os.environ.get('LEAN_PATH','')
    if not binary or not external:
        return dict(accepted=False,reason='Lean 4.20.0 and pinned Mathlib on LEAN_PATH required')
    libraries={name:runtime_root()/f'PerfectPower/{name}.lean' for name in modules}
    if any(not p.is_file() for p in libraries.values()):
        return dict(accepted=False,reason='proved-family source libraries unavailable')
    try:
        version=subprocess.run([binary,'--version'],capture_output=True,text=True,timeout=timeout,check=True).stdout.strip()
        if not version.startswith('Lean (version 4.20.0,'):
            return dict(accepted=False,reason='Lean 4.20.0 required',version=version)
        logs=[]
        with tempfile.TemporaryDirectory(prefix='pp-proved-family-') as directory:
            root=Path(directory);(root/'PerfectPower').mkdir()
            commands=[]
            for name,path in libraries.items():
                local=root/f'PerfectPower/{name}.lean';local.write_bytes(path.read_bytes())
                commands.append([binary,str(local),'-o',str(local.with_suffix('.olean'))])
            query=root/'Query.lean';query.write_text(expected['lean'],encoding='utf-8')
            audit=root/'SourceAudit.lean';audit.write_text(
                ''.join(f'import PerfectPower.{name}\n' for name in modules)+
                ''.join(f'#print axioms PerfectPower.{name}\n' for name in audits),encoding='utf-8')
            commands += [[binary,str(audit)],[binary,str(query)]]
            environment=dict(os.environ,LEAN_PATH=str(root)+os.pathsep+external)
            for command in commands:
                run=subprocess.run(command,cwd=root,env=environment,capture_output=True,text=True,timeout=timeout)
                log=run.stdout+run.stderr;logs.append(log)
                axioms=[v.strip() for row in re.findall(r'depends on axioms: \[([^\]]*)\]',log)
                        for v in row.split(',') if v.strip()]
                if run.returncode or 'sorry' in log or 'ofReduceBool' in log or any(
                        v not in {'propext','Classical.choice','Quot.sound'} for v in axioms):
                    return dict(accepted=False,reason='kernel rejected proved source or query',log=log[-12000:])
        printed=re.findall(r'(?:depends on axioms: \[[^\]]*\]|does not depend on any axioms)',''.join(logs))
        if len(printed)!=expected['lean'].count('#print axioms ')+len(audits):
            return dict(accepted=False,reason='required proved-source or query audit missing')
        return dict(accepted=True,proof_status='kernel_checked',execution_verified=False,
                    scope=expected['scope'],version=version,specification_sha256=expected['specification_sha256'],
                    source_sha256=expected['source_sha256'],library_sha256={
                        name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in libraries.items()},
                    log=''.join(logs))
    except (OSError,subprocess.SubprocessError) as error:
        return dict(accepted=False,reason='kernel execution failed: '+str(error))
