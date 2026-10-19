"""Globally complete queries for proved families and exact affine input pullbacks."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .checked_box import _hash, _integer
from .checked_population import _compile_queries, _emit_queries, _tree
from .divisor_square import WorkLimit
from .resources import runtime_root

MODULES=('BoundedNative','QueryNative','AffinePopulation','MordellMinus2Core','GlobalMordellPopulation')


def global_population_certificate(queries, *, family='mordell_minus2', scale=1, shift=0,
                                  domain='integer'):
    """All integer solutions of y²=(scale*x+shift)³-2, with no search interval.

    Supported domains: integer, nonnegative, positive. Query x is the ORIGINAL
    input after affine recovery. Zero scale is excluded because its fibre can
    be infinite. The certificate checks the source theorem and exact pullback.
    """
    if family!='mordell_minus2': raise ValueError('unsupported globally proved family')
    a=_integer(scale,'scale'); b=_integer(shift,'shift')
    if a==0: raise ValueError('affine scale must be nonzero')
    if domain not in ('integer','nonnegative','positive'):
        raise ValueError('domain must be integer, nonnegative or positive')
    condition=True if domain=='integer' else ['le',0 if domain=='nonnegative' else 1,'x']
    dc,de=_tree(condition,condition=True)
    n=(3-b)//a
    points=[[n,-5],[n,5]] if (3-b)%a==0 and de([n,0]) else []
    normalized,plans=_compile_queries(points,queries)
    spec=dict(family=family,scale=a,shift=b,domain=domain,queries=normalized)
    name='PerfectPower.CheckedGlobalPopulation_'+_hash(spec)[:16]
    coefficients=[b**3-2,3*a*b*b,3*a*a*b,a**3]
    source=f'''import PerfectPower.GlobalMordellPopulation
namespace {name}
open PerfectPower.QueryNative PerfectPower.AffinePopulation
def domainCondition := {dc}
def sourcePoints := restrict (pullback PerfectPower.GlobalMordellPopulation.points ({a}) ({b})) domainCondition
def original (p : Int × Int) : Prop := p.2^2 = (({a})*p.1+({b}))^3-2 ∧ domainCondition.holds p
theorem source_complete (p : Int × Int) : p ∈ sourcePoints ↔ original p :=
  restrict_complete _ _ (PerfectPower.GlobalMordellPopulation.affine_complete ({a}) ({b}) (by decide +kernel)) domainCondition p
theorem expanded_original (p : Int × Int) : original p ↔
    p.2^2 = PerfectPower.BoundedNative.horner {coefficients} p.1 ∧ domainCondition.holds p := by
  have he : (({a})*p.1+({b}))^3-2 = PerfectPower.BoundedNative.horner {coefficients} p.1 := by
    simp only [PerfectPower.BoundedNative.horner]
    ring
  simp only [original, he]
'''
    source,results=_emit_queries(source,name,points,normalized,plans)
    source+=f'#print axioms {name}.expanded_original\n'
    return dict(schema='pp-checked-global-population/1',specification=spec,source_count=len(points),
                source_points=points,original_coefficients=coefficients,results=results,lean=source,
                namespace=name,specification_sha256=_hash(spec),
                source_sha256=hashlib.sha256(source.encode()).hexdigest(),proof_status='emitted',
                execution_verified=False,scope='complete globally for all integer coordinates in the declared domain')


def check_global_population(packet, *, lean=None, lean_path=None, timeout=120):
    """Rebuild the source completeness proof and query libraries privately.

    Pinned Mathlib must be available on LEAN_PATH. A matching .olean for our
    source modules is not trusted: their packaged source is recompiled.
    """
    if type(timeout) not in (int,float) or not 0 < timeout <= 600:
        raise ValueError('timeout must be positive and at most 600 seconds')
    try: expected=global_population_certificate(**packet['specification'])
    except (KeyError,TypeError,ValueError,WorkLimit) as error:
        return dict(accepted=False,reason='invalid specification: '+str(error))
    if packet!=expected:
        return dict(accepted=False,reason='packet differs from reconstructed global query')
    binary=lean or os.environ.get('PERFECTPOWER_LEAN') or shutil.which('lean')
    external=lean_path if lean_path is not None else os.environ.get('LEAN_PATH','')
    if not binary or not external:
        return dict(accepted=False,reason='Lean 4.20.0 and pinned Mathlib on LEAN_PATH required')
    libraries={name:runtime_root()/f'PerfectPower/{name}.lean' for name in MODULES}
    if any(not p.is_file() for p in libraries.values()):
        return dict(accepted=False,reason='global source libraries unavailable')
    try:
        version=subprocess.run([binary,'--version'],capture_output=True,text=True,timeout=timeout,check=True).stdout.strip()
        if not version.startswith('Lean (version 4.20.0,'):
            return dict(accepted=False,reason='Lean 4.20.0 required',version=version)
        logs=[]
        with tempfile.TemporaryDirectory(prefix='pp-global-population-') as directory:
            root=Path(directory);(root/'PerfectPower').mkdir()
            commands=[]
            for name,path in libraries.items():
                local=root/f'PerfectPower/{name}.lean';local.write_bytes(path.read_bytes())
                commands.append([binary,str(local),'-o',str(local.with_suffix('.olean'))])
            query=root/'Query.lean';query.write_text(expected['lean'],encoding='utf-8')
            audit=root/'SourceAudit.lean';audit.write_text('import PerfectPower.GlobalMordellPopulation\n'
                '#print axioms PerfectPower.MordellMinus2.points\n'
                '#print axioms PerfectPower.GlobalMordellPopulation.affine_complete\n',encoding='utf-8')
            commands += [[binary,str(audit)],[binary,str(query)]]
            environment=dict(os.environ,LEAN_PATH=str(root)+os.pathsep+external)
            for command in commands:
                run=subprocess.run(command,cwd=root,env=environment,capture_output=True,text=True,timeout=timeout)
                log=run.stdout+run.stderr;logs.append(log)
                axioms=[v.strip() for row in re.findall(r'depends on axioms: \[([^\]]*)\]',log)
                        for v in row.split(',') if v.strip()]
                if run.returncode or 'sorry' in log or 'ofReduceBool' in log or any(
                        v not in {'propext','Classical.choice','Quot.sound'} for v in axioms):
                    return dict(accepted=False,reason='kernel rejected global source or query',log=log[-12000:])
        printed=re.findall(r'(?:depends on axioms: \[[^\]]*\]|does not depend on any axioms)',''.join(logs))
        if len(printed)!=expected['lean'].count('#print axioms ')+2:
            return dict(accepted=False,reason='required global source or query audit missing')
        return dict(accepted=True,proof_status='kernel_checked',execution_verified=False,
                    scope=expected['scope'],version=version,specification_sha256=expected['specification_sha256'],
                    source_sha256=expected['source_sha256'],library_sha256={
                        name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in libraries.items()},
                    log=''.join(logs))
    except (OSError,subprocess.SubprocessError) as error:
        return dict(accepted=False,reason='kernel execution failed: '+str(error))


def add_commands(sub):
    p=sub.add_parser('checked-global-population',help='globally complete proved-family queries')
    p.add_argument('--queries',required=True,type=json.loads)
    p.add_argument('--scale',type=int,default=1)
    p.add_argument('--shift',type=int,default=0)
    p.add_argument('--domain',choices=('integer','nonnegative','positive'),default='integer')
    p.add_argument('--check',action='store_true')


def cli(args):
    if args.command!='checked-global-population':return False
    packet=global_population_certificate(args.queries,scale=args.scale,shift=args.shift,domain=args.domain)
    output=dict(packet=packet)
    if args.check:output['acceptance']=check_global_population(packet)
    print(json.dumps(output,sort_keys=True))
    if args.check and not output['acceptance']['accepted']:raise SystemExit(1)
    return True
