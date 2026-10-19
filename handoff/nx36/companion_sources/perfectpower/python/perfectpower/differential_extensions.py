"""Finite etale differential algebras, fixed algebras and scalar descent.

All extensions retain their defining polynomial. Squarefree is certified;
irreducibility is neither required nor silently assumed. Nonunits carry a
proper polynomial factor witness. The base is Q(t) or an existing parameter
tower; nested algebras allow tensor products without claiming a compositum.
"""
from copy import deepcopy
from fractions import Fraction as Q
from . import field_polynomials as F
from .rational_functions import RationalFunction as RF, AlgebraBudget, solve_many, determinant
from .parameter_functions import ParameterFunction
from .divisor_square import WorkLimit


def encode(value):
    return value.packet() if hasattr(value, 'packet') else str(value)


def matrix_encode(a):return [[encode(v) for v in row] for row in a]


def base_derivative(value, parameter=0):
    if isinstance(value, RF):
        if parameter not in (0, 't', 's'):raise ValueError('unknown single parameter')
        return value.derivative()
    return value.derivative(parameter)


def nullspace(rows, columns, zero):
    """Kernel over a genuine coefficient field, free variables in order."""
    a=[list(r) for r in rows];pivots=[]
    for c in range(columns):
        k=len(pivots);p=next((i for i in range(k,len(a)) if a[i][c]),None)
        if p is None:continue
        a[k],a[p]=a[p],a[k];v=a[k][c];a[k]=[x/v for x in a[k]]
        for i in range(len(a)):
            if i!=k and a[i][c]:
                v=a[i][c];a[i]=[x-v*y for x,y in zip(a[i],a[k])]
        pivots.append(c)
    out=[]
    for c in range(columns):
        if c in pivots:continue
        v=[zero]*columns;v[c]=zero.coerce(1)
        for i,p in enumerate(pivots):v[p]=-a[i][c]
        out.append(v)
    return out


class ExtensionNonUnit(ArithmeticError):
    def __init__(self,factor):
        self.factor=factor
        super().__init__('nonunit in finite etale algebra; split on factor '+str([encode(v) for v in factor]))


class EtaleAlgebra:
    def __init__(self,modulus,base=None,budget=None):
        self.budget=budget or getattr(base,'budget',None) or AlgebraBudget()
        self.base=RF([0],budget=self.budget) if base is None else base.coerce(0)
        self.modulus=F.trim([self.base.coerce(v) for v in modulus])
        if not 1<=len(self.modulus)-1<=32:raise ValueError('extension degree one through 32 required')
        leading=self.modulus[-1];self.modulus=[v/leading for v in self.modulus]
        common,_,_=F.extended_gcd(self.modulus,F.derivative(self.modulus))
        if len(common)!=1:raise ValueError('squarefree extension modulus required')
        self.degree=len(self.modulus)-1
        self.zero=self.element([0]);self.one=self.element([1]);self.generator=self.element([0,1])
        self._derivatives={}

    def element(self,coefficients):
        if isinstance(coefficients,EtaleElement):
            if coefficients.algebra is not self:raise ValueError('different extension algebras')
            return coefficients
        if not isinstance(coefficients,(list,tuple)):coefficients=[coefficients]
        return EtaleElement(self,coefficients)

    def basis(self):return [self.element([0]*j+[1]) for j in range(self.degree)]

    def generator_derivative(self,parameter=0):
        if parameter not in self._derivatives:
            numerator=self.element([base_derivative(v,parameter) for v in self.modulus])
            denominator=self.element(F.derivative(self.modulus))
            velocity=-numerator/denominator
            if numerator+denominator*velocity:raise AssertionError('extension derivative relation failed')
            self._derivatives[parameter]=velocity
        return self._derivatives[parameter]

    def automorphism(self,image):
        image=self.element(image)
        if F.evaluate([self.zero.coerce(v) for v in self.modulus],image):raise ValueError('generator image does not preserve modulus')
        columns=[(image**i).padded() for i in range(self.degree)]
        matrix=list(map(list,zip(*columns)))
        det=determinant(matrix)
        if not det:raise ValueError('generator image is not an algebra automorphism')
        # A nested coefficient algebra can be a product. Nonzero is then
        # weaker than invertible: certify the determinant is a unit.
        self.base.coerce(1)/det
        return image,matrix

    def group(self,images,limit=32):
        if type(limit) is not int or not 1<=limit<=64:raise ValueError('group limit one through 64 required')
        generators=[self.automorphism(v)[0] for v in images]
        elements=[self.generator]
        for current in elements:
            for g in generators:
                new=current.at(g)
                if new not in elements:
                    if len(elements)==limit:raise WorkLimit('automorphism closure exceeds group limit')
                    elements.append(new)
        matrices=[self.automorphism(v)[1] for v in elements]
        return elements,matrices

    def fixed_algebra(self,images,limit=32):
        group,matrices=self.group(images,limit);n=self.degree;z=self.base
        rows=[[v-z.coerce(int(i==j)) for j,v in enumerate(row)] for m in matrices for i,row in enumerate(m)]
        vectors=nullspace(rows,n,z);basis=[self.element(v) for v in vectors]
        columns=list(map(list,zip(*(v.padded() for v in basis))))
        products=[]
        for a in basis:
            row=[]
            for b in basis:
                answer=solve_many(columns,[[v] for v in (a*b).padded()])
                if answer is None:raise AssertionError('fixed algebra is not multiplicatively closed')
                row.append([v[0] for v in answer])
            products.append(row)
        return dict(schema='pp-fixed-etale-algebra/1',group_order=len(group),dimension=len(basis),
            group_images=[v.packet() for v in group],basis=[v.packet() for v in basis],
            multiplication_table=[[[encode(v) for v in p] for p in row] for row in products],
            closure_checked=True,scope='fixed subalgebra of this finite etale algebra, not necessarily a field')

    def hilbert90(self,image,element,candidate_limit=128):
        sigma,matrix=self.automorphism(image);a=self.element(element)
        a.inverse();group,_=self.group([image]);fixed=self.fixed_algebra([image])
        if len(group)!=self.degree or fixed['dimension']!=1:
            raise ValueError('scalar Hilbert 90 requires a cyclic Galois etale algebra: group order equals degree and fixed dimension is one')
        norm=self.one
        for g in group:norm=norm*a.at(g)
        if norm!=1:return dict(schema='pp-hilbert90/1',status='NORM_OBSTRUCTION',group_norm=norm.packet(),order=len(group))
        columns=[(a*v.at(sigma)-v).padded() for v in self.basis()]
        kernel=nullspace(list(map(list,zip(*columns))),self.degree,self.base)
        if type(candidate_limit) is not int or not 1<=candidate_limit<=256:raise ValueError('candidate limit one through 256 required')
        candidates=[self.element(v) for v in kernel]
        # A field needs one nonzero vector; a product can need a combination.
        for k in range(1,candidate_limit+1):
            candidates.append(sum((self.element(v)*(k**j) for j,v in enumerate(kernel)),self.zero))
        for count,b in enumerate(candidates[:candidate_limit],1):
            try:b.inverse()
            except (ExtensionNonUnit,ZeroDivisionError):continue
            if a!=b/b.at(sigma):raise AssertionError('Hilbert 90 replay failed')
            return dict(schema='pp-hilbert90/1',status='DESCENDED_SCALAR',order=len(group),
                element=a.packet(),witness=b.packet(),sigma_witness=b.at(sigma).packet(),
                identity='a=b/sigma(b)',identity_checked=True,candidates_tested=count,
                scope='scalar multiplicative cocycle only; projective-coordinate descent and twists need separate analysis')
        return dict(schema='pp-hilbert90/1',status='UNIT_SEARCH_BUDGET',order=len(group),candidates_tested=candidate_limit)


class EtaleElement:
    def __init__(self,algebra,coefficients):
        self.algebra=algebra;self.budget=algebra.budget
        values=[algebra.base.coerce(v) for v in coefficients]
        if not values:values=[algebra.base]
        self.coefficients=F.divide(F.trim(values),algebra.modulus)[1]
        self.budget.work+=len(values)+len(self.coefficients)
        if self.budget.work>self.budget.work_limit:raise WorkLimit('differential extension work budget')
    def coerce(self,value):
        if isinstance(value,EtaleElement) and value.algebra is self.algebra:return value
        return self.algebra.element([self.algebra.base.coerce(value)])
    def _accepts_scalar(self,value):
        if isinstance(value,EtaleElement) and value.algebra is self.algebra:return False
        try:self.algebra.base.coerce(value);return True
        except (ValueError,TypeError):return False
    def padded(self):return self.coefficients+[self.algebra.base]*(self.algebra.degree-len(self.coefficients))
    def __bool__(self):return any(self.coefficients)
    def __eq__(self,value):
        if isinstance(value,EtaleElement) and value._accepts_scalar(self):return NotImplemented
        return self.coefficients==self.coerce(value).coefficients
    def __neg__(self):return self.algebra.element([-v for v in self.coefficients])
    def __add__(self,value):
        if isinstance(value,EtaleElement) and value._accepts_scalar(self):return NotImplemented
        return self.algebra.element(F.add(self.coefficients,self.coerce(value).coefficients))
    __radd__=__add__
    def __sub__(self,value):
        if isinstance(value,EtaleElement) and value._accepts_scalar(self):return NotImplemented
        return self+-self.coerce(value)
    def __rsub__(self,value):return self.coerce(value)+-self
    def __mul__(self,value):
        if isinstance(value,EtaleElement) and value._accepts_scalar(self):return NotImplemented
        return self.algebra.element(F.product(self.coefficients,self.coerce(value).coefficients))
    __rmul__=__mul__
    def inverse(self):
        if not self:raise ZeroDivisionError('zero algebra element')
        common,u,_=F.extended_gcd(self.coefficients,self.algebra.modulus)
        if len(common)!=1:raise ExtensionNonUnit(common)
        return self.algebra.element(u)/common[0] if common[0]!=1 else self.algebra.element(u)
    def __truediv__(self,value):
        if isinstance(value,EtaleElement) and value._accepts_scalar(self):return NotImplemented
        other=self.coerce(value)
        if len(other.coefficients)==1:
            if not other:raise ZeroDivisionError('zero algebra element')
            return self.algebra.element([v/other.coefficients[0] for v in self.coefficients])
        return self*other.inverse()
    def __rtruediv__(self,value):return self.coerce(value)/self
    def __pow__(self,n):
        if type(n) is not int or not -256<=n<=256:raise ValueError('extension exponent between -256 and 256 required')
        if n<0:return self.inverse()**(-n)
        out=self.coerce(1);v=self
        while n:
            if n&1:out=out*v
            n//=2
            if n:v=v*v
        return out
    def at(self,image):
        out=self.coerce(0);image=self.coerce(image)
        for c in reversed(self.coefficients):out=out*image+self.coerce(c)
        return out
    def derivative(self,parameter=0):
        velocity=self.algebra.generator_derivative(parameter)
        return self.algebra.element([base_derivative(v,parameter) for v in self.coefficients])+self.algebra.element(F.derivative(self.coefficients))*velocity
    def matrix(self):return list(map(list,zip(*((self*b).padded() for b in self.algebra.basis()))))
    def trace(self):return sum((row[i] for i,row in enumerate(self.matrix())),self.algebra.base)
    def characteristic_polynomial(self):
        a=self.matrix();n=len(a);z=self.algebra.base
        b=[[z.coerce(int(i==j)) for j in range(n)] for i in range(n)];coeff=[z.coerce(1)]
        for k in range(1,n+1):
            ab=F.matrix_product(a,b);c=-sum((ab[i][i] for i in range(n)),z)/k;coeff.append(c)
            b=[[ab[i][j]+(c if i==j else z) for j in range(n)] for i in range(n)]
        return list(reversed(coeff))
    def norm(self):return (-1)**self.algebra.degree*self.characteristic_polynomial()[0]
    def minimal_polynomial(self):
        columns=[];v=self.coerce(1)
        for k in range(self.algebra.degree+1):
            if columns:
                sol=solve_many(list(map(list,zip(*columns))),[[c] for c in v.padded()])
                if sol is not None:return [-row[0] for row in sol]+[self.algebra.base.coerce(1)]
            columns.append(v.padded());v=v*self
        raise AssertionError('finite algebra did not satisfy Cayley-Hamilton')
    def packet(self):return [encode(v) for v in self.coefficients]
    def evidence(self,parameters=(0,)):
        norm=self.norm();trace=self.trace();derivatives=[]
        for p in parameters:
            da=self.derivative(p);trace_ok=base_derivative(trace,p)==da.trace();norm_ok=None
            if norm:norm_ok=base_derivative(norm,p)/norm==(da/self).trace()
            if not trace_ok or norm_ok is False:raise AssertionError('trace/norm differential identity failed')
            derivatives.append(dict(parameter=p,value=da.packet(),trace_identity_checked=trace_ok,norm_log_identity_checked=norm_ok))
        minimum=self.minimal_polynomial()
        return dict(element=self.packet(),trace=encode(trace),norm=encode(norm),
            characteristic_polynomial=[encode(v) for v in self.characteristic_polynomial()],
            minimal_polynomial=[encode(v) for v in minimum],primitive=len(minimum)-1==self.algebra.degree,
            derivatives=derivatives)


class DifferentialExtension:
    """Persistent public object over one to three named parameter fields."""
    def __init__(self,specification):
        allowed={'parameters','modulus','work_limit','degree_limit','bit_limit'}
        if not isinstance(specification,dict) or 'modulus' not in specification or set(specification)-allowed:raise ValueError('extension modulus, parameters and optional budgets required')
        self.specification=deepcopy(specification);self.parameters=specification.get('parameters',['t'])
        if not isinstance(self.parameters,list) or not 1<=len(self.parameters)<=3 or len(set(self.parameters))!=len(self.parameters) or any(not isinstance(p,str) or not p.isidentifier() for p in self.parameters):raise ValueError('one through three distinct parameter names required')
        self.limits={k:specification[k] for k in ('work_limit','degree_limit','bit_limit') if k in specification}
        budget=AlgebraBudget(**self.limits);self.base=ParameterFunction(self.parameters,budget=budget)
        raw=specification['modulus']
        if not isinstance(raw,list) or not 2<=len(raw)<=33:raise ValueError('bounded extension modulus array required')
        self.algebra=EtaleAlgebra([ParameterFunction.parse(self.parameters,v,budget) for v in raw],self.base,budget)
    def _read(self,value):
        if not isinstance(value,list) or not 1<=len(value)<=33:raise ValueError('bounded extension element coefficient array required')
        return self.algebra.element([ParameterFunction.parse(self.parameters,v,self.algebra.budget) for v in value])
    def summary(self):return dict(degree=self.algebra.degree,parameters=self.parameters,squarefree=True,irreducibility_assumed=False)
    def evidence(self):
        a=self.algebra;z=a.generator;velocities=[z.derivative(i) for i in range(len(self.parameters))]
        mixed=[dict(parameters=[self.parameters[i],self.parameters[j]],commute=velocities[i].derivative(j)==velocities[j].derivative(i)) for i in range(len(self.parameters)) for j in range(i+1,len(self.parameters))]
        if any(not v['commute'] for v in mixed):raise AssertionError('extended parameter derivations do not commute')
        return dict(schema='pp-differential-extension/1',**self.summary(),modulus=[encode(v) for v in a.modulus],
            generator_derivatives=[v.packet() for v in velocities],mixed_derivatives=mixed,
            generator_evidence=z.evidence(range(len(self.parameters))),
            scope='finite etale differential algebra over Q(parameters); components may be fields or products; no numerical embeddings or radical formulas required')
    def element_data(self,coefficients):return self._read(coefficients).evidence(range(len(self.parameters)))
    def fixed_algebra(self,images,limit=32):return self.algebra.fixed_algebra([self._read(v) for v in images],limit)
    def hilbert90(self,image,element,candidate_limit=128):return self.algebra.hilbert90(self._read(image),self._read(element),candidate_limit)


def tensor_primitive(left,right,candidate_limit=32):
    """Tensor two etale algebras and return an exact single-generator model.

    This preserves every tensor component; it does not choose an embedding or
    identify a field compositum. Primitive witnesses are searched and replayed.
    """
    if left.degree*right.degree>16:raise WorkLimit('tensor degree exceeds 16')
    if type(candidate_limit) is not int or not 1<=candidate_limit<=64:raise ValueError('primitive candidate limit one through 64 required')
    if isinstance(left.base,EtaleElement) or isinstance(right.base,EtaleElement):raise ValueError('two unnested algebras with a common coefficient field required')
    if type(left.base)!=type(right.base) or (isinstance(left.base,ParameterFunction) and left.base.parameters!=right.base.parameters):raise ValueError('tensor coefficient fields must agree')
    nested=EtaleAlgebra([left.element([v]) for v in right.modulus],left.zero,left.budget)
    a=nested.zero.coerce(left.generator);b=nested.generator;n=left.degree*right.degree
    flatten=lambda v:[c for coefficient in v.padded() for c in coefficient.padded()]
    for c in range(1,candidate_limit+1):
        gamma=a+c*b;columns=[flatten(gamma**j) for j in range(n)]
        matrix=list(map(list,zip(*columns)))
        if not determinant(matrix):continue
        rhs=[flatten(gamma**n),flatten(a),flatten(b)]
        answer=solve_many(matrix,list(map(list,zip(*rhs))))
        polynomial=[-v[0] for v in answer]+[left.base.coerce(1)]
        target=EtaleAlgebra(polynomial,left.base,left.budget);g=target.generator
        images=[target.element([v[k] for v in answer]) for k in (1,2)]
        if F.evaluate([target.zero.coerce(v) for v in left.modulus],images[0]) or F.evaluate([target.zero.coerce(v) for v in right.modulus],images[1]) or images[0]+c*images[1]!=g:raise AssertionError('tensor primitive map replay failed')
        return dict(schema='pp-etale-tensor-primitive/1',degree=n,combination_coefficient=c,
            modulus=[encode(v) for v in polynomial],left_generator=images[0].packet(),right_generator=images[1].packet(),
            change_of_basis=matrix_encode(matrix),identity_checked=True,
            scope='isomorphism of the full tensor algebra; no choice of field compositum or irreducibility assertion')
    return dict(schema='pp-etale-tensor-primitive/1',status='CANDIDATE_BUDGET',degree=n)
