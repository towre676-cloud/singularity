"""Constructive integral lifts with replayable unimodular Smith certificates.

Exact standard-library arithmetic. Certificate replay is not a Lean proof.
Columns generate lattices; kernel vectors form a saturated Z-basis.
"""
from .integral_lattice import _matrix


class ReductionLimit(ValueError):
    """No complete reduction is returned when an explicit budget is exhausted."""


def _identity(n):
    return [[int(i == j) for j in range(n)] for i in range(n)]


def _apply(a, v):
    return [sum(x*y for x, y in zip(row, v)) for row in a]


def _multiply(a, b):
    return [[sum(x*y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


def _operation(a, op):
    axis, kind, i, j, coefficient = op
    if axis == 'column':
        if kind == 'swap':
            for row in a: row[i], row[j] = row[j], row[i]
        elif kind == 'add':
            for row in a: row[i] += coefficient * row[j]
        else:
            for row in a: row[i] *= -1
    elif kind == 'swap':
        a[i], a[j] = a[j], a[i]
    elif kind == 'add':
        a[i] = [x + coefficient*y for x, y in zip(a[i], a[j])]
    else:
        a[i] = [-x for x in a[i]]


def smith_certificate(matrix, *, operation_limit=100_000, entry_bit_limit=100_000):
    """Return D=U A V, positive diagonal d_i dividing d_(i+1).

    Only swaps, negations, and integer row/column additions are used. A
    recorded operation transcript independently certifies U,V unimodular.
    Budgets cap matrix dimensions, operation count and intermediate bit size.
    """
    original = _matrix(matrix)
    m, n = len(original), len(original[0])
    if any(type(x) is not int or x < 1 for x in (operation_limit, entry_bit_limit)):
        raise ValueError('positive integer budgets required')
    if m*n + m*m + n*n > operation_limit:
        raise ReductionLimit('matrix allocation budget exceeded')
    a = [list(row) for row in original]
    u, v, operations = _identity(m), _identity(n), []

    def bounds():
        if any(abs(x).bit_length() > entry_bit_limit for block in (a,u,v) for row in block for x in row):
            raise ReductionLimit('intermediate entry bit budget exceeded')

    def step(axis, kind, i, j=0, coefficient=0):
        if len(operations) >= operation_limit:
            raise ReductionLimit('Smith operation budget exceeded')
        op = [axis, kind, i, j, coefficient]
        _operation(a, op)
        _operation(u if axis == 'row' else v, op)
        operations.append(op)
        bounds()

    bounds()
    for k in range(min(m,n)):
        candidates = [(abs(a[i][j]),i,j) for i in range(k,m) for j in range(k,n) if a[i][j]]
        if not candidates: break
        _, i, j = min(candidates)
        if i != k: step('row','swap',k,i)
        if j != k: step('column','swap',k,j)
        while True:
            if a[k][k] < 0: step('row','negate',k)
            for i in range(k+1,m):
                if a[i][k]:
                    q = a[i][k] // a[k][k]
                    if q: step('row','add',i,k,-q)
                    if a[i][k]: step('row','swap',k,i)
                    break
            else:
                for j in range(k+1,n):
                    if a[k][j]:
                        q = a[k][j] // a[k][k]
                        if q: step('column','add',j,k,-q)
                        if a[k][j]: step('column','swap',k,j)
                        break
                else:
                    # A diagonal pivot must divide the remaining block. Feed
                    # an offending entry into its row, then resume Euclid.
                    bad = next(((i,j) for i in range(k+1,m) for j in range(k+1,n)
                                if a[i][j] % a[k][k]), None)
                    if bad is None: break
                    step('row','add',k,bad[0],1)
        if a[k][k] < 0: step('row','negate',k)
    diagonal = [a[i][i] for i in range(min(m,n)) if a[i][i]]
    result = {'matrix':[list(row) for row in original], 'left':u, 'right':v,
              'diagonal_matrix':a, 'smith_factors':diagonal, 'rank':len(diagonal),
              'operations':operations, 'operation_count':len(operations),
              'execution_verified':False, 'certificate_kind':'unimodular operation transcript'}
    if not verify_smith(result, operation_limit=operation_limit, entry_bit_limit=entry_bit_limit):
        raise AssertionError('Smith transcript replay failed')
    return result


def verify_smith(certificate, *, operation_limit=100_000, entry_bit_limit=100_000):
    """Replay a possibly untrusted certificate without rerunning reduction.

    False on malformed, corrupted or oversized input. Each operation itself
    has an integer inverse; no determinant or modular rank oracle is trusted.
    """
    try:
        if any(type(x) is not int or x < 1 for x in (operation_limit,entry_bit_limit)): return False
        original = _matrix(certificate['matrix']); m,n = len(original),len(original[0])
        operations = certificate['operations']
        if not isinstance(operations,(list,tuple)) or len(operations)>operation_limit: return False
        if m*n+m*m+n*n>operation_limit: return False
        a=[list(row) for row in original];u,v=_identity(m),_identity(n)
        def bounded():
            return all(abs(x).bit_length()<=entry_bit_limit for block in (a,u,v) for row in block for x in row)
        if not bounded(): return False
        for op in operations:
            if not isinstance(op,(list,tuple)) or len(op)!=5: return False
            axis,kind,i,j,c = op
            size = m if axis=='row' else n if axis=='column' else 0
            if kind not in ('swap','add','negate') or any(type(x) is not int for x in (i,j,c)): return False
            if not 0<=i<size or not 0<=j<size: return False
            if kind in ('swap','add') and i==j: return False
            if kind!='add' and c!=0: return False
            if abs(c).bit_length()>entry_bit_limit: return False
            _operation(a,op);_operation(u if axis=='row' else v,op)
            if not bounded(): return False
        if any(a[i][j] for i in range(m) for j in range(n) if i!=j): return False
        factors=[a[i][i] for i in range(min(m,n)) if a[i][i]]
        if any(x<=0 for x in factors): return False
        if [a[i][i] for i in range(min(m,n))]!=factors+[0]*(min(m,n)-len(factors)): return False
        if any(y%x for x,y in zip(factors,factors[1:])): return False
        # Compare exact integer matrices, rejecting Python's bool==int alias.
        for key,computed in (('left',u),('right',v),('diagonal_matrix',a)):
            if [list(row) for row in _matrix(certificate[key])]!=computed: return False
        if certificate['smith_factors']!=factors or any(type(x) is not int for x in certificate['smith_factors']): return False
        return type(certificate['rank']) is int and certificate['rank']==len(factors) and type(certificate['operation_count']) is int and certificate['operation_count']==len(operations)
    except (KeyError,TypeError,ValueError,IndexError,ZeroDivisionError):
        return False


def _solve_with_certificate(cert, vector):
    a,u,v=cert['matrix'],cert['left'],cert['right'];m,n=len(a),len(a[0])
    b=list(vector)
    if len(b)!=m or any(type(x) is not int for x in b): raise ValueError('matching integer vector required')
    transformed=_apply(u,b);r=cert['rank'];diagonal=cert['smith_factors']
    for i,value in enumerate(transformed):
        if i<r and value%diagonal[i]:
            return {'status':'DIVISIBILITY_OBSTRUCTION','annihilator':u[i],
                    'modulus':diagonal[i],'pairing':value,'residue':value%diagonal[i],
                    'annihilator_times_matrix':[sum(u[i][k]*a[k][j] for k in range(m)) for j in range(n)]}
        if i>=r and value:
            return {'status':'RATIONAL_IMAGE_OBSTRUCTION','annihilator':u[i],
                    'pairing':value,'annihilator_times_matrix':[0]*n}
    coordinates=[transformed[i]//diagonal[i] if i<r else 0 for i in range(n)]
    particular=_apply(v,coordinates)
    basis=[[v[i][j] for i in range(n)] for j in range(r,n)]
    if _apply(a,particular)!=b or any(any(_apply(a,w)) for w in basis):
        raise AssertionError('invalid integer fibre')
    return {'status':'INTEGER_AFFINE_FIBRE','particular':particular,'kernel_basis':basis,
            'parameter_count':n-r,'parameter_domain':'Z','complete':True,
            'transformed_rhs':transformed}


def solve_integer(matrix, vector, **budgets):
    """All integer x with A x=b: x=x0+sum t_i k_i, t_i in Z.

    A dual row certifies impossibility either exactly or modulo d>1.
    Nonunique rational coordinates never imply integer impossibility.
    """
    cert=smith_certificate(matrix,**budgets)
    return dict(_solve_with_certificate(cert,vector),certificate=cert,execution_verified=False)


def integral_task_section(target, carrier, **budgets):
    """Construct every integral T with carrier*T=target, column by column.

    Each target column has independent integer kernel parameters. Injection
    is not asserted. One carrier certificate is shared by all columns.
    """
    f,g=_matrix(target),_matrix(carrier)
    if len(f)!=len(g): raise ValueError('common output dimension required')
    cert=smith_certificate(g,**budgets);columns=[]
    for j,col in enumerate(zip(*f)):
        result=_solve_with_certificate(cert,col)
        if result['status']!='INTEGER_AFFINE_FIBRE':
            return dict(result,target_column=j,certificate=cert,execution_verified=False)
        columns.append(result['particular'])
    lift=[list(row) for row in zip(*columns)]
    if _multiply(g,lift)!=[list(row) for row in f]: raise AssertionError('invalid integral task lift')
    return {'status':'INTEGRAL_TASK_SECTION','lift':lift,
            'kernel_basis':result['kernel_basis'],'target_columns':len(columns),
            'parameter_count':result['parameter_count']*len(columns),'parameter_domain':'Z',
            'complete':True,'certificate':cert,'execution_verified':False}


def integral_intertwiners(source, target, *, variable_limit=256, **budgets):
    """Saturated integral basis for all T with T*A_i=B_i*T.

    Clearing denominators of a rational nullspace can miss integer solutions;
    the unimodular right matrix instead parameterizes the entire Z-kernel.
    """
    aa,bb=tuple(map(_matrix,source)),tuple(map(_matrix,target))
    if not aa or len(aa)!=len(bb): raise ValueError('matching nonempty context families required')
    n,m=len(aa[0]),len(bb[0])
    if any(len(a)!=n or len(a[0])!=n for a in aa) or any(len(b)!=m or len(b[0])!=m for b in bb):
        raise ValueError('fixed square context dimensions required')
    if type(variable_limit) is not int or variable_limit<1 or m*n>variable_limit:
        raise ReductionLimit('intertwiner variable budget exceeded')
    rows=[]
    for a,b in zip(aa,bb):
        for i in range(m):
            for j in range(n):
                row=[0]*(m*n)
                for k in range(n): row[i*n+k]+=a[k][j]
                for k in range(m): row[k*n+j]-=b[i][k]
                rows.append(row)
    solved=solve_integer(rows,[0]*len(rows),**budgets)
    basis=[[[w[i*n+j] for j in range(n)] for i in range(m)] for w in solved['kernel_basis']]
    for t in basis:
        if any(_multiply(t,a)!=_multiply(b,t) for a,b in zip(aa,bb)):
            raise AssertionError('invalid integral intertwiner')
    return {'status':'INTEGRAL_INTERTWINER_MODULE','basis':basis,'dimension':len(basis),
            'contexts':len(aa),'variables':m*n,'complete':True,
            'certificate':solved['certificate'],'execution_verified':False}


def compare_column_lattices(left, right, **budgets):
    """Same embedded Z-lattice iff integral transports exist both ways.

    Equal Smith factors only classify abstract cokernels up to ambient basis
    change; they do not assert equality of the actual embedded lattices.
    """
    a,b=_matrix(left),_matrix(right)
    if len(a)!=len(b): raise ValueError('common ambient dimension required')
    b_in_a=integral_task_section(b,a,**budgets)
    if b_in_a['status']!='INTEGRAL_TASK_SECTION':
        return {'equal':False,'failed_inclusion':'right_in_left','obstruction':b_in_a,'execution_verified':False}
    a_in_b=integral_task_section(a,b,**budgets)
    if a_in_b['status']!='INTEGRAL_TASK_SECTION':
        return {'equal':False,'failed_inclusion':'left_in_right','obstruction':a_in_b,'execution_verified':False}
    return {'equal':True,'right_in_left':b_in_a,'left_in_right':a_in_b,'execution_verified':False}
