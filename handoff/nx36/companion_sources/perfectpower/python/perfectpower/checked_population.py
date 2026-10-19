"""Compile once, query many: exact restrictions and objectives in source coordinates.

Packets remain proposals until the reconstructed Lean source is accepted. The
source interval is explicit; this API does not establish a global height bound.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from .checked_box import box_certificate, _hash, _integer
from .divisor_square import WorkLimit
from .resources import runtime_root


def _tree(value, *, condition=False, depth=0, counter=None):
    """Validate a small closed AST, returning Lean syntax and a Python evaluator."""
    counter = [0] if counter is None else counter
    counter[0] += 1
    if depth > 32 or counter[0] > 128:
        raise WorkLimit('query AST exceeds depth 32 or 128 nodes')
    prefix = 'Condition' if condition else 'Expr'
    def child(v, cond=False):
        return _tree(v, condition=cond, depth=depth+1, counter=counter)
    if condition and type(value) is bool:
        return ('Condition.truth' if value else 'Condition.falsity'), lambda p: value
    if not condition:
        if type(value) is int:
            n = _integer(value, 'expression constant')
            return f'(Expr.constant ({n}))', lambda p: n
        if type(value) is str and value in ('x', 'y'):
            i = 0 if value == 'x' else 1
            return 'Expr.'+value, lambda p: p[i]
    if not isinstance(value, list) or not value or type(value[0]) is not str:
        raise ValueError('invalid '+prefix+' AST')
    op = value[0]
    if not condition and op in ('add', 'mul') and len(value) == 3:
        a, ea = child(value[1]); b, eb = child(value[2])
        def evaluate(p):
            x, y = ea(p), eb(p)
            v = x+y if op == 'add' else x*y
            if abs(v).bit_length() > 4096:
                raise WorkLimit('query expression exceeds 4096 bits')
            return v
        return f'(Expr.{op} {a} {b})', evaluate
    if not condition and op == 'pow' and len(value) == 3:
        a, ea = child(value[1]); n = value[2]
        if type(n) is not int or not 0 <= n <= 16:
            raise ValueError('query power must be between 0 and 16')
        def evaluate(p):
            v = ea(p)**n
            if abs(v).bit_length() > 4096:
                raise WorkLimit('query expression exceeds 4096 bits')
            return v
        return f'(Expr.power {a} {n})', evaluate
    if condition and op in ('eq', 'le') and len(value) == 3:
        a, ea = child(value[1]); b, eb = child(value[2])
        return f'(Condition.{"equal" if op == "eq" else "le"} {a} {b})', (
            lambda p: ea(p) == eb(p)) if op == 'eq' else lambda p: ea(p) <= eb(p)
    if condition and op == 'mod' and len(value) == 4:
        a, ea = child(value[1]); r = _integer(value[2], 'residue')
        m = _integer(value[3], 'modulus')
        if m <= 0:
            raise ValueError('query modulus must be positive')
        return f'(Condition.congruent {a} ({r}) ({m}))', lambda p: ea(p) % m == r % m
    if condition and op in ('and', 'or') and len(value) == 3:
        a, ea = child(value[1], True); b, eb = child(value[2], True)
        return f'(Condition.{"both" if op == "and" else "either"} {a} {b})', (
            lambda p: ea(p) and eb(p)) if op == 'and' else lambda p: ea(p) or eb(p)
    if condition and op == 'not' and len(value) == 2:
        a, ea = child(value[1], True)
        return f'(Condition.negate {a})', lambda p: not ea(p)
    raise ValueError('unsupported '+prefix+' operation or arity')


def _compile_queries(source_points, queries):
    if not isinstance(queries, list) or not 1 <= len(queries) <= 64:
        raise ValueError('one through 64 queries required')
    normalized=[]; plans=[]; cost=0
    for query in queries:
        if not isinstance(query, dict) or set(query)-{'condition','ranks','objective'}:
            raise ValueError('query keys must be condition, ranks, objective')
        condition=query.get('condition',True); objective=query.get('objective')
        counter=[0]; c, ec=_tree(condition,condition=True,counter=counter)
        o, eo=(None,None) if objective is None else _tree(objective,counter=counter)
        ranks=query.get('ranks',[])
        if not isinstance(ranks,list) or len(ranks)>64 or any(
                type(i) is not int or i < 0 or i.bit_length() > 128 for i in ranks):
            raise ValueError('at most 64 nonnegative selection ranks of at most 128 bits required')
        cost += max(1,len(source_points))*counter[0]
        if cost > 262144:
            raise WorkLimit('batch exceeds 262144 point/AST-node operations')
        normalized.append(dict(condition=condition,ranks=ranks,objective=objective))
        plans.append((c,ec,o,eo))
    return normalized, plans


def _emit_queries(source, namespace, source_points, normalized, plans):
    results=[]; audits=['source_complete']
    for j,(query,plan) in enumerate(zip(normalized,plans)):
        c,ec,o,eo=plan; points=[p for p in source_points if ec(p)]
        selections=[dict(rank=i,point=points[i] if i<len(points) else None) for i in query['ranks']]
        source+=f'def condition_{j} := {c}\ndef answer_{j} := restrict sourcePoints condition_{j}\n'
        source+=f'theorem complete_{j} (p : Int × Int) : p ∈ answer_{j} ↔ original p ∧ condition_{j}.holds p :=\n  restrict_complete sourcePoints original source_complete condition_{j} p\n'
        source+=f'theorem count_{j} : answer_{j}.length = {len(points)} := by decide +kernel\n'
        source+=f'theorem nodup_{j} : answer_{j}.Nodup := by decide +kernel\n'
        source+=f'theorem rank_domain_{j} (p : Int × Int) : (∃ i, rank p answer_{j} = some i) ↔ original p ∧ condition_{j}.holds p :=\n  query_rank_exists sourcePoints original source_complete condition_{j} p\n'
        source+=f'theorem rank_roundtrip_{j} (p : Int × Int) (i : Nat) (h : answer_{j}[i]? = some p) : rank p answer_{j} = some i :=\n  select_rank p answer_{j} nodup_{j} i h\n'
        for k,item in enumerate(selections):
            point=item['point']; expected='none' if point is None else f'some (({point[0]}),({point[1]}))'
            source+=f'theorem selection_{j}_{k} : answer_{j}[{item["rank"]}]? = {expected} := by decide +kernel\n'
        minimum=None
        if query['objective'] is not None and points:
            value=min(eo(p) for p in points); ties=[p for p in points if eo(p)==value]
            minimum=dict(value=value,points=ties)
            source+=f'def objective_{j} := {o}\n'
            source+=f'theorem lower_checked_{j} : (answer_{j}.all fun p => decide (({value}) ≤ objective_{j}.eval p)) = true := by decide +kernel\n'
            source+=f'theorem minimum_{j} (p : Int × Int) (h : original p ∧ condition_{j}.holds p) : ({value}) ≤ objective_{j}.eval p :=\n  objective_lower_bound answer_{j} _ complete_{j} objective_{j} ({value}) lower_checked_{j} p h\n'
            literal='['+','.join(f'(({x}),({y}))' for x,y in ties)+']'
            source+=f'theorem ties_checked_{j} : answer_{j}.filter (fun p => decide (objective_{j}.eval p = ({value}))) = {literal} := by decide +kernel\n'
            source+=f'theorem ties_{j} (p : Int × Int) : p ∈ ({literal} : List (Int × Int)) ↔ (original p ∧ condition_{j}.holds p) ∧ objective_{j}.eval p = ({value}) := by\n  rw [← ties_checked_{j}]\n  exact objective_ties_complete answer_{j} _ complete_{j} objective_{j} ({value}) p\n'
            audits += [f'minimum_{j}',f'ties_{j}']
        results.append(dict(points=points,count=len(points),selections=selections,minimum=minimum))
        audits += [f'complete_{j}',f'count_{j}',f'nodup_{j}',f'rank_domain_{j}',f'rank_roundtrip_{j}']
        audits += [f'selection_{j}_{k}' for k in range(len(selections))]
    source+=f'end {namespace}\n'
    source+=''.join(f'#print axioms {namespace}.{name}\n' for name in audits)
    return source, results


def population_certificate(coefficients, exponent, x_bounds, queries, y_bounds=None, *,
                           work_limit=4096):
    """One source population, up to 64 restrictions with rank and bivariate minima.

    Expr := integer | "x" | "y" | ["add"|"mul", Expr, Expr] | ["pow", Expr, 0..16].
    Condition := bool | ["eq"|"le", Expr, Expr] | ["mod", Expr, residue, modulus]
                 | ["and"|"or", Condition, Condition] | ["not", Condition].
    Queries contain condition, ranks, and optional objective; defaults are true/[]/None.
    """
    base = box_certificate(coefficients, exponent, x_bounds, y_bounds, work_limit=work_limit)
    normalized, plans = _compile_queries(base['points'], queries)
    spec=dict(coefficients=base['specification']['coefficients'],exponent=exponent,
              x_bounds=base['specification']['x_bounds'],y_bounds=base['specification']['y_bounds'],
              queries=normalized,work_limit=work_limit)
    namespace='PerfectPower.CheckedPopulation_'+_hash(spec)[:16]
    source=base['lean'].replace('import PerfectPower.BoundedNative','import PerfectPower.QueryNative',1)
    source+=f'\nnamespace {namespace}\nopen PerfectPower.QueryNative\n'
    source+=f'def sourcePoints := {base["namespace"]}.answer\n'
    theorem='complete_all_integer_y' if y_bounds is None else 'original_complete'
    xl,xu=base['specification']['x_bounds']; yl,yu=base['resolved_y_bounds']
    bounds=f'({xl}) ≤ p.1 ∧ p.1 ≤ ({xu}) ∧ '
    if y_bounds is not None: bounds+=f'({yl}) ≤ p.2 ∧ p.2 ≤ ({yu}) ∧ '
    source+=f'def original (p : Int × Int) : Prop := {bounds}p.2 ^ {exponent} = PerfectPower.BoundedNative.horner {spec["coefficients"]} p.1\n'
    source+=f'theorem source_complete (p : Int × Int) : p ∈ sourcePoints ↔ original p :=\n  {base["namespace"]}.{theorem} p.1 p.2\n'
    source, results = _emit_queries(source, namespace, base['points'], normalized, plans)
    return dict(schema='pp-checked-population/1',specification=spec,source_count=base['count'],
                results=results,lean=source,namespace=namespace,specification_sha256=_hash(spec),
                source_sha256=hashlib.sha256(source.encode()).hexdigest(),proof_status='emitted',
                execution_verified=False,scope=base['scope'])


def check_population(packet, *, lean=None, timeout=60):
    """Reconstruct all queries, then compile both generic libraries and the batch."""
    if type(timeout) not in (int,float) or not 0 < timeout <= 600:
        raise ValueError('timeout must be positive and at most 600 seconds')
    try:
        expected=population_certificate(**packet['specification'])
    except (KeyError,TypeError,ValueError,WorkLimit) as error:
        return dict(accepted=False,reason='invalid specification: '+str(error))
    if packet != expected:
        return dict(accepted=False,reason='packet differs from reconstructed original queries')
    binary=lean or os.environ.get('PERFECTPOWER_LEAN') or shutil.which('lean')
    if not binary:
        return dict(accepted=False,reason='Lean 4.20.0 unavailable; proposal remains unaccepted')
    libraries={name:runtime_root()/f'PerfectPower/{name}.lean' for name in ('BoundedNative','QueryNative')}
    if any(not path.is_file() for path in libraries.values()):
        return dict(accepted=False,reason='population kernel libraries unavailable')
    try:
        version=subprocess.run([binary,'--version'],capture_output=True,text=True,timeout=timeout,check=True).stdout.strip()
        if not version.startswith('Lean (version 4.20.0,'):
            return dict(accepted=False,reason='Lean 4.20.0 required',version=version)
        logs=[]
        with tempfile.TemporaryDirectory(prefix='pp-checked-population-') as directory:
            root=Path(directory); (root/'PerfectPower').mkdir()
            commands=[]
            for name,path in libraries.items():
                local=root/f'PerfectPower/{name}.lean'; local.write_bytes(path.read_bytes())
                commands.append([binary,str(local),'-o',str(local.with_suffix('.olean'))])
            query=root/'Query.lean'; query.write_text(expected['lean'],encoding='utf-8')
            commands.append([binary,str(query)])
            environment=dict(os.environ,LEAN_PATH=str(root))
            for command in commands:
                run=subprocess.run(command,cwd=root,env=environment,capture_output=True,text=True,timeout=timeout)
                log=run.stdout+run.stderr; logs.append(log)
                axioms=[a.strip() for group in re.findall(r'depends on axioms: \[([^\]]*)\]',log)
                        for a in group.split(',') if a.strip()]
                if run.returncode or 'sorry' in log or 'ofReduceBool' in log or any(
                        a not in {'propext','Classical.choice','Quot.sound'} for a in axioms):
                    return dict(accepted=False,reason='kernel rejected query batch',log=log[-12000:])
        return dict(accepted=True,proof_status='kernel_checked',execution_verified=False,
                    scope=expected['scope'],version=version,specification_sha256=expected['specification_sha256'],
                    source_sha256=expected['source_sha256'],library_sha256={
                        name:hashlib.sha256(path.read_bytes()).hexdigest() for name,path in libraries.items()},
                    log=''.join(logs))
    except (OSError,subprocess.SubprocessError) as error:
        return dict(accepted=False,reason='kernel execution failed: '+str(error))


def add_commands(sub):
    p=sub.add_parser('checked-population',help='one original population, many certified queries')
    p.add_argument('--coeff',required=True,type=json.loads)
    p.add_argument('--d',required=True,type=int)
    p.add_argument('--x',required=True,type=json.loads)
    p.add_argument('--y',type=json.loads)
    p.add_argument('--queries',required=True,type=json.loads)
    p.add_argument('--work-limit',type=int,default=4096)
    p.add_argument('--check',action='store_true')


def cli(args):
    if args.command != 'checked-population': return False
    packet=population_certificate(args.coeff,args.d,args.x,args.queries,args.y,work_limit=args.work_limit)
    result=dict(packet=packet)
    if args.check:
        result['acceptance']=check_population(packet)
    print(json.dumps(result,sort_keys=True))
    if args.check and not result['acceptance']['accepted']: raise SystemExit(1)
    return True
