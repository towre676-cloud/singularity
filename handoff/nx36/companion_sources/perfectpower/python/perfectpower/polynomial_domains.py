"""Complete integer sign domains and discrete polynomial optimization.

Sturm leaves locate every real sign-change region between adjacent integers.
Boolean combinations then have an exact finite union of integer intervals.
Optimization uses G(n+1)-G(n), retaining adjacent equal-value ties.
All coefficients and evaluations are exact; execution is not Lean verified.
"""
from copy import deepcopy
from fractions import Fraction
import json
from . import polyalg as P
from .residue_cover import integer_polynomial, evaluate
from .sturm_fibres import root_certificate, verify_roots
from .divisor_square import WorkLimit


RELATIONS = ('=', '!=', '<', '<=', '>', '>=')


def _normalize(predicate, *, atom_limit=128):
    atoms = []
    def walk(node, depth=0):
        if depth > 64: raise WorkLimit('Boolean depth budget exceeded')
        if type(node) is bool: return node
        if not isinstance(node, dict): raise ValueError('Boolean polynomial predicate required')
        if 'poly' in node:
            if set(node) != {'poly', 'relation'} or node['relation'] not in RELATIONS:
                raise ValueError('atom requires poly and a supported relation to zero')
            if len(atoms) >= atom_limit: raise WorkLimit('polynomial atom budget exceeded')
            atom = {'poly': list(integer_polynomial(node['poly'])), 'relation': node['relation']}
            atoms.append(atom)
            return {'atom': len(atoms)-1}
        op = node.get('op'); args = node.get('args')
        if set(node) != {'op', 'args'} or op not in ('and', 'or', 'not') or not isinstance(args, (list, tuple)):
            raise ValueError('Boolean node requires op and args')
        if op == 'not' and len(args) != 1: raise ValueError('not requires one argument')
        return {'op': op, 'args': [walk(a, depth+1) for a in args]}
    return walk(predicate), atoms


def _holds(value, relation):
    if relation == '=': return value == 0
    if relation == '!=': return value != 0
    if relation == '<': return value < 0
    if relation == '<=': return value <= 0
    if relation == '>': return value > 0
    return value >= 0


def _boolean(tree, truth):
    if type(tree) is bool: return tree
    if 'atom' in tree: return truth[tree['atom']]
    values = [_boolean(a, truth) for a in tree['args']]
    if tree['op'] == 'and': return all(values)
    if tree['op'] == 'or': return any(values)
    return not values[0]


def _critical(certificates):
    cuts = set()
    for certificate in certificates:
        for a, b, va, vb in certificate['nodes']:
            if b-a == 1 and va > vb:
                cuts.update((a, b))
    return sorted(cuts)


def _cells(cuts):
    if not cuts: return [(None, None)]
    result = [(None, cuts[0]-1)]
    for i, value in enumerate(cuts):
        result.append((value, value))
        if i+1 < len(cuts) and value+1 <= cuts[i+1]-1:
            result.append((value+1, cuts[i+1]-1))
    result.append((cuts[-1]+1, None))
    return result


def _merge(intervals):
    result = []
    for lo, hi in intervals:
        if result and result[-1][1] is not None and lo is not None and result[-1][1]+1 == lo:
            result[-1][1] = hi
        else: result.append([lo, hi])
    return result


def _domain(tree, atoms, certificates):
    records = []; accepted = []
    for lo, hi in _cells(_critical(certificates)):
        sample = lo if lo is not None else hi if hi is not None else 0
        values = [evaluate(a['poly'], sample) for a in atoms]
        truth = [_holds(v, a['relation']) for a, v in zip(atoms, values)]
        keep = _boolean(tree, truth)
        records.append({'interval': [lo, hi], 'sample': sample, 'values': values, 'accepted': keep})
        if keep: accepted.append((lo, hi))
    return records, _merge(accepted)


def integer_domain(predicate, *, node_limit=100000, atom_limit=128):
    """Every integer satisfying a Boolean polynomial predicate, as intervals.

    None is an infinite endpoint. No scanning of the intervals is performed.
    A shared root-node budget applies across distinct nonconstant polynomials.
    """
    if any(type(n) is not int or n < 1 for n in (node_limit, atom_limit)):
        raise ValueError('positive node and atom budgets required')
    tree, atoms = _normalize(predicate, atom_limit=atom_limit)
    certificates = []; seen = set(); used = 0
    for atom in atoms:
        f = tuple(atom['poly'])
        if len(f) < 2 or f in seen: continue
        seen.add(f)
        if used >= node_limit: raise WorkLimit('complete integer sign domain exceeds node budget')
        cert = root_certificate(f, node_limit=node_limit-used)
        used += cert['nodes_checked']; certificates.append(cert)
    cells, intervals = _domain(tree, atoms, certificates)
    cardinality = None if any(lo is None or hi is None for lo, hi in intervals) else sum(hi-lo+1 for lo, hi in intervals)
    return {'schema': 'pp-integer-polynomial-domain/1', 'predicate': deepcopy(predicate),
            'tree': tree, 'atoms': atoms, 'root_certificates': certificates,
            'cells': cells, 'intervals': intervals, 'cardinality': cardinality,
            'root_nodes': used, 'complete': True, 'domain': 'all integers',
            'execution_verified': False}


def verify_domain(result, *, node_limit=100000, atom_limit=128):
    """Replay the supplied Sturm trees and sign cells without root discovery."""
    try:
        tree, atoms = _normalize(result['predicate'], atom_limit=atom_limit)
        same = lambda a,b: json.dumps(a,sort_keys=True) == json.dumps(b,sort_keys=True)
        if result['schema'] != 'pp-integer-polynomial-domain/1' or result['domain'] != 'all integers': return False
        if result['complete'] is not True or result['execution_verified'] is not False: return False
        if not same(tree,result['tree']) or not same(atoms,result['atoms']): return False
        expected = list(dict.fromkeys(tuple(a['poly']) for a in atoms if len(a['poly']) > 1))
        certificates = result['root_certificates']
        if [tuple(c['coefficients']) for c in certificates] != expected: return False
        used = 0
        for cert in certificates:
            if used >= node_limit or cert['domain'] != [None,None]: return False
            if not verify_roots(cert,node_limit=node_limit-used): return False
            used += cert['nodes_checked']
        cells, intervals = _domain(tree,atoms,certificates)
        cardinality = None if any(lo is None or hi is None for lo,hi in intervals) else sum(hi-lo+1 for lo,hi in intervals)
        return same(cells,result['cells']) and same(intervals,result['intervals']) and cardinality == result['cardinality'] and used == result['root_nodes']
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError): return False


def contains(domain, value):
    if type(value) is not int: raise ValueError('integer coordinate required')
    return any((lo is None or lo <= value) and (hi is None or value <= hi) for lo,hi in domain['intervals'])


def _optimization_data(domain, objective, difference_certificate):
    intervals = domain['intervals']
    if not intervals: return {'status':'EMPTY','value':None,'optimizers':[],'candidates':[]}
    f = objective
    if len(f) == 1:
        return {'status':'OPTIMAL','value':f[0],'optimizers':deepcopy(intervals),'candidates':[], 'attainment':'entire feasible domain'}
    for lo,hi in intervals:
        if (lo is None and f[-1]*(-1)**(len(f)-1) < 0) or (hi is None and f[-1] < 0):
            return {'status':'UNBOUNDED','value':None,'optimizers':[], 'candidates':[],
                    'unbounded_tail': 'left' if lo is None and f[-1]*(-1)**(len(f)-1) < 0 else 'right'}
    critical = _critical([difference_certificate])
    turning = set(critical) | {n+1 for n in critical}
    candidates = set()
    for lo,hi in intervals:
        if lo is not None: candidates.add(lo)
        if hi is not None: candidates.add(hi)
        candidates.update(n for n in turning if (lo is None or lo <= n) and (hi is None or n <= hi))
    if not candidates: raise AssertionError('bounded nonconstant objective lacks candidate')
    values = [(n,evaluate(f,n)) for n in sorted(candidates)]
    value = min(v for n,v in values)
    minimizers = _merge([(n,n) for n,v in values if v == value])
    return {'status':'OPTIMAL','value':value,'optimizers':minimizers,'candidates':values,
            'attainment':'finite integer endpoints and discrete turning regions'}


def optimize_polynomial(predicate, objective, *, sense='min', node_limit=100000, atom_limit=128):
    """Global integer min/max over an arbitrary univariate Boolean domain.

    Discrete differences, rather than rounded real critical points, preserve
    every tied integer optimum. Empty and unbounded objectives are explicit.
    """
    if sense not in ('min','max'): raise ValueError('sense must be min or max')
    original = integer_polynomial(objective)
    f = original if sense == 'min' else tuple(-c for c in original)
    domain = integer_domain(predicate,node_limit=node_limit,atom_limit=atom_limit)
    difference = tuple(int(c) for c in P.subtract(P.compose_linear(P.poly(f),1,1),P.poly(f)))
    cert = None
    if domain['intervals'] and len(f) > 1:
        remaining = node_limit-domain['root_nodes']
        if remaining < 1: raise WorkLimit('discrete optimization exceeds shared root-node budget')
        cert = root_certificate(difference,node_limit=remaining)
    data = _optimization_data(domain,f,cert)
    if sense == 'max' and data['value'] is not None:
        data['value'] = -data['value']
        data['candidates'] = [(n,-v) for n,v in data['candidates']]
    return {'schema':'pp-integer-polynomial-optimum/1','objective':original,'sense':sense,
            'feasible_domain':domain,'difference':difference,'difference_certificate':cert,
            'root_nodes':domain['root_nodes']+(cert['nodes_checked'] if cert else 0),
            'complete':True,'execution_verified':False,**data}


def verify_optimization(result, *, node_limit=100000, atom_limit=128):
    try:
        if result['schema'] != 'pp-integer-polynomial-optimum/1' or result['complete'] is not True or result['execution_verified'] is not False: return False
        domain = result['feasible_domain']
        if not verify_domain(domain,node_limit=node_limit,atom_limit=atom_limit): return False
        original = integer_polynomial(result['objective']); sense = result['sense']
        if sense not in ('min','max'): return False
        f = original if sense == 'min' else tuple(-c for c in original)
        difference = tuple(int(c) for c in P.subtract(P.compose_linear(P.poly(f),1,1),P.poly(f)))
        if tuple(result['difference']) != difference: return False
        cert = result['difference_certificate']
        if domain['intervals'] and len(f)>1:
            if cert['domain'] != [None,None] or tuple(cert['coefficients']) != difference: return False
            if not verify_roots(cert,node_limit=node_limit-domain['root_nodes']): return False
        elif cert is not None: return False
        data = _optimization_data(domain,f,cert)
        if sense == 'max' and data['value'] is not None:
            data['value'] = -data['value']; data['candidates'] = [(n,-v) for n,v in data['candidates']]
        same = lambda a,b: json.dumps(a,sort_keys=True) == json.dumps(b,sort_keys=True)
        return all(same(result[k],v) for k,v in data.items()) and result['root_nodes'] == domain['root_nodes']+(cert['nodes_checked'] if cert else 0)
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError): return False


def _query_predicate(script, *, allow_mod=False):
    """Shared exact single-coordinate SMT polynomial/modular normalization."""
    from .integer_projection import _parse_integer_query
    from .finite_projection import _literal, _simplify, _render
    names, atoms = _parse_integer_query(script)
    if len(names) != 1: raise ValueError('one integer variable required')
    name = names[0]; nonlinear = False; modular = False; operations = 0
    def term(node, depth=0):
        nonlocal operations
        operations += 1
        if operations > 100000 or depth > 64: raise WorkLimit('polynomial expression budget exceeded')
        if node == name: return P.X
        if isinstance(node,str) and node.isascii() and node.isdecimal(): return P.poly([int(node)])
        if not isinstance(node,list) or not node or node[0] not in ('+','-','*'): raise ValueError('polynomial arithmetic required')
        op,args=node[0],node[1:]
        if op == '-' and len(args)==1: return P.scale(term(args[0],depth+1),-1)
        if len(args)<2: raise ValueError('arithmetic arity')
        out=term(args[0],depth+1)
        for arg in args[1:]:
            child=term(arg,depth+1)
            if op=='*' and P.degree(out)+P.degree(child)>64: raise WorkLimit('degree budget exceeded')
            out=P.mul(out,child) if op=='*' else P.add(out,child) if op=='+' else P.subtract(out,child)
            integer_polynomial(int(c) for c in out)
        return out
    def boolean(node):
        nonlocal nonlinear,modular
        if node=='true': return True
        if node=='false': return False
        if not isinstance(node,list) or not node: raise ValueError('polynomial Boolean expression required')
        op,args=node[0],node[1:]
        if op in ('and','or','not'): return {'op':op,'args':[boolean(a) for a in args]}
        if op=='=>':
            out=boolean(args[-1])
            for arg in reversed(args[:-1]): out={'op':'or','args':[{'op':'not','args':[boolean(arg)]},out]}
            return out
        if op in RELATIONS or op=='distinct':
            if len(args)<2: raise ValueError('comparison arity')
            if allow_mod and len(args)==2 and any(isinstance(a,list) and a and a[0]=='mod' for a in args):
                left,right=args;relation='!=' if op=='distinct' else op
                if not (isinstance(left,list) and left and left[0]=='mod'):
                    left,right=right,left;relation={'<':'>','<=':'>=','>':'<','>=':'<=','=':'=','!=':'!='}[relation]
                if len(left)!=3:raise ValueError('mod arity')
                modulus=term(left[2]);value=term(right)
                if len(modulus)!=1 or modulus[0]<=0 or len(value)!=1:raise ValueError('constant positive modulus and integer threshold required')
                polynomial=term(left[1]);modular=True
                return {'poly':[int(c) for c in polynomial],'modulus':int(modulus[0]),'relation':relation,'value':int(value[0])}
            terms=[term(a) for a in args]
            pairs=[(a,b) for i,a in enumerate(terms) for b in terms[i+1:]] if op=='distinct' else list(zip(terms,terms[1:]))
            comparisons=[]
            for a,b in pairs:
                f=P.subtract(a,b); nonlinear |= P.degree(f)>1
                comparisons.append({'poly':[int(c) for c in f],'relation':'!=' if op=='distinct' else op})
            return {'op':'and','args':comparisons}
        raise ValueError('unsupported Boolean polynomial operator')
    predicate={'op':'and','args':[boolean(a) for a in atoms]}
    return name,predicate,nonlinear,modular


def project_univariate_query(script, *, node_limit=100000):
    """Pointwise replacement of a whole polynomial query by integer cells."""
    from .finite_projection import _literal, _simplify, _render
    name,predicate,nonlinear,modular=_query_predicate(script)
    if not nonlinear: raise ValueError('query has no nonlinear polynomial predicate')
    domain=integer_domain(predicate,node_limit=node_limit)
    branches=[]
    for lo,hi in domain['intervals']:
        bounds=[]
        if lo is not None: bounds.append(['>=',name,_literal(lo)])
        if hi is not None: bounds.append(['<=',name,_literal(hi)])
        branches.append(_simplify(['and']+bounds))
    assertion=_simplify(['or']+branches)
    out='\n'.join(['(set-logic QF_LIA)',f'(declare-const {name} Int)',f'(assert {_render(assertion)})','(check-sat)'])+'\n'
    return {'smt':out,'symbol':name,'domain':domain,'meaning':'pointwise equivalence for every integer value'}
