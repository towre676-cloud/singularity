"""Exact minimal linear machines for supplied rational operator outputs.

First restrict to states reached from the seed; then quotient directions
invisible to every future readout. Finite word witnesses and a nonsingular
Hankel minor certify minimal state dimension over Q, not primitive-call cost.
Words name chronological column-vector execution, unless explicitly reversed.
"""
from fractions import Fraction as Q
import json
from . import exact_linear as E
from .divisor_square import WorkLimit


def _q(x):
    if type(x) not in (int,str,Q):raise ValueError('exact rational entry required')
    v=Q(x)
    if max(abs(v.numerator).bit_length(),v.denominator.bit_length())>8192:raise WorkLimit('rational entry exceeds bit budget')
    return v


def _matrix(rows,n,m):
    a=tuple(tuple(_q(x) for x in row) for row in rows)
    if len(a)!=n or any(len(row)!=m for row in a):raise ValueError('matrix shape mismatch')
    return a


def _inputs(operators,seed,readouts):
    seed=tuple(map(_q,seed));n=len(seed);ops=tuple(operators);h=tuple(readouts)
    if not 1<=n<=64 or not 1<=len(ops)<=16 or not 1<=len(h)<=64:raise ValueError('state/context/readout shape budget exceeded')
    return tuple(_matrix(a,n,n) for a in ops),seed,_matrix(h,len(h),n)


def _rank(rows):return E.rank(rows) if rows else 0


def _mm(a,b,n,m,k):
    return tuple(tuple(sum(a[i][t]*b[t][j] for t in range(m)) for j in range(k)) for i in range(n))


def _apply(a,v):return tuple(sum(x*y for x,y in zip(row,v)) for row in a)


def _rows_times(row,a,n):return tuple(sum(row[t]*a[t][j] for t in range(n)) for j in range(n))


def _coordinate(basis,vector):
    if not basis:
        if any(vector):raise ValueError('vector outside zero span')
        return ()
    c=E.solve(E.transpose(basis),vector)
    if c is None:raise ValueError('vector outside supplied span')
    return tuple(map(_q,c))


def _word(ops,seed,word):
    v=seed
    for i in word:
        if type(i) is not int or not 0<=i<len(ops):raise ValueError('invalid operator letter')
        v=tuple(map(_q,_apply(ops[i],v)))
    return v


def _row_word(ops,row,word):
    for i in reversed(word):
        if type(i) is not int or not 0<=i<len(ops):raise ValueError('invalid operator letter')
        row=tuple(map(_q,_rows_times(row,ops[i],len(row))))
    return row


def _det(a):
    n=len(a);a=[list(row) for row in a];det=Q(1)
    for j in range(n):
        pivot=next((i for i in range(j,n) if a[i][j]),None)
        if pivot is None:return Q(0)
        if pivot!=j:a[j],a[pivot]=a[pivot],a[j];det=-det
        v=a[j][j];det*=v
        for i in range(j+1,n):
            factor=a[i][j]/v
            for k in range(j+1,n):a[i][k]-=factor*a[j][k]
    return det


def minimal_machine(operators,seed,readouts,*,product_limit=8192):
    ops,seed,h=_inputs(operators,seed,readouts);n=len(seed)
    if type(product_limit) is not int or product_limit<1:raise ValueError('positive product budget required')
    basis=[];words=[];products=0
    if any(seed):basis.append(seed);words.append(())
    cursor=0
    while cursor<len(basis):
        for i,a in enumerate(ops):
            products+=1
            if products>product_limit:raise WorkLimit('reachable closure exceeds budget')
            v=tuple(map(_q,_apply(a,basis[cursor])))
            if _rank(basis+[v])>len(basis):basis.append(v);words.append(words[cursor]+(i,))
        cursor+=1
    r=len(basis);lift=tuple(tuple(v[i] for v in basis) for i in range(n))
    restricted=tuple(tuple(zip(*(_coordinate(basis,_apply(a,v)) for v in basis))) if r else () for a in ops)
    restricted=tuple(_matrix(a,r,r) for a in restricted)
    initial=_coordinate(basis,seed);hr=_mm(h,lift,len(h),n,r)
    observations=[];row_words=[]
    for i,row in enumerate(hr):
        if _rank(observations+[row])>len(observations):observations.append(row);row_words.append((i,()))
    cursor=0
    while cursor<len(observations):
        for i,a in enumerate(restricted):
            products+=1
            if products>product_limit:raise WorkLimit('observable closure exceeds budget')
            row=tuple(map(_q,_rows_times(observations[cursor],a,r)))
            if _rank(observations+[row])>len(observations):
                observations.append(row);output,w=row_words[cursor];row_words.append((output,(i,)+w))
        cursor+=1
    k=len(observations);o=tuple(observations)
    compressed=tuple(tuple(_coordinate(o,_rows_times(row,a,r)) for row in o) for a in restricted)
    decoder=tuple(_coordinate(o,row) for row in hr);compressed_seed=_apply(o,initial)
    columns=E.rref(o)[1] if k else ()
    minor=tuple(tuple(row[j] for j in columns) for row in o)
    result={'schema':'pp-observable-machine/1','operators':ops,'seed':seed,'readouts':h,
        'state_dimension':n,'reachable_dimension':r,'minimal_dimension':k,'reachable_basis':lift,
        'state_words':tuple(words),'restricted_operators':restricted,'reachable_seed':initial,
        'observable_rows':o,'readout_words':tuple(row_words),'operators_minimal':compressed,
        'seed_minimal':compressed_seed,'readouts_minimal':decoder,'hankel_columns':columns,
        'hankel_minor':minor,'hankel_determinant':_det(minor),'closure_products':products,
        'word_order':'chronological column-vector execution','field':'Q','execution_verified':False,
        'scope':'all finite operator words and supplied readouts; minimal linear state dimension, not integral coordinates or primitive-call optimality'}
    if not verify_machine(result):raise AssertionError('minimal machine replay failed')
    return result


def verify_machine(receipt):
    """Check finite spanning words, closure identities and the Hankel minor.

    Does not discover reachable or observable bases or perform minimization.
    """
    try:
        if receipt['schema']!='pp-observable-machine/1' or receipt['field']!='Q' or receipt['execution_verified'] is not False or receipt['word_order']!='chronological column-vector execution':return False
        ops,seed,h=_inputs(receipt['operators'],receipt['seed'],receipt['readouts']);n=len(seed);m=len(h)
        r=receipt['reachable_dimension'];k=receipt['minimal_dimension']
        if any(type(t) is not int for t in (r,k)) or not 0<=k<=r<=n or receipt['state_dimension']!=n:return False
        lift=_matrix(receipt['reachable_basis'],n,r);words=receipt['state_words']
        restricted=tuple(_matrix(a,r,r) for a in receipt['restricted_operators'])
        initial=tuple(map(_q,receipt['reachable_seed']))
        if len(words)!=r or any(len(w)>n for w in words) or len(restricted)!=len(ops) or len(initial)!=r or _rank(E.transpose(lift))!=r:return False
        if _apply(lift,initial)!=seed:return False
        if any(_word(ops,seed,w)!=v for w,v in zip(words,E.transpose(lift))):return False
        if any(_mm(a,lift,n,n,r)!=_mm(lift,b,n,r,r) for a,b in zip(ops,restricted)):return False
        o=_matrix(receipt['observable_rows'],k,r);row_words=receipt['readout_words']
        compressed=tuple(_matrix(a,k,k) for a in receipt['operators_minimal']);decoder=_matrix(receipt['readouts_minimal'],m,k)
        hr=_mm(h,lift,m,n,r)
        if _rank(o)!=k or len(row_words)!=k or len(compressed)!=len(ops):return False
        for row,(index,word) in zip(o,row_words):
            if type(index) is not int or not 0<=index<m or len(word)>r or _row_word(restricted,hr[index],word)!=row:return False
        if any(_mm(o,a,k,r,r)!=_mm(b,o,k,k,r) for a,b in zip(restricted,compressed)):return False
        if _mm(decoder,o,m,k,r)!=hr or tuple(map(_q,receipt['seed_minimal']))!=_apply(o,initial):return False
        columns=tuple(receipt['hankel_columns'])
        if len(columns)!=k or len(set(columns))!=k or any(type(j) is not int or not 0<=j<r for j in columns):return False
        minor=tuple(tuple(row[j] for j in columns) for row in o)
        if _matrix(receipt['hankel_minor'],k,k)!=minor:return False
        return _q(receipt['hankel_determinant'])==_det(minor)!=0
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError,OverflowError):return False


def word_output(receipt,word,*,order='execution',original=False):
    if not verify_machine(receipt):raise ValueError('invalid machine certificate')
    if order not in ('execution','written'):raise ValueError('execution or written word order required')
    word=tuple(word)
    if len(word)>4096:raise WorkLimit('word length exceeds budget')
    if order=='written':word=word[::-1]
    if original:
        ops,seed,h=_inputs(receipt['operators'],receipt['seed'],receipt['readouts'])
    else:
        k=receipt['minimal_dimension'];ops=tuple(_matrix(a,k,k) for a in receipt['operators_minimal'])
        seed=tuple(map(_q,receipt['seed_minimal']));h=_matrix(receipt['readouts_minimal'],len(receipt['readouts']),k)
    return _apply(h,_word(ops,seed,word))


def recurrence_batch(models):
    """Share an exact machine across supplied Recurrence definitions."""
    from .recurrence import Recurrence
    from .recurrence_identity import companion
    models=tuple(models)
    if not models or any(not isinstance(m,Recurrence) for m in models):raise ValueError('nonempty supplied recurrence models required')
    dims=[len(m.initial) for m in models];n=sum(dims)
    if n>64 or len(models)>64:raise WorkLimit('recurrence batch exceeds state budget')
    a=[[Q(0)]*n for _ in range(n)];h=[];seed=();offset=0
    for model,d in zip(models,dims):
        block=companion(model)
        for i in range(d):a[offset+i][offset:offset+d]=block[i]
        row=[Q(0)]*n;row[offset]=Q(1);h.append(row);seed+=model.initial;offset+=d
    return minimal_machine([a],seed,h)


def power_outputs(receipt,index,*,context=0,original=False):
    """Read a repeated operator word by exact binary powering."""
    if not verify_machine(receipt):raise ValueError('invalid machine certificate')
    if type(index) is not int or index<0 or index.bit_length()>64:raise ValueError('nonnegative 64-bit index required')
    if type(context) is not int or not 0<=context<len(receipt['operators']):raise ValueError('invalid operator context')
    if original:
        ops,seed,h=_inputs(receipt['operators'],receipt['seed'],receipt['readouts']);n=len(seed)
    else:
        n=receipt['minimal_dimension'];ops=tuple(_matrix(a,n,n) for a in receipt['operators_minimal'])
        seed=tuple(map(_q,receipt['seed_minimal']));h=_matrix(receipt['readouts_minimal'],len(receipt['readouts']),n)
    a=ops[context];v=seed
    while index:
        if index&1:v=tuple(map(_q,_apply(a,v)))
        index//=2
        if index:a=tuple(tuple(map(_q,row)) for row in _mm(a,a,n,n,n))
    return tuple(map(_q,_apply(h,v)))
