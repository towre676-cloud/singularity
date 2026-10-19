"""Eliminate affine equalities using a complete integer fibre, not a Q basis.

Single existential SMT query. Residual nonlinear assertions remain exact.
Unsupported syntax is rejected before a reduced query is returned.
"""
from dataclasses import dataclass
import re
from .smt_cert import split_commands, _sexpr
from .finite_formula import _poly
from .smt_adapter import _padd
from .finite_projection import _literal, _simplify, _render
from .industrial_router import route_lia
from .integer_lifting import solve_integer


@dataclass
class IntegerProjection:
    smt: str
    symbols: tuple
    parameters: tuple
    bindings: dict
    solution: dict
    linear: bool

    def lift(self, values):
        """Lift exact integer parameter values to the original variable model."""
        if self.solution['status']!='INTEGER_AFFINE_FIBRE': raise ValueError('empty integer fibre')
        if set(values)!=set(self.parameters) or any(type(x) is not int for x in values.values()):
            raise ValueError('exact values for every integer parameter required')
        point=self.solution['particular'];basis=self.solution['kernel_basis']
        return {name:point[i]+sum(values[p]*basis[j][i] for j,p in enumerate(self.parameters))
                for i,name in enumerate(self.symbols)}


def _parse_integer_query(script):
    names,assertions=[],[];seen_logic=False;checks=0
    for raw in split_commands(script):
        node=_sexpr(raw)
        if checks: raise ValueError('commands after query')
        if node==['set-logic','QF_NIA'] and not seen_logic: seen_logic=True
        elif node[0]=='declare-const' and len(node)==3 and node[2]=='Int': names.append(node[1])
        elif node[0]=='declare-fun' and len(node)==4 and node[2:]==[[],'Int']: names.append(node[1])
        elif node[0]=='assert' and len(node)==2: assertions.append(node[1])
        elif node==['check-sat']: checks+=1
        else: raise ValueError('unsupported integer projection command')
    if not seen_logic or checks!=1 or not 1<=len(names)<=32 or len(set(names))!=len(names):
        raise ValueError('requires QF_NIA, 1..32 distinct Int constants, one query')
    if any(not isinstance(n,str) or not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*',n) or n in ('true','false') for n in names):
        raise ValueError('plain integer identifiers required')

    def sort(node):
        if isinstance(node,str):
            if node in ('true','false'): return 'Bool'
            if node in names or (node.isascii() and node.isdecimal()): return 'Int'
            raise ValueError('undeclared arithmetic symbol')
        if not node: raise ValueError('empty expression')
        op,args=node[0],node[1:];types=[sort(a) for a in args]
        if op in ('+','*') and len(args)>=2 and all(t=='Int' for t in types): return 'Int'
        if op=='-' and args and all(t=='Int' for t in types): return 'Int'
        if op in ('mod','div') and len(args)==2 and types==['Int','Int']: return 'Int'
        if op in ('=','distinct') and len(args)>=2 and len(set(types))==1: return 'Bool'
        if op in ('<','<=','>','>=') and len(args)>=2 and all(t=='Int' for t in types): return 'Bool'
        if op in ('and','or') and all(t=='Bool' for t in types): return 'Bool'
        if op=='not' and types==['Bool']: return 'Bool'
        if op=='=>' and len(args)>=2 and all(t=='Bool' for t in types): return 'Bool'
        if op=='ite' and len(args)==3 and types[0]=='Bool' and types[1]==types[2]: return types[1]
        raise ValueError('unsupported or ill-sorted residual expression')

    def flatten(node):
        if isinstance(node,list) and node and node[0]=='and':
            return [a for child in node[1:] for a in flatten(child)]
        return [node]

    atoms=[]
    for node in assertions:
        if sort(node)!='Bool': raise ValueError('Boolean assertion required')
        atoms.extend(flatten(node))
    if len(atoms)>1000: raise ValueError('assertion budget exceeded')
    return names,atoms


def project_integer_query(script, **budgets):
    names,atoms=_parse_integer_query(script)
    rows,rhs,residual=[],[],[]
    for atom in atoms:
        linear=None
        if isinstance(atom,list) and len(atom)==3 and atom[0]=='=':
            try:
                polynomial=_padd(_poly(atom[1],names),_poly(atom[2],names),-1)
                if all(sum(e for _,e in monomial)<=1 for monomial in polynomial): linear=polynomial
            except ValueError: pass
        if linear is None: residual.append(atom)
        else:
            rows.append([linear.get(((name,1),),0) for name in names]);rhs.append(-linear.get((),0))
    if not rows: raise ValueError('no direct affine integer equalities')
    solved=solve_integer(rows,rhs,**budgets)
    params=[];bindings={}
    if solved['status']=='INTEGER_AFFINE_FIBRE':
        for j in range(solved['parameter_count']):
            name=f'_pp_integer_{j}'
            while name in names or name in params: name+='_'
            params.append(name)
        for i,name in enumerate(names):
            terms=[_literal(solved['particular'][i])]
            terms.extend(['*',_literal(w[i]),p] for w,p in zip(solved['kernel_basis'],params) if w[i])
            bindings[name]=_simplify(['+']+terms)
        def substitute(node):
            if isinstance(node,str): return bindings.get(node,node)
            return [node[0]]+[substitute(x) for x in node[1:]]
        assertion=_simplify(['and']+[substitute(node) for node in residual])
    else: assertion='false'
    out='\n'.join(['(set-logic QF_NIA)']+[f'(declare-const {p} Int)' for p in params]
                  +[f'(assert {_render(assertion)})','(check-sat)'])+'\n'
    routed,linear=route_lia(out)
    return IntegerProjection(routed,tuple(names),tuple(params),bindings,solved,linear)
