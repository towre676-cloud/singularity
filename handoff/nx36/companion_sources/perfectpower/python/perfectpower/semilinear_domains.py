"""Complete Boolean polynomial/congruence domains and lattice optimization.

Sign cells crossed with finite residue tables give disjoint periodic cells.
Counting uses floor quotients; selection uses counts, never interval scanning.
Optimization uses G(n+M)-G(n) once per cell period, preserving every tie.
"""
from copy import deepcopy
from fractions import Fraction as Q
from math import lcm
import json
from . import polyalg as P
from .polynomial_domains import integer_domain, verify_domain, _holds, _boolean, _critical
from .residue_cover import integer_polynomial, evaluate
from .sturm_fibres import root_certificate, verify_roots
from .divisor_square import WorkLimit


def _normalize(predicate,atom_limit=128):
    atoms=[];nodes=0
    def walk(node,depth=0):
        nonlocal nodes
        nodes+=1
        if depth>64 or nodes>2048:raise WorkLimit('Boolean expression budget exceeded')
        if type(node) is bool:return node
        if not isinstance(node,dict):raise ValueError('structured Boolean predicate required')
        if 'poly' in node:
            modular='modulus' in node
            fields={'poly','relation','modulus','value'} if modular else {'poly','relation'}
            if set(node)!=fields or node['relation'] not in ('=','!=','<','<=','>','>='):
                raise ValueError('polynomial sign or modular comparison atom required')
            if len(atoms)>=atom_limit:raise WorkLimit('atom budget exceeded')
            atom={'poly':list(integer_polynomial(node['poly'])),'relation':node['relation']}
            if modular:
                m,v=node['modulus'],node['value']
                if type(m) is not int or m<1 or type(v) is not int or abs(v).bit_length()>16384:
                    raise ValueError('positive modulus and bounded integer comparison value required')
                atom.update(modulus=m,value=v)
            atoms.append(atom);return {'atom':len(atoms)-1}
        op,args=node.get('op'),node.get('args')
        if set(node)!={'op','args'} or op not in ('and','or','not') or not isinstance(args,(list,tuple)):
            raise ValueError('and/or/not node required')
        if op=='not' and len(args)!=1:raise ValueError('not arity')
        return {'op':op,'args':[walk(a,depth+1) for a in args]}
    return walk(predicate),atoms


def _sign_predicate(atoms):
    return {'op':'and','args':[{'poly':a['poly'],'relation':'='} for a in atoms if 'modulus' not in a]}


def _period(atoms,limit):
    period=1
    for a in atoms:
        if 'modulus' in a:
            period=lcm(period,a['modulus'])
            if period>limit:raise WorkLimit('exact residue period exceeds budget')
    return period


def _minimal_period(bits):
    prefix=[0]*len(bits)
    for i in range(1,len(bits)):
        j=prefix[i-1]
        while j and bits[i]!=bits[j]:j=prefix[j-1]
        if bits[i]==bits[j]:j+=1
        prefix[i]=j
    candidate=len(bits)-prefix[-1]
    return candidate if len(bits)%candidate==0 else len(bits)


def _build(tree,atoms,sign_domain,period,work_limit):
    modular=[a for a in atoms if 'modulus' in a]
    work=period*len(modular)
    if work>work_limit:raise WorkLimit('residue truth table exceeds work budget')
    tables=[[_holds(evaluate(a['poly'],r)%a['modulus']-a['value'],a['relation'])
             for r in range(period)] for a in modular]
    cache={};cells=[];records=[]
    for sign_cell in sign_domain['cells']:
        ordinary=tuple(_holds(v,a['relation']) for a,v in zip(
            [a for a in atoms if 'modulus' not in a],sign_cell['values']))
        if ordinary not in cache:
            work+=period*max(1,len(atoms))
            if work>work_limit:raise WorkLimit('Boolean/residue cell work budget exceeded')
            bits=[]
            for r in range(period):
                si=mi=0;truth=[]
                for a in atoms:
                    if 'modulus' in a:truth.append(tables[mi][r]);mi+=1
                    else:truth.append(ordinary[si]);si+=1
                bits.append(_boolean(tree,truth))
            m=_minimal_period(bits);cache[ordinary]=(m,[r for r in range(m) if bits[r]])
        m,residues=cache[ordinary];lo,hi=sign_cell['interval']
        records.append({'interval':[lo,hi],'ordinary_truth':list(ordinary),'modulus':m,'residues':residues})
        if not residues:continue
        cell={'interval':[lo,hi],'modulus':m,'residues':residues}
        if _count_cell(cell)==0:continue
        if cells and cells[-1]['interval'][1] is not None and lo is not None and cells[-1]['interval'][1]+1==lo and cells[-1]['modulus']==m and cells[-1]['residues']==residues:
            cells[-1]['interval'][1]=hi
        else:cells.append(cell)
    return cells,records,work


def _count_cell(cell,lo=None,hi=None):
    a,b=cell['interval']
    a=lo if a is None else a if lo is None else max(a,lo)
    b=hi if b is None else b if hi is None else min(b,hi)
    if a is not None and b is not None and a>b:return 0
    if a is None or b is None:return None
    m=cell['modulus']
    return sum((b-r)//m-(a-1-r)//m for r in cell['residues'])


def count_domain(domain,lo=None,hi=None):
    if any(v is not None and type(v) is not int for v in (lo,hi)):raise ValueError('integer or infinite endpoints required')
    if lo is not None and hi is not None and lo>hi:return 0
    counts=[_count_cell(c,lo,hi) for c in domain['cells']]
    return None if None in counts else sum(counts)


def contains(domain,n):
    if type(n) is not int:raise ValueError('integer coordinate required')
    return any((lo is None or lo<=n) and (hi is None or n<=hi) and n%c['modulus'] in c['residues']
               for c in domain['cells'] for lo,hi in [c['interval']])


def select(domain,index,*,start=0):
    """Zero-based selected admissible integer >= start; None past a finite end."""
    if type(index) is not int or index<0 or type(start) is not int or max(index.bit_length(),abs(start).bit_length())>16384:
        raise ValueError('bounded integer start and nonnegative rank required')
    total=count_domain(domain,start,None)
    if total is not None and index>=total:return None
    lo=start;hi=start+1
    while count_domain(domain,start,hi)<=index:hi=start+2*(hi-start)
    while lo<hi:
        mid=(lo+hi)//2
        if count_domain(domain,start,mid)>index:hi=mid
        else:lo=mid+1
    return lo


def semilinear_domain(predicate,*,node_limit=100000,period_limit=65536,work_limit=1000000,atom_limit=128):
    if any(type(v) is not int or v<1 for v in (node_limit,period_limit,work_limit,atom_limit)):raise ValueError('positive budgets required')
    tree,atoms=_normalize(predicate,atom_limit);period=_period(atoms,period_limit)
    signs=integer_domain(_sign_predicate(atoms),node_limit=node_limit,atom_limit=atom_limit)
    cells,records,work=_build(tree,atoms,signs,period,work_limit)
    result={'schema':'pp-semilinear-domain/1','predicate':deepcopy(predicate),'tree':tree,'atoms':atoms,
            'sign_domain':signs,'period':period,'cells':cells,'cell_records':records,'work':work,
            'root_nodes':signs['root_nodes'],'complete':True,'execution_verified':False,'domain':'all integers'}
    result['cardinality']=count_domain(result)
    result['nonnegative_density']=str(next((Q(len(c['residues']),c['modulus']) for c in reversed(cells) if c['interval'][1] is None),Q(0)))
    return result


def _same(a,b):return json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True)


def verify_domain(result,*,node_limit=100000,period_limit=65536,work_limit=1000000,atom_limit=128):
    try:
        if result['schema']!='pp-semilinear-domain/1' or result['complete'] is not True or result['execution_verified'] is not False or result['domain']!='all integers':return False
        tree,atoms=_normalize(result['predicate'],atom_limit);period=_period(atoms,period_limit);signs=result['sign_domain']
        if not _same(signs['predicate'],_sign_predicate(atoms)) or not verify_sign_domain(signs,node_limit=node_limit,atom_limit=atom_limit):return False
        cells,records,work=_build(tree,atoms,signs,period,work_limit)
        density=str(next((Q(len(c['residues']),c['modulus']) for c in reversed(cells) if c['interval'][1] is None),Q(0)))
        expected={'tree':tree,'atoms':atoms,'period':period,'cells':cells,'cell_records':records,'work':work,'root_nodes':signs['root_nodes'],'cardinality':count_domain({'cells':cells}),'nonnegative_density':density}
        return all(_same(result[k],v) for k,v in expected.items())
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError):return False


# Keep the imported sign checker separate from the public semilinear checker.
from .polynomial_domains import verify_domain as verify_sign_domain


def _optimizer_data(domain,f,certificates,work_limit):
    if not domain['cells']:return {'status':'EMPTY','value':None,'points':[],'optimizer_domain':None,'candidates':[],'candidate_work':0}
    if len(f)==1:return {'status':'OPTIMAL','value':f[0],'points':None,'optimizer_domain':domain,'candidates':[],'candidate_work':0}
    for c in domain['cells']:
        lo,hi=c['interval']
        if lo is None and f[-1]*(-1)**(len(f)-1)<0 or hi is None and f[-1]<0:
            return {'status':'UNBOUNDED','value':None,'points':[],'optimizer_domain':None,'candidates':[],'candidate_work':0}
    cuts={r['modulus']:_critical([r['certificate']]) for r in certificates};candidates=set();work=0
    for c in domain['cells']:
        lo,hi=c['interval'];m=c['modulus'];critical=cuts[m]
        work+=len(c['residues'])*(2+4*len(critical))
        if work>work_limit:raise WorkLimit('complete lattice candidate budget exceeded')
        for r in c['residues']:
            values=[]
            if lo is not None:values.append(lo+(r-lo)%m)
            if hi is not None:values.append(hi-(hi-r)%m)
            for cut in critical:
                lower=cut-(cut-r)%m;upper=cut+(r-cut)%m
                values.extend((lower,upper,lower+m,upper+m))
            candidates.update(n for n in values if (lo is None or lo<=n) and (hi is None or n<=hi))
    if not candidates:raise AssertionError('bounded nonconstant objective lacks lattice candidate')
    values=[(n,evaluate(f,n)) for n in sorted(candidates)];value=min(v for n,v in values)
    return {'status':'OPTIMAL','value':value,'points':[n for n,v in values if v==value],
            'optimizer_domain':None,'candidates':values,'candidate_work':work}


def optimize_semilinear(predicate,objective,*,sense='min',node_limit=100000,period_limit=65536,work_limit=1000000,atom_limit=128):
    if sense not in ('min','max'):raise ValueError('min or max required')
    original=integer_polynomial(objective);f=original if sense=='min' else tuple(-c for c in original)
    domain=semilinear_domain(predicate,node_limit=node_limit,period_limit=period_limit,work_limit=work_limit,atom_limit=atom_limit)
    certificates=[];used=domain['root_nodes']
    if domain['cells'] and len(f)>1:
        for m in sorted({c['modulus'] for c in domain['cells']}):
            if used>=node_limit:raise WorkLimit('shared lattice optimization root budget exceeded')
            difference=integer_polynomial(int(c) for c in P.subtract(P.compose_linear(P.poly(f),m,1),P.poly(f)))
            cert=root_certificate(difference,node_limit=node_limit-used);used+=cert['nodes_checked']
            certificates.append({'modulus':m,'certificate':cert})
    data=_optimizer_data(domain,f,certificates,work_limit)
    if sense=='max' and data['value'] is not None:
        data['value']=-data['value'];data['candidates']=[(n,-v) for n,v in data['candidates']]
    return {'schema':'pp-semilinear-optimum/1','objective':original,'sense':sense,'feasible_domain':domain,
            'difference_certificates':certificates,'root_nodes':used,'complete':True,'execution_verified':False,**data}


def verify_optimization(result,*,node_limit=100000,period_limit=65536,work_limit=1000000,atom_limit=128):
    try:
        if result['schema']!='pp-semilinear-optimum/1' or result['complete'] is not True or result['execution_verified'] is not False:return False
        domain=result['feasible_domain']
        if not verify_domain(domain,node_limit=node_limit,period_limit=period_limit,work_limit=work_limit,atom_limit=atom_limit):return False
        original=integer_polynomial(result['objective']);sense=result['sense']
        if sense not in ('min','max'):return False
        f=original if sense=='min' else tuple(-c for c in original);certificates=result['difference_certificates'];used=domain['root_nodes']
        expected=sorted({c['modulus'] for c in domain['cells']}) if domain['cells'] and len(f)>1 else []
        if [r['modulus'] for r in certificates]!=expected:return False
        for r in certificates:
            m=r['modulus'];cert=r['certificate']
            difference=integer_polynomial(int(c) for c in P.subtract(P.compose_linear(P.poly(f),m,1),P.poly(f)))
            if tuple(cert['coefficients'])!=difference or cert['domain']!=[None,None] or used>=node_limit or not verify_roots(cert,node_limit=node_limit-used):return False
            used+=cert['nodes_checked']
        data=_optimizer_data(domain,f,certificates,work_limit)
        if sense=='max' and data['value'] is not None:
            data['value']=-data['value'];data['candidates']=[(n,-v) for n,v in data['candidates']]
        return used==result['root_nodes'] and all(_same(result[k],v) for k,v in data.items())
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError):return False


def render_domains(domains,symbol,*,branch_limit=128):
    """Exact Presburger interval/congruence formula; bound expansion size."""
    from .finite_projection import _literal,_simplify,_render
    branches=[];work=0
    for domain in domains:
        for c in domain['cells']:
            lo,hi=c['interval'];m=c['modulus'];bounds=[]
            if lo is not None:bounds.append(['>=',symbol,_literal(lo)])
            if hi is not None:bounds.append(['<=',symbol,_literal(hi)])
            if m!=1:
                work+=len(c['residues'])
                bounds.append(_simplify(['or']+[['=',['mod',symbol,str(m)],str(r)] for r in c['residues']]))
            else:work+=1
            if work>branch_limit:raise WorkLimit('complete Presburger expansion exceeds branch budget')
            branch=_simplify(['and']+bounds)
            if branch not in branches:branches.append(branch)
    assertion=_simplify(['or']+branches)
    return '\n'.join(['(set-logic QF_LIA)',f'(declare-const {symbol} Int)',f'(assert {_render(assertion)})','(check-sat)'])+'\n'


def project_semilinear_query(script,*,node_limit=100000,period_limit=65536,branch_limit=128):
    from .polynomial_domains import _query_predicate
    name,predicate,nonlinear,modular=_query_predicate(script,allow_mod=True)
    if not modular:raise ValueError('no modular atom for semilinear pass')
    domain=semilinear_domain(predicate,node_limit=node_limit,period_limit=period_limit)
    return {'smt':render_domains([domain],name,branch_limit=branch_limit),'symbol':name,'domain':domain,
            'meaning':'pointwise equivalence for every integer coordinate'}
