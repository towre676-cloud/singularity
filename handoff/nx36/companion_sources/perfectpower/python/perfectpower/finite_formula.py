"""Whole-query Lean proof emission for finite arithmetic relations.

Registry entries are compiled source theorems, not point scans. Emission is
not proof acceptance: compile the returned Lean file before using its result.
"""
from __future__ import annotations
from .resources import runtime_root
from dataclasses import dataclass
import hashlib
import ast
from pathlib import Path
import re
from math import isqrt
from .smt_cert import split_commands, _sexpr
from .smt_adapter import _padd, _pmul
from .compiler import match_affine_cube

@dataclass
class Emission:
    lean: str
    points: list[tuple[int, int]]
    family: str
    source_sha256: str
    imports: list[str]
    smt: str
    eliminated_symbols: tuple[str, str] = ()
    residual_assertions: tuple = ()
    remaining_symbols: tuple[str, ...] = ()



def _positive_source(k):
    """Read only an explicit all-integer complete-list statement; Lean checks its use."""
    path=runtime_root()/'PerfectPower'/'Generated'/'ClassLists'/f'K{k}.lean'
    if not path.is_file(): return None
    pattern=rf'^theorem plus{k} \(x y : ℤ\) : y \^ 2 = x \^ 3 \+ {k} ↔ \(x, y\) ∈ \((\[[0-9(), \-]*\]) : List \(ℤ × ℤ\)\) :=$'
    match=re.search(pattern,path.read_text(),re.M)
    if not match: return None
    points=ast.literal_eval(match.group(1))
    if any(not isinstance(p,tuple) or len(p)!=2 or any(type(v)!=int for v in p) for p in points):
        return None
    return f'PerfectPower.Generated.ClassLists.K{k}',points,f'Generated.ClassLists.K{k}.plus{k} x y'


def _poly(e, declared):
    if isinstance(e, str):
        if e in declared: return {((e, 1),): 1}
        if e.isascii() and e.isdecimal(): return {(): int(e)} if int(e) else {}
        raise ValueError('unsupported arithmetic atom')
    if not e or e[0] not in ('+', '-', '*'): raise ValueError('unsupported arithmetic operator')
    op, args = e[0], e[1:]
    if op == '-' and len(args) == 1:
        return {m: -c for m,c in _poly(args[0], declared).items()}
    if len(args) < 2: raise ValueError('arithmetic arity')
    out = _poly(args[0], declared)
    for arg in args[1:]:
        p = _poly(arg, declared)
        out = _pmul(out,p) if op == '*' else _padd(out,p,-1 if op == '-' else 1)
        if len(out) > 1000 or any(sum(v for _,v in m)>8 for m in out):
            raise ValueError('normalization budget exceeded')
    return out


def _match(P):
    vs = sorted({v for m in P for v,_ in m})
    if len(vs)!=2 or any(len(m)>1 for m in P): return None
    for y in vs:
        x = vs[0] if vs[1]==y else vs[1]
        c2=P.get(((y,2),),0)
        if not c2 or any(v==y and e>2 for m in P for v,e in m): continue
        sign=1 if c2>0 else -1
        Q={m:sign*c for m,c in P.items()}
        a=isqrt(abs(c2))
        if a*a!=abs(c2) or Q.get(((y,1),),0)%(2*a): continue
        b=Q.get(((y,1),),0)//(2*a)
        deg=max((e for m in Q for v,e in m if v==x),default=0)
        F=[b*b-Q.get((),0)]+[-Q.get(((x,i),),0) for i in range(1,deg+1)]
        if F==[1,0,3,0,3] and (a,b)==(1,0):
            return x,y,sign,'quartic',1,0,0,1,0
        if deg==3:
            affine=match_affine_cube(F)
            if affine and (affine[2]==-1 or _positive_source(affine[2]) is not None):
                r,s,k=affine
                return x,y,sign,'mordell',r,s,k,a,b
    return None


def emit_finite_query(script: str) -> Emission:
    names,assertions,checks=[],[],0
    for c in split_commands(script):
        n=_sexpr(c)
        if checks: raise ValueError('commands after query')
        if n[0]=='set-info': continue
        if n==['set-logic','QF_NIA']: continue
        if n[0]=='declare-const' and len(n)==3 and n[2]=='Int': names.append(n[1])
        elif n[0]=='declare-fun' and len(n)==4 and n[2:]==[[],'Int']: names.append(n[1])
        elif n[0]=='assert' and len(n)==2: assertions.append(n[1])
        elif n==['check-sat']: checks+=1
        else: raise ValueError('unsupported command')
    if checks!=1 or not 2<=len(names)<=32 or len(set(names))!=len(names):
        raise ValueError('requires 2..32 distinct Int constants and one query')
    if any(not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',n) for n in names):
        raise ValueError('plain identifiers required')
    selected=None
    for atom in assertions:
        if isinstance(atom,list) and len(atom)==3 and atom[0]=='=':
            try: P=_padd(_poly(atom[1],names),_poly(atom[2],names),-1)
            except ValueError: continue
            match=_match(P)
            if match:
                selected=atom,match
                break
    if selected is None: raise ValueError('no supported direct finite relation')
    atom,(x,y,sign,kind,r,s,k,a,b)=selected
    extras=[n for n in names if n not in (x,y)]
    symbols={x:'x',y:'y',**{n:f'z{i}' for i,n in enumerate(extras)}}
    def term(e):
        if isinstance(e,str):
            if e in symbols: return symbols[e]
            if e.isascii() and e.isdecimal(): return f'({e} : ℤ)'
            raise ValueError('unsupported term')
        if not e or e[0] not in ('+','-','*'): raise ValueError('unsupported operator')
        op,args=e[0],e[1:]
        if op=='-' and len(args)==1: return f'(-{term(args[0])})'
        if len(args)<2: raise ValueError('arithmetic arity')
        return '('+f' {op} '.join(term(v) for v in args)+')'
    def prop(e):
        if e=='true': return 'True'
        if e=='false': return 'False'
        if not isinstance(e,list) or not e: raise ValueError('Boolean atom')
        op,args=e[0],e[1:]
        if op in ('=','<','<=','>','>=') and len(args)==2:
            return f'({term(args[0])} '+{'=':'=','<':'<','<=':'≤','>':'>','>=':'≥'}[op]+f' {term(args[1])})'
        if op in ('and','or') and len(args)>=2:
            return '('+(' ∧ ' if op=='and' else ' ∨ ').join(prop(v) for v in args)+')'
        if op=='not' and len(args)==1: return f'(¬ {prop(args[0])})'
        raise ValueError('unsupported Boolean operator')
    residual=assertions.copy();residual.remove(atom)
    body=' ∧ '.join(prop(v) for v in residual) or 'True'
    binders=' '.join(f'(z{i} : ℤ)' for i in range(len(extras)))
    zs=' '.join(f'z{i}' for i in range(len(extras)))
    cfun=f'(residual {zs})' if extras else 'residual'
    if kind=='quartic':
        module='PerfectPower.QuarticPilot'
        points=[(0,-1),(0,1)]
        relation='y ^ 2 = 3*x^4+3*x^2+1'
        complete='by simpa [pointList, and_or_left, or_comm] using QuarticPilot.complete x y'
        R='(fun x y : ℤ => y ^ 2 = 3*x^4+3*x^2+1)'
        theorem=f'FormulaTransport.finite_exists {R} pointList pointList_complete {cfun}'
    else:
        if k>0:
            module,points,complete=_positive_source(k)
        else:
            module='PerfectPower.MordellMinus1';points=[(1,0)]
            complete='by simpa [pointList, sub_eq_add_neg] using MordellMinus1.complete x y'
        relation=f'(({a}:ℤ)*y+({b}))^2 = (({r}:ℤ)*x+({s}))^3+({k})'
        R=f'(fun x y : ℤ => y^2 = x^3+({k}))'
        theorem=f'FormulaTransport.affine_pair_finite_exists {R} pointList pointList_complete ({r}) ({s}) ({a}) ({b}) (by norm_num) (by norm_num) {cfun}'
    listtext='['+', '.join(f'(({u}), ({v}))' for u,v in points)+']'
    lifts=points if kind=='quartic' else sorted({((u-s)//r,(v-b)//a) for u,v in points if (u-s)%r==0 and (v-b)%a==0})
    answer=' ∨ '.join(f'{cfun} ({u}) ({v})' for u,v in lifts) or 'False'
    # Lean independently checks the exact polynomial identity and every finite image test.
    sha=hashlib.sha256(script.encode()).hexdigest()
    whole = ''
    if extras:
        quantified = ' '.join(f'z{i}' for i in range(len(extras)))
        whole = f'''theorem whole_query_iff :
    (∃ {quantified} : ℤ, ∃ x y : ℤ, {prop(atom)} ∧ {cfun} x y) ↔
      (∃ {quantified} : ℤ, {answer}) := by
  simp_rw [original_iff_finite]
#print axioms whole_query_iff
'''
    lean=f'''import PerfectPower.FormulaAffine
import {module}
-- Source SHA256: {sha}
-- Integer symbols mapped to Lean names: {symbols!r}
namespace PerfectPower.GeneratedFiniteFormula.S{sha[:12]}
private def residual {binders} (x y : ℤ) : Prop := {body}
private def pointList : List (ℤ × ℤ) := {listtext}
private theorem pointList_complete (x y : ℤ) :
    {R} x y ↔ (x,y) ∈ pointList := {complete}
private theorem relation {binders} (x y : ℤ) : {prop(atom)} ↔ {relation} := by
  have identity : {term(atom[1])} - {term(atom[2])} =
      ({sign}:ℤ) * (({relation.split(' = ')[0]}) - ({relation.split(' = ')[1]})) := by ring
  constructor <;> intro h <;> nlinarith [identity]
theorem original_iff_finite {binders} :
    (∃ x y : ℤ, {prop(atom)} ∧ {cfun} x y) ↔
      ({answer}) := by
  simp_rw [relation {zs}]
  simpa [pointList] using {theorem}
#print axioms original_iff_finite
{whole}end PerfectPower.GeneratedFiniteFormula.S{sha[:12]}
'''
    def numeral(v):
        return str(v) if v>=0 else f'(- {-v})'
    choices=[f'(and (= {x} {numeral(u)}) (= {y} {numeral(v)}))' for u,v in lifts]
    replacement='false' if not choices else choices[0] if len(choices)==1 else '(or '+' '.join(choices)+')'
    replaced=False
    commands=[]
    for command in split_commands(script):
        if not replaced and _sexpr(command)==['assert',atom]:
            commands.append(f'(assert {replacement})');replaced=True
        else: commands.append(command)
    smt='\n'.join(commands)+'\n'
    return Emission(lean,lifts,kind,sha,['PerfectPower.FormulaAffine',module],smt,
                    (x,y),tuple(residual),tuple(extras))


def main():
    import argparse
    from pathlib import Path
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--smt-output',type=Path)
    args=parser.parse_args()
    result=emit_finite_query(args.source.read_bytes().decode('utf-8'))
    args.output.write_text(result.lean)
    if args.smt_output: args.smt_output.write_text(result.smt)
    print(f'Emitted {result.family} equivalence; {len(result.points)} lifted points. Compile with lake env lean {args.output}')

if __name__=='__main__':main()
