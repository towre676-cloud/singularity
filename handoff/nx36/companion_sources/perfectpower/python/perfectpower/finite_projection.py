"""Eliminate a complete finite arithmetic relation from an existential SMT query.

Retain every residual assertion and remaining integer variable. Completeness
comes only from the finite_formula supported theorem registry, never a scan.
"""
from dataclasses import dataclass
from .finite_formula import emit_finite_query
from .industrial_router import route_lia


def _number(node):
    if isinstance(node,str) and node.isascii() and node.isdecimal():return int(node)
    if isinstance(node,list) and len(node)==2 and node[0]=='-':
        value=_number(node[1]);return -value if value is not None else None
    return None


def _literal(n):return str(n) if n>=0 else ['-',str(-n)]


def _substitute(node,bindings):
    if isinstance(node,str):return _literal(bindings[node]) if node in bindings else node
    return [node[0]]+[_substitute(x,bindings) for x in node[1:]]


def _simplify(node):
    if isinstance(node,str):return node
    op,args=node[0],[_simplify(x) for x in node[1:]];nums=[_number(x) for x in args]
    if op in ('+','-','*') and all(x is not None for x in nums):
        if op=='+':value=sum(nums)
        elif op=='*':
            value=1
            for x in nums:value*=x
        else:value=-nums[0] if len(nums)==1 else nums[0]-sum(nums[1:])
        return _literal(value)
    if op=='*':
        if 0 in nums:return '0'
        kept=[a for a,n in zip(args,nums) if n!=1]
        return '1' if not kept else kept[0] if len(kept)==1 else ['*']+kept
    if op=='+':
        kept=[a for a,n in zip(args,nums) if n!=0]
        return '0' if not kept else kept[0] if len(kept)==1 else ['+']+kept
    if op in ('=','<','<=','>','>=') and len(args)==2 and all(x is not None for x in nums):
        a,b=nums;value={'=':a==b,'<':a<b,'<=':a<=b,'>':a>b,'>=':a>=b}[op]
        return 'true' if value else 'false'
    if op in ('and','or'):
        zero,one=('false','true') if op=='and' else ('true','false')
        if zero in args:return zero
        kept=[x for x in args if x!=one]
        return one if not kept else kept[0] if len(kept)==1 else [op]+kept
    if op=='not' and len(args)==1 and args[0] in ('true','false'):
        return 'false' if args[0]=='true' else 'true'
    return [op]+args


def _render(node):
    return node if isinstance(node,str) else '('+' '.join(_render(x) for x in node)+')'


@dataclass
class Projection:
    smt:str
    emission:object
    branches:tuple
    linear:bool


class ProjectionLimit(ValueError):
    """No query reduction is returned after a branch budget failure."""


def project_finite_query(script,*,branch_limit=10000):
    if type(branch_limit) is not int or branch_limit<1:raise ValueError('positive branch budget required')
    emission=emit_finite_query(script)
    if len(emission.points)>branch_limit:raise ProjectionLimit('finite projection branch budget exceeded')
    x,y=emission.eliminated_symbols;branches=[]
    for a,b in emission.points:
        residual=['and']+[_substitute(node,{x:a,y:b}) for node in emission.residual_assertions]
        branches.append(_simplify(residual))
    assertion=_simplify(['or']+branches)
    declarations=[f'(declare-const {name} Int)' for name in emission.remaining_symbols]
    out='\n'.join(['(set-logic QF_NIA)']+declarations+[f'(assert {_render(assertion)})','(check-sat)'])+'\n'
    routed,linear=route_lia(out)
    return Projection(routed,emission,tuple(branches),linear)
