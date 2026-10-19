"""Minimal integral output machines on saturated reachable lattices.

Two unimodular Smith certificates replace rational state coordinates with
integer coordinates. Saturation is not the Z-span of actual orbit words.
All outputs of the fixed supplied seed are preserved for all finite words.
"""
from fractions import Fraction as Q
from math import prod
from . import exact_linear as E
from .observable_machine import (minimal_machine,verify_machine,_mm,_apply,
    _word,_row_word,_q)
from .integer_lifting import smith_certificate,verify_smith,_solve_with_certificate
from .divisor_square import WorkLimit


def _integer(x):
    if type(x) not in (int,Q,str) or Q(x).denominator!=1:raise ValueError('integer entries required')
    return int(_q(x))


def _mat(a,n,m):
    a=tuple(tuple(_integer(x) for x in row) for row in a)
    if len(a)!=n or any(len(row)!=m for row in a):raise ValueError('integer matrix shape mismatch')
    return a


def _mul(a,b,n,m,k):return _mat(_mm(a,b,n,m,k),n,k)
def _iv(v):return tuple(_integer(x) for x in v)


def _charts(machine,reach_cert,observe_cert):
    n=machine['state_dimension'];r=machine['reachable_dimension'];k=machine['minimal_dimension']
    ops=tuple(_mat(a,n,n) for a in machine['operators']);s=_iv(machine['seed'])
    h=_mat(machine['readouts'],len(machine['readouts']),n)
    if r:
        u=_mat(reach_cert['left'],n,n);uinv=_mat(E.inverse(u),n,n)
        lift=tuple(tuple(row[j] for j in range(r)) for row in uinv);coordinates=u[:r]
    else:lift=tuple(() for _ in range(n));coordinates=()
    restricted=tuple(_mul(_mul(coordinates,a,r,n,n),lift,r,n,r) for a in ops)
    initial=_iv(_apply(coordinates,s));hr=_mul(h,lift,len(h),n,r)
    observations=tuple(_iv(_apply(E.transpose(lift),_row_word(ops,h[index],word))) if r else ()
                       for index,word in machine['readout_words'])
    if k:
        v=_mat(observe_cert['right'],r,r);vinv=_mat(E.inverse(v),r,r)
    else:v=_mat(E.identity(r),r,r);vinv=v
    quotient=vinv[:k];section=tuple(tuple(row[j] for j in range(k)) for row in v)
    kernel=tuple(tuple(row[j] for j in range(k,r)) for row in v)
    compressed=tuple(_mul(_mul(quotient,a,k,r,r),section,k,r,k) for a in restricted)
    decoder=_mul(hr,section,len(h),r,k);seed=_iv(_apply(quotient,initial))
    return {'reachable_lift':lift,'reachable_coordinates':coordinates,'reachable_operators':restricted,
        'reachable_seed':initial,'observation_matrix':observations,'quotient':quotient,'section':section,
        'invisible_kernel':kernel,'operators_minimal':compressed,'readouts_minimal':decoder,'seed_minimal':seed}


def integral_machine(operators,seed,readouts,*,operation_limit=100000,entry_bit_limit=8192,product_limit=8192):
    seed=_iv(seed);n=len(seed);ops=tuple(_mat(a,n,n) for a in operators)
    h=_mat(readouts,len(readouts),n)
    machine=minimal_machine(ops,seed,h,product_limit=product_limit)
    return integralize_machine(machine,operation_limit=operation_limit,entry_bit_limit=entry_bit_limit)


def integralize_machine(machine,*,operation_limit=100000,entry_bit_limit=8192):
    """Reuse a checked rational certificate with integral source data."""
    if not verify_machine(machine):raise ValueError('invalid rational machine certificate')
    n=machine['state_dimension'];_iv(machine['seed'])
    tuple(_mat(a,n,n) for a in machine['operators']);_mat(machine['readouts'],len(machine['readouts']),n)
    if type(entry_bit_limit) is not int or not 1<=entry_bit_limit<=8192:raise ValueError('bit budget must be 1 through 8192')
    if type(operation_limit) is not int or operation_limit<1:raise ValueError('positive Smith operation budget required')
    r=machine['reachable_dimension'];k=machine['minimal_dimension']
    j=_mat(machine['reachable_basis'],n,r)
    budgets={'operation_limit':operation_limit,'entry_bit_limit':entry_bit_limit}
    reach=smith_certificate(j,**budgets) if r else None
    # First derive the integer saturated-reachable chart and witness rows.
    preliminary=_charts(machine,reach,None if not k else {'right':E.identity(r)})
    observation=smith_certificate(preliminary['observation_matrix'],**budgets) if k else None
    charts=_charts(machine,reach,observation)
    result={'schema':'pp-integral-machine/1','rational_certificate':machine,'reachable_smith':reach,
        'observation_smith':observation,'state_dimension':n,'reachable_dimension':r,'minimal_dimension':k,
        'selected_word_lattice_index':prod(reach['smith_factors']) if reach else 1,
        'observation_image_factors':observation['smith_factors'] if observation else [],
        'field':'Z','word_order':'chronological column-vector execution','execution_verified':False,
        'scope':'minimal integral realization of fixed-seed future outputs on the saturated rational reachable lattice; not an exact integral orbit-word module or primitive-cost optimum',**charts}
    if not verify_integral_machine(result,**budgets):raise AssertionError('integral machine replay failed')
    return result


def verify_integral_machine(receipt,*,operation_limit=100000,entry_bit_limit=8192):
    """Replay word/Hankel and unimodular transcripts plus descent identities."""
    try:
        if type(operation_limit) is not int or operation_limit<1 or type(entry_bit_limit) is not int or not 1<=entry_bit_limit<=8192:return False
        if receipt['schema']!='pp-integral-machine/1' or receipt['field']!='Z' or receipt['execution_verified'] is not False or receipt['word_order']!='chronological column-vector execution':return False
        machine=receipt['rational_certificate']
        if not verify_machine(machine):return False
        n=machine['state_dimension'];r=machine['reachable_dimension'];k=machine['minimal_dimension'];m=len(machine['readouts'])
        if any(type(receipt[key]) is not int or receipt[key]!=v for key,v in [('state_dimension',n),('reachable_dimension',r),('minimal_dimension',k)]):return False
        ops=tuple(_mat(a,n,n) for a in machine['operators']);s=_iv(machine['seed']);h=_mat(machine['readouts'],m,n)
        reach=receipt['reachable_smith'];observation=receipt['observation_smith']
        budgets={'operation_limit':operation_limit,'entry_bit_limit':entry_bit_limit}
        if r:
            if not verify_smith(reach,**budgets) or _mat(reach['matrix'],n,r)!=_mat(machine['reachable_basis'],n,r) or reach['rank']!=r:return False
        elif reach is not None:return False
        lift=_mat(receipt['reachable_lift'],n,r);coordinates=_mat(receipt['reachable_coordinates'],r,n)
        if r:
            if coordinates!=_mat(reach['left'],n,n)[:r] or _mul(reach['left'],lift,n,n,r)!=tuple(tuple(int(i==j) for j in range(r)) for i in range(n)):return False
        restricted=tuple(_mat(a,r,r) for a in receipt['reachable_operators']);initial=_iv(receipt['reachable_seed'])
        if len(restricted)!=len(ops) or len(initial)!=r or _iv(_apply(lift,initial))!=s:return False
        if any(_mul(a,lift,n,n,r)!=_mul(lift,b,n,r,r) for a,b in zip(ops,restricted)):return False
        o=_mat(receipt['observation_matrix'],k,r)
        expected=tuple(_iv(_apply(E.transpose(lift),_row_word(ops,h[i],w))) if r else () for i,w in machine['readout_words'])
        if o!=expected:return False
        if k:
            if not verify_smith(observation,**budgets) or _mat(observation['matrix'],k,r)!=o or observation['rank']!=k:return False
            v=_mat(observation['right'],r,r)
        else:
            if observation is not None:return False
            v=_mat(E.identity(r),r,r)
        quotient=_mat(receipt['quotient'],k,r);section=_mat(receipt['section'],r,k);kernel=_mat(receipt['invisible_kernel'],r,r-k)
        if section!=tuple(tuple(row[j] for j in range(k)) for row in v) or kernel!=tuple(tuple(row[j] for j in range(k,r)) for row in v):return False
        if _mul(quotient,v,k,r,r)!=tuple(tuple(int(i==j) for j in range(r)) for i in range(k)):return False
        compressed=tuple(_mat(a,k,k) for a in receipt['operators_minimal']);decoder=_mat(receipt['readouts_minimal'],m,k)
        if len(compressed)!=len(ops) or any(_mul(quotient,a,k,r,r)!=_mul(b,quotient,k,k,r) for a,b in zip(restricted,compressed)):return False
        if _mul(h,lift,m,n,r)!=_mul(decoder,quotient,m,k,r) or _iv(receipt['seed_minimal'])!=_iv(_apply(quotient,initial)):return False
        factors=observation['smith_factors'] if observation else []
        if receipt['observation_image_factors']!=factors:return False
        return type(receipt['selected_word_lattice_index']) is int and receipt['selected_word_lattice_index']==(prod(reach['smith_factors']) if reach else 1)
    except (ValueError,TypeError,KeyError,IndexError,ArithmeticError,OverflowError):return False


def integral_word_output(receipt,word,*,order='execution'):
    if not verify_integral_machine(receipt):raise ValueError('invalid integral machine')
    if order not in ('execution','written'):raise ValueError('invalid word order')
    word=tuple(word)
    if len(word)>4096:raise WorkLimit('word length exceeds budget')
    if order=='written':word=word[::-1]
    v=_word(receipt['operators_minimal'],receipt['seed_minimal'],word)
    return _iv(_apply(receipt['readouts_minimal'],v))


def integral_power_output(receipt,index,*,context=0):
    if not verify_integral_machine(receipt):raise ValueError('invalid integral machine')
    if type(index) is not int or not 0<=index<2**64:raise ValueError('nonnegative 64-bit index required')
    if type(context) is not int or not 0<=context<len(receipt['operators_minimal']):raise ValueError('invalid operator context')
    k=receipt['minimal_dimension'];a=receipt['operators_minimal'][context];v=receipt['seed_minimal']
    while index:
        if index&1:v=_iv(_apply(a,v))
        index//=2
        if index:a=_mul(a,a,k,k,k)
    return _iv(_apply(receipt['readouts_minimal'],v))


def project_state(receipt,state):
    """Project an integer state in the saturated rational reachable space."""
    if not verify_integral_machine(receipt):raise ValueError('invalid integral machine')
    state=_iv(state)
    if len(state)!=receipt['state_dimension']:raise ValueError('state dimension mismatch')
    restricted=_iv(_apply(receipt['reachable_coordinates'],state))
    if _iv(_apply(receipt['reachable_lift'],restricted))!=state:raise ValueError('state outside saturated reachable space')
    return _iv(_apply(receipt['quotient'],restricted))


def distinguish_states(receipt,left,right):
    """All-future equality, or an actual finite readout word separating states."""
    a=project_state(receipt,left);b=project_state(receipt,right)
    if a==b:return {'status':'ALL_FUTURE_EQUAL','execution_verified':False}
    difference=_iv(x-y for x,y in zip(_iv(left),_iv(right)))
    v=_iv(_apply(receipt['reachable_coordinates'],difference))
    observations=_iv(_apply(receipt['observation_matrix'],v))
    i=next(i for i,x in enumerate(observations) if x)
    readout,word=receipt['rational_certificate']['readout_words'][i]
    return {'status':'DISTINGUISHED_BY_WORD','readout':readout,'word':tuple(word),
        'difference':observations[i],'execution_verified':False}


def modular_power_output(receipt,index,modulus,*,context=0):
    """Exact output residues for every modulus, including denominator primes."""
    if not verify_integral_machine(receipt):raise ValueError('invalid integral machine')
    if type(index) is not int or not 0<=index<2**64 or type(modulus) is not int or not 2<=modulus<2**64:raise ValueError('64-bit nonnegative index and modulus at least two required')
    if type(context) is not int or not 0<=context<len(receipt['operators_minimal']):raise ValueError('invalid operator context')
    a=receipt['operators_minimal'][context];v=receipt['seed_minimal'];k=receipt['minimal_dimension']
    def mm(a,b):return tuple(tuple(sum(a[i][t]*b[t][j] for t in range(k))%modulus for j in range(k)) for i in range(k))
    while index:
        if index&1:v=tuple(x%modulus for x in _apply(a,v))
        index//=2
        if index:a=mm(a,a)
    return tuple(x%modulus for x in _apply(receipt['readouts_minimal'],v))


def observation_fibre(receipt,values):
    """All integer saturated-reachable states with supplied witness observations.

    Observations are the certificate's finite readout/word witnesses, not
    arbitrary samples and not a claim that these states lie on the seed orbit.
    """
    if not verify_integral_machine(receipt):raise ValueError('invalid integral machine')
    values=_iv(values);r=receipt['reachable_dimension'];k=receipt['minimal_dimension']
    if len(values)!=k:raise ValueError('one value for each witness observation required')
    if k:result=_solve_with_certificate(receipt['observation_smith'],values)
    else:result={'status':'INTEGER_AFFINE_FIBRE','particular':[0]*r,'kernel_basis':[list(map(int,row)) for row in E.identity(r)],
        'parameter_count':r,'parameter_domain':'Z','transformed_rhs':[],'complete':True}
    if result['status']=='INTEGER_AFFINE_FIBRE':
        result['original_particular']=_iv(_apply(receipt['reachable_lift'],result['particular']))
        result['original_kernel_basis']=tuple(_iv(_apply(receipt['reachable_lift'],v)) for v in result['kernel_basis'])
        result['quotient_state']=_iv(_apply(receipt['quotient'],result['particular']))
    return dict(result,execution_verified=False,scope='all integer states in the saturated reachable space with these finite witness observations; not seed-orbit membership')
