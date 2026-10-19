"""Construct quotient fields and de Rham projectors from finite curve actions.

Möbius transformations are verified on the binary branch form and lifted to y.
The fixed x field is certified by invariant-map degree, then an invariant y
coordinate is constructed by orbit traces. Rational reconstruction and square
removal produce the quotient equation. Differential pullbacks are independently
reduced and compared with the quotient connection and group-average projector.
"""
from copy import deepcopy
from fractions import Fraction as Q
from . import field_polynomials as F
from .rational_functions import RationalFunction as RF, AlgebraBudget, solve_many
from .differential_extensions import EtaleAlgebra, EtaleElement, encode, matrix_encode, nullspace
from .parameter_functions import ParameterFunction
from .algebraic_local_curves import characteristic, squarefree_layers
from .divisor_square import WorkLimit


class XFunction:
    """Reduced rational functions of x over the recorded coefficient algebra."""
    def __init__(self,numerator,denominator=None):
        n=F.trim(numerator);z=n[0].coerce(0);d=F.trim(denominator or [z.coerce(1)])
        if not any(d):raise ValueError('nonzero x-function denominator required')
        if not any(n):n,d=[z],[z.coerce(1)]
        else:
            common=F.extended_gcd(n,d)[0];n=F.divide(n,common)[0];d=F.divide(d,common)[0]
            c=d[-1];n,d=F.scale(n,1/c),F.scale(d,1/c)
        self.n,self.d=n,d;self.zero=z;self.budget=z.budget
        if max(len(n),len(d))>129:raise WorkLimit('x-function degree exceeds 128')
    def coerce(self,v):return v if isinstance(v,XFunction) else XFunction([self.zero.coerce(v)])
    def __bool__(self):return any(self.n)
    def __eq__(self,v):
        v=self.coerce(v);return self.n==v.n and self.d==v.d
    def __neg__(self):return XFunction(F.scale(self.n,-1),self.d)
    def __add__(self,v):
        v=self.coerce(v);return XFunction(F.add(F.product(self.n,v.d),F.product(v.n,self.d)),F.product(self.d,v.d))
    __radd__=__add__
    def __sub__(self,v):return self+-self.coerce(v)
    def __mul__(self,v):
        v=self.coerce(v);return XFunction(F.product(self.n,v.n),F.product(self.d,v.d))
    __rmul__=__mul__
    def __truediv__(self,v):
        v=self.coerce(v)
        if not v:raise ZeroDivisionError('zero x function')
        return XFunction(F.product(self.n,v.d),F.product(self.d,v.n))
    def __rtruediv__(self,v):return self.coerce(v)/self
    def __pow__(self,k):
        if type(k) is not int or not -64<=k<=64:raise ValueError('x-function exponent between -64 and 64 required')
        if k<0:return XFunction(self.d,self.n)**(-k)
        out=self.coerce(1);v=self
        while k:
            if k&1:out=out*v
            k//=2
            if k:v=v*v
        return out
    def at(self,x):
        def horner(p):
            out=x.coerce(0)
            for c in reversed(p):out=out*x+c
            return out
        return horner(self.n)/horner(self.d)
    def dx(self):return XFunction(F.add(F.product(F.derivative(self.n),self.d),F.scale(F.product(self.n,F.derivative(self.d)),-1)),F.product(self.d,self.d))
    def dt(self):return XFunction(F.add(F.product([v.derivative() for v in self.n],self.d),F.scale(F.product(self.n,[v.derivative() for v in self.d]),-1)),F.product(self.d,self.d))
    def degree(self):return max(len(self.n),len(self.d))-1
    def packet(self):return dict(numerator=[encode(v) for v in self.n],denominator=[encode(v) for v in self.d])


def series_inverse_sqrt(w,length):
    z=w[0].coerce(0);w=w+[z]*max(0,length+1-len(w));out=[z.coerce(1)]
    for k in range(1,length+1):out.append(-sum(((k-j+Q(j,2))*w[j]*out[k-j] for j in range(1,k+1)),z)/k)
    return out


class PolynomialCurve:
    """Independent de Rham reduction for odd and even models of degrees 3..8."""
    def __init__(self,f,budget):
        self.f=F.trim(f);self.budget=budget;m=len(self.f)-1
        if not 3<=m<=8:raise ValueError('de Rham polynomial degree three through eight required')
        self.genus=(m-1)//2;self.dimension=2*self.genus;z=self.f[0].coerce(0)
        self.zero=z;self.one=z.coerce(1)
        if len(F.extended_gcd(self.f,F.derivative(self.f))[0])!=1:raise ValueError('generically smooth polynomial curve required')
        self.basis=[]
        if m%2:
            self.basis=[[z]*i+[self.one] for i in range(self.dimension)]
        else:
            w=[a/self.f[-1] for a in reversed(self.f)];b=series_inverse_sqrt(w,self.genus)
            for i in range(2*self.genus+1):
                if i==self.genus:continue
                q=[z]*i+[self.one]
                if i>self.genus:q[self.genus]=-b[i-self.genus]
                self.basis.append(q)
        size=2*m-1;pad=lambda a:a+[z]*(size-len(a));columns=[pad(F.product(q,self.f)) for q in self.basis]
        for k in range(m):
            r=[z]*k+[self.one]
            columns.append(pad(F.add(F.product(F.derivative(r),self.f),F.scale(F.product(r,F.derivative(self.f)),-Q(1,2)))))
        dt=[a.derivative() for a in self.f];targets=[]
        for q in self.basis:
            targets.append(pad(F.add(F.product([a.derivative() for a in q],self.f),F.scale(F.product(q,dt),-Q(1,2)))))
        solution=solve_many(list(map(list,zip(*columns))),list(map(list,zip(*targets))))
        if solution is None:raise AssertionError('residue-free polynomial de Rham reduction failed')
        self.connection=list(map(list,zip(*solution[:self.dimension])))
        self.reductions=list(map(list,zip(*solution[self.dimension:])))
        for i,target in enumerate(targets):
            replay=[z]
            for c,column in zip([v[i] for v in solution],columns):replay=F.add(replay,F.scale(column,c))
            if pad(replay)!=target:raise AssertionError('independent polynomial connection replay failed')

    def reduce_form(self,h):
        """Find h dx/y = sum c_i omega_i + d(R/y), retaining exact R."""
        f=self.f;z=self.zero;d=h.d
        for i,q in enumerate(self.basis):
            if h==XFunction(q):return [z.coerce(int(i==j)) for j in range(self.dimension)],XFunction([z])
        # Differentiation raises finite pole order by one. A branch point can
        # also acquire a simple pole from P_x/P, so gcd(d,d_x) is sufficient
        # for the primitive denominator; avoid redundant pole coordinates.
        rd=F.extended_gcd(d,F.derivative(d))[0];rd2=F.product(rd,rd)
        target=F.product(F.product(h.n,f),rd2)
        columns=[F.product(F.product(F.product(q,f),rd2),d) for q in self.basis]
        bound=max(len(f)-1,len(h.n)-len(d)+2)+len(rd)-1
        if bound>64:raise WorkLimit('rational differential reduction exceeds degree bound')
        for k in range(bound):
            r=[z]*k+[self.one]
            numerator=F.add(F.product(F.derivative(r),rd),F.scale(F.product(r,F.derivative(rd)),-1))
            columns.append(F.add(F.product(F.product(numerator,f),d),F.scale(F.product(F.product(F.product(r,rd),d),F.derivative(f)),-Q(1,2))))
        length=max(len(target),*(len(c) for c in columns));pad=lambda p:p+[z]*(length-len(p))
        answer=solve_many(list(map(list,zip(*(pad(c) for c in columns)))),[[v] for v in pad(target)])
        if answer is None:raise ValueError('rational form has no supported residue-free de Rham reduction')
        coordinates=[v[0] for v in answer[:self.dimension]];r=[v[0] for v in answer[self.dimension:]]
        replay=[z]
        for c,q in zip(coordinates,self.basis):replay=F.add(replay,F.scale(q,c))
        R=XFunction(r,rd);P=XFunction(f)
        if h!=XFunction(replay)+R.dx()-R*P.dx()/(2*P):raise AssertionError('rational differential reduction replay failed')
        return coordinates,R

    def pairing(self):
        m=len(self.f)-1;g=self.genus;odd=m%2;step=2 if odd else 1
        w=[self.one]+[self.zero]*(4*g+8)
        for i,a in enumerate(self.f[:-1]):
            k=step*(m-i)
            if k<len(w):w[k]=a/self.f[-1]
        b=series_inverse_sqrt(w,len(w)-1);forms=[]
        for q in self.basis:
            terms={}
            for i,c in enumerate(q):
                for k,v in enumerate(b):
                    exponent=(m-3-2*i if odd else g-1-i)+k
                    terms[exponent]=terms.get(exponent,self.zero)-step*c*v
            forms.append({k:v for k,v in terms.items() if v})
        j=[[sum((c*right.get(-2-k,self.zero)/(k+1) for k,c in left.items() if k!=-1),self.zero)*(1 if odd else 2)/self.f[-1] for right in forms] for left in forms]
        if F.matrix_rank(j)!=self.dimension or any(j[i][k]!=-j[k][i] for i in range(self.dimension) for k in range(self.dimension)):raise AssertionError('curve pairing failed')
        aj=F.matrix_product(self.connection,j);jat=F.matrix_product(j,list(map(list,zip(*self.connection))))
        if any(j[i][k].derivative()!=aj[i][k]+jat[i][k] for i in range(self.dimension) for k in range(self.dimension)):raise AssertionError('curve pairing is not horizontal')
        return j

    def evidence(self):return dict(genus=self.genus,state_dimension=self.dimension,polynomial=[encode(v) for v in self.f],
        basis_polynomials=[[encode(v) for v in q] for q in self.basis],connection=matrix_encode(self.connection),
        exact_derivative_numerators=matrix_encode(self.reductions),reduction_identities_checked=self.dimension)

    def observable(self,coefficients=None):
        row=[self.one]+[self.zero]*(self.dimension-1) if coefficients is None else coefficients
        if len(row)!=self.dimension:raise ValueError('one observable coefficient per de Rham basis vector required')
        rows=[]
        while True:
            decoder=solve_many(list(map(list,zip(*rows))),[[v] for v in row]) if rows else ([] if not any(row) else None)
            if decoder is not None:break
            if len(rows)==self.dimension:raise AssertionError('observable derivative span failed to close')
            rows.append(row)
            row=[v.derivative()+sum((rows[-1][k]*self.connection[k][j] for k in range(self.dimension)),self.zero) for j,v in enumerate(rows[-1])]
        operator=[-v[0] for v in decoder]+[self.one]
        replay=[sum((operator[i]*rows[i][j] for i in range(len(rows))),self.zero)+row[j] for j in range(self.dimension)]
        if any(replay):raise AssertionError('quotient observable operator replay failed')
        packet=dict(schema='pp-symmetry-curve-observable/1',order=len(rows),monic_operator=[encode(v) for v in operator],
            derivative_rows=matrix_encode(rows),operator_identity_checked=True,
            scope='minimum universal differential order for the supplied observable on this de Rham module, not every marked period')
        if isinstance(self.zero,RF):
            from .curve_families import primitive_operator
            packet['polynomial_operator']=primitive_operator(operator,self.budget)
        return packet


def _compose_action(left,right):
    x,h=left;u,k=right
    return x.at(u),h.at(u)*k


class SymmetryCurve:
    def __init__(self,specification):
        allowed={'coefficients','generators','coefficient_extension','group_limit','work_limit','degree_limit','bit_limit'}
        if not isinstance(specification,dict) or 'coefficients' not in specification or set(specification)-allowed:raise ValueError('polynomial coefficients, optional generators and budgets required')
        self.specification=deepcopy(specification);limits={k:specification[k] for k in ('work_limit','degree_limit','bit_limit') if k in specification}
        self.budget=AlgebraBudget(**limits);base=RF([0],budget=self.budget);self.extension=None
        if 'coefficient_extension' in specification:
            raw=specification['coefficient_extension']
            if not isinstance(raw,list):raise ValueError('coefficient extension modulus array required')
            self.extension=EtaleAlgebra([RF.parse(v,self.budget) for v in raw],base,self.budget);base=self.extension.zero
        self.zero=base;self.one=base.coerce(1)
        def read(v):
            if isinstance(v,dict) and set(v)=={'algebra_coefficients'}:
                if self.extension is None:raise ValueError('coefficient extension required')
                coefficients=v['algebra_coefficients']
                if not isinstance(coefficients,list) or not 1<=len(coefficients)<=33:raise ValueError('bounded algebra coefficient array required')
                return self.extension.element([RF.parse(c,self.budget) for c in coefficients])
            return base.coerce(RF.parse(v,self.budget))
        self.read=read;raw=specification['coefficients']
        if not isinstance(raw,list) or not 4<=len(raw)<=9:raise ValueError('polynomial degree three through eight required')
        self.f=F.trim([read(v) for v in raw]);self.curve=PolynomialCurve(self.f,self.budget)
        self.x=XFunction([base,self.one]);self.P=XFunction(self.f)
        generators=specification.get('generators',[])
        if not isinstance(generators,list) or len(generators)>8:raise ValueError('at most eight action generators required')
        self.generators=[]
        for raw in generators:
            if not isinstance(raw,dict) or set(raw)-{'matrix','y_scale'} or 'matrix' not in raw:raise ValueError('Möbius matrix and y_scale required')
            matrix=raw['matrix']
            if not isinstance(matrix,list) or len(matrix)!=2 or any(not isinstance(row,list) or len(row)!=2 for row in matrix):raise ValueError('two by two Möbius matrix required')
            a,b,c,d=[read(v) for row in matrix for v in row]
            if not a*d-b*c:raise ValueError('singular Möbius matrix')
            numerator=XFunction([b,a]);denominator=XFunction([d,c]);u=numerator/denominator
            scale=read(raw.get('y_scale',1));h=XFunction([scale])/denominator**(self.curve.genus+1)
            if not scale or self.P.at(u)!=self.P*h*h:raise ValueError('action does not preserve the curve equation')
            self.generators.append((u,h))
        limit=specification.get('group_limit',16)
        if type(limit) is not int or not 1<=limit<=32:raise ValueError('curve group limit one through 32 required')
        self.group=[(self.x,XFunction([self.one]))]
        for current in self.group:
            for generator in self.generators:
                new=_compose_action(current,generator)
                if new not in self.group:
                    if len(self.group)==limit:raise WorkLimit('curve action closure exceeds group limit')
                    self.group.append(new)
        self._projectors=None;self._quotients={}

    def summary(self):return dict(genus=self.curve.genus,state_dimension=self.curve.dimension,group_order=len(self.group),
        x_group_order=len(self._x_group()),coefficient_extension_degree=self.extension.degree if self.extension else 1)

    def _x_group(self):
        out=[]
        for u,h in self.group:
            if u not in out:out.append(u)
        return out

    def evidence(self):return dict(schema='pp-curve-symmetry/1',**self.summary(),curve=self.curve.evidence(),
        actions=[dict(x=u.packet(),y_over_y=h.packet()) for u,h in self.group],
        equation_identities_checked=len(self.group),finite_group_closed=True,
        scope='complete closure of the supplied verified generators, not a classification of all automorphisms')

    def projectors(self):
        if self._projectors is not None:return deepcopy(self._projectors)
        n=self.curve.dimension;z=self.zero;matrices=[];exact_terms=[]
        for u,h in self.group:
            rows=[];terms=[]
            for q in self.curve.basis:
                form=XFunction(q).at(u)*u.dx()/h
                row,R=self.curve.reduce_form(form);rows.append(row);terms.append(R.packet())
            matrices.append(rows);exact_terms.append(terms)
        p=[[sum((a[i][j] for a in matrices),z)/len(matrices) for j in range(n)] for i in range(n)]
        a=self.curve.connection;j=self.curve.pairing();pa=F.matrix_product(p,a);ap=F.matrix_product(a,p)
        pp=F.matrix_product(p,p);pj=F.matrix_product(p,j);jpt=F.matrix_product(j,list(map(list,zip(*p))))
        horizontal=not any(p[i][k].derivative()+pa[i][k]-ap[i][k] for i in range(n) for k in range(n))
        if pp!=p or not horizontal or pj!=jpt:raise AssertionError('geometric group projector identities failed')
        for matrix in matrices:
            if F.matrix_product(matrix,p)!=p or F.matrix_product(p,matrix)!=p:raise AssertionError('group average is not invariant')
        self._projectors=dict(schema='pp-geometric-group-projector/1',rank=F.matrix_rank(p),matrix=matrix_encode(p),
            complement=matrix_encode([[z.coerce(int(i==k))-p[i][k] for k in range(n)] for i in range(n)]),
            action_matrices=[matrix_encode(v) for v in matrices],exact_pullback_terms=exact_terms,
            idempotent=True,horizontal=True,polarization_self_adjoint=True,
            holomorphic_filtration_preserved=not any(p[i][k] for i in range(self.curve.genus) for k in range(self.curve.genus,n)),
            pairing=matrix_encode(j),geometric_origin='average of actual verified curve automorphisms',
            scope='geometric invariant de Rham sector of the supplied finite action; no marked integral matrix or full Jacobian factorization computed')
        return deepcopy(self._projectors)

    def quotient(self,reconstruction_degree=8):
        if type(reconstruction_degree) is not int or not 1<=reconstruction_degree<=12:raise ValueError('rational reconstruction degree one through twelve required')
        if reconstruction_degree in self._quotients:return deepcopy(self._quotients[reconstruction_degree])
        orbit=self._x_group();size=len(orbit);z=self.zero
        # A nonconstant orbit trace can already have the full map degree.
        candidates=[sum(orbit,XFunction([z]))]
        generator=None
        for u in candidates:
            if u.degree()==size and all(u.at(v)==u for v in orbit):generator=u;break
        if generator is None:
            for c in range(size*size+1):
                u=XFunction([self.one])
                for v in orbit:u=u*(v-c)
                if u.degree()==size and all(u.at(v)==u for v in orbit):generator=u;break
        if generator is None:raise WorkLimit('no full-degree invariant coordinate within orbit norm search')
        u=generator;projector=self.projectors()
        packet=dict(schema='pp-symmetry-curve-quotient/1',u=u.packet(),map_degree=len(self.group),x_map_degree=size,
            fixed_x_field_certified=True,invariance_checked=True,source_genus=self.curve.genus,projector=projector,
            coordinate_certificate='u is invariant and deg(u)=order of the faithful x action, hence K(x)^H=K(u)')
        if len(self.group)>size:
            if projector['rank']!=0:raise AssertionError('sheet involution quotient has nonzero H1')
            packet=dict(packet,target_genus=0,target_equation='projective line with coordinate u',
                scope='full group contains the hyperelliptic involution; fixed curve field is K(u)')
            self._quotients[reconstruction_degree]=deepcopy(packet);return packet
        v=None
        for k in range(size):
            multiplier=sum((h*x**k for x,h in self.group),XFunction([z]))
            if multiplier:v=multiplier;break
        if v is None:raise AssertionError('faithful group has no invariant anti-sheet trace')
        if any(v.at(x)*h!=v for x,h in self.group):raise AssertionError('quotient y trace is not invariant')
        square=self.P*v*v;numerator,denominator=self._reconstruct(square,u,reconstruction_degree)
        ln,ld=numerator[-1],denominator[-1]
        ns=F.scale(numerator,1/ln);ds=F.scale(denominator,1/ld)
        nodd,dodd,sn,sd=[self.one],[self.one],[self.one],[self.one]
        for multiplicity,factor in squarefree_layers(ns):
            sn=F.product(sn,F.power(factor,multiplicity//2))
            if multiplicity%2:nodd=F.product(nodd,factor)
        for multiplicity,factor in squarefree_layers(ds):
            sd=F.product(sd,F.power(factor,multiplicity//2))
            if multiplicity%2:dodd=F.product(dodd,factor)
        q=F.scale(F.product(nodd,dodd),ln/ld)
        normalized_v=v*XFunction(F.product(sd,dodd)).at(u)/XFunction(sn).at(u)
        if self.P*normalized_v*normalized_v!=XFunction(q).at(u):raise AssertionError('normalized quotient equation failed')
        genus=(len(q)-2)//2
        if genus<0:genus=0
        packet.update(v_over_y=normalized_v.packet(),raw_v_over_y=v.packet(),raw_square_in_u=dict(numerator=[encode(a) for a in numerator],denominator=[encode(a) for a in denominator]),
            target_coefficients=[encode(a) for a in q],target_genus=genus,equation_identity_checked=True,
            square_factors_removed=dict(numerator=[encode(a) for a in sn],denominator=[encode(a) for a in sd]),
            fixed_curve_field_certified=True,scope='quotient of the complete supplied action; invariant x and y generators, exact function-field degree and normalized curve equation')
        if projector['rank']!=2*genus:raise AssertionError('geometric projector rank disagrees with quotient genus')
        if genus:
            target=PolynomialCurve(q,self.budget);pullback=[];exact=[]
            for basis in target.basis:
                row,R=self.curve.reduce_form(XFunction(basis).at(u)*u.dx()/normalized_v);pullback.append(row);exact.append(R.packet())
            if F.matrix_rank(pullback)!=2*genus:raise AssertionError('quotient pullbacks are not independent')
            ta=F.matrix_product(pullback,self.curve.connection);bt=F.matrix_product(target.connection,pullback)
            if any(pullback[i][j].derivative()+ta[i][j]-bt[i][j] for i in range(2*genus) for j in range(self.curve.dimension)):raise AssertionError('quotient connection does not intertwine')
            p=[[self.read(a) for a in row] for row in projector['matrix']] if not self.extension else None
            # Reuse computed action average directly when coefficient packets
            # are algebra elements; never reinterpret them as rational scalars.
            if p is None:
                p=[[self.extension.element([RF.parse(v,self.budget) for v in a]) for a in row] for row in projector['matrix']]
            if F.matrix_product(pullback,p)!=pullback:raise AssertionError('pullbacks not in the invariant sector')
            packet.update(target_de_rham=target.evidence(),pullback_matrix=matrix_encode(pullback),
                pullback_exact_terms=exact,connection_intertwining_checked=True,
                pullback_image_equals_projector_image=True)
        self._quotients[reconstruction_degree]=deepcopy(packet);return packet

    def observable(self,sector='source',coefficients=None):
        if sector not in ('source','quotient'):raise ValueError('observable sector source or quotient required')
        curve=self.curve
        if sector=='quotient':
            packet=self.quotient()
            if not packet['target_genus']:raise ValueError('genus-zero quotient has no first de Rham cohomology')
            f=[self.extension.element([RF.parse(c,self.budget) for c in v]) if self.extension else RF.parse(v,self.budget) for v in packet['target_coefficients']]
            curve=PolynomialCurve(f,self.budget)
        if coefficients is not None:
            if not isinstance(coefficients,list):raise ValueError('observable coefficient array required')
            coefficients=[self.read(v) for v in coefficients]
        return dict(sector=sector,**curve.observable(coefficients))

    def involution_decomposition(self):
        """Actual paired covers and their induced Jacobian isogeny.

        For sigma and iota*sigma the norm/pullback compositions are [2].
        With canonical principal polarizations the maps are dual, hence both
        have degree 2^g. Integral kernel generators are not calculated here.
        """
        if len(self.generators)!=1 or len(self.group)!=2 or len(self._x_group())!=2:
            raise ValueError('one non-hyperelliptic involution generator required')
        specification=deepcopy(self.specification);generator=specification['generators'][0]
        scale=self.read(generator.get('y_scale',1))
        generator['y_scale']={'algebra_coefficients':[(-RF.parse(v)).packet() for v in scale.packet()]} if self.extension else (-scale).packet()
        other=SymmetryCurve(specification);plus=self.quotient();minus=other.quotient()
        n=self.curve.dimension;z=self.zero
        decode=lambda packet:[[self.extension.element([RF.parse(c,self.budget) for c in v]) if self.extension else RF.parse(v,self.budget) for v in row] for row in packet]
        p=decode(plus['projector']['matrix']);q=decode(minus['projector']['matrix'])
        identity=[[z.coerce(int(i==j)) for j in range(n)] for i in range(n)]
        if [[a+b for a,b in zip(r,s)] for r,s in zip(p,q)]!=identity or any(v for row in F.matrix_product(p,q) for v in row):raise AssertionError('paired geometric projectors are not complementary')
        maps=[v for v in (plus,minus) if v['target_genus']]
        rows=[row for v in maps for row in decode(v['pullback_matrix'])]
        holomorphic=[row for v in maps for row in decode(v['pullback_matrix'])[:v['target_genus']]]
        if sum(v['target_genus'] for v in maps)!=self.curve.genus or F.matrix_rank(rows)!=n or F.matrix_rank(holomorphic)!=self.curve.genus:raise AssertionError('quotient differentials do not span the Jacobian tangent space')
        cup=self.curve.pairing()
        for i,left in enumerate(maps):
            for right in maps[i+1:]:
                cross=F.matrix_product(F.matrix_product(decode(left['pullback_matrix']),cup),list(map(list,zip(*decode(right['pullback_matrix'])))))
                if any(v for row in cross for v in row):raise AssertionError('paired quotient sectors are not orthogonal')
        return dict(schema='pp-involution-jacobian-isogeny/1',source_genus=self.curve.genus,
            quotient_genera=[v['target_genus'] for v in maps],quotients=maps,
            cohomology_pullback_matrix=matrix_encode(rows),cohomology_rank=n,
            holomorphic_pullback_rank=self.curve.genus,orthogonal_complementary_sectors=True,
            isogeny_certified=True,isogeny_degree=2**self.curve.genus,kernel_annihilator=2,
            jacobian_maps='F=(pi_plus_*,pi_minus_*); G=pi_plus^*+pi_minus^*',
            composition_identities=['G F=[2] on Jac(C)','F G=[2] on the product of quotient Jacobians'],
            justification='actual degree-two quotient maps; pi^* pi_*=1+deck involution, hyperelliptic involution acts as -1; cross homomorphisms vanish; norm and pullback are dual for canonical principal polarizations, so deg(F)=deg(G)=2^g',
            scope='specific isogeny induced by these verified involution covers; no explicit integral kernel generators, torsion coordinates or arbitrary Jacobian factorization algorithm')

    def _reconstruct(self,square,u,limit):
        # Many orbit traces have a polynomial square in u. Solve that linear
        # identity first, without introducing denominator unknowns or taking
        # an inverse in a larger parameter tower.
        columns=[F.product(F.product(F.power(u.n,j),F.power(u.d,limit-j)),square.d) for j in range(limit+1)]
        target=F.product(square.n,F.power(u.d,limit));length=max(len(target),*(len(p) for p in columns))
        pad=lambda p:p+[self.zero]*(length-len(p))
        solution=solve_many(list(map(list,zip(*(pad(p) for p in columns)))),[[v] for v in pad(target)])
        if solution is not None:
            n=F.trim([v[0] for v in solution]);d=[self.one]
            if XFunction(n,d).at(u)!=square:raise AssertionError('polynomial quotient equation replay failed')
            return n,d
        if self.extension is None:
            # Work in K(U)[x]/(N(x)-U D(x)). Invariance and the full-degree
            # fixed-field certificate force the reduced answer to be constant
            # in x. This directly constructs the rational quotient equation.
            constant=all(len(a.n)==len(a.d)==1 for a in square.n+square.d+u.n+u.d)
            if constant:
                base=RF([0],budget=self.budget);U=RF([0,1],budget=self.budget)
                lift=lambda a:RF([a.evaluate(0)],budget=self.budget)
            else:
                def lift(a):
                    lower=ParameterFunction(['t'],a.n,a.d,self.budget)
                    return ParameterFunction(['t','U'],[lower],budget=self.budget)
                base=ParameterFunction(['t','U'],budget=self.budget);U=base.variable(1)
            modulus=F.add([lift(v) for v in u.n],F.scale([lift(v) for v in u.d],-U))
            extension=EtaleAlgebra(modulus,base,self.budget);x=extension.generator
            numerator=F.evaluate([extension.zero.coerce(lift(v)) for v in square.n],x)
            denominator=F.evaluate([extension.zero.coerce(lift(v)) for v in square.d],x)
            answer=numerator/denominator
            if len(answer.coefficients)!=1:raise AssertionError('invariant square did not descend to the fixed field')
            ratio=answer.coefficients[0]
            if max(len(ratio.n),len(ratio.d))>limit+1:raise WorkLimit('quotient equation exceeds rational reconstruction bound')
            lower=(lambda v:RF([v],budget=self.budget)) if constant else (lambda v:RF(v.n,v.d,budget=self.budget))
            n,d=[lower(v) for v in ratio.n],[lower(v) for v in ratio.d]
            if XFunction(n,d).at(u)!=square:raise AssertionError('fixed-field descent identity failed')
            return n,d
        powers=[u**j for j in range(limit+1)]
        for degree in range(limit+1):
            columns=powers[:degree+1]+[-square*p for p in powers[:degree+1]]
            common=[self.one]
            for col in columns:
                g=F.extended_gcd(common,col.d)[0];common=F.product(common,F.divide(col.d,g)[0])
            polys=[F.product(col.n,F.divide(common,col.d)[0]) for col in columns]
            length=max(len(p) for p in polys);pad=lambda p:p+[self.zero]*(length-len(p))
            rows=list(map(list,zip(*(pad(p) for p in polys))))
            for vector in nullspace(rows,2*(degree+1),self.zero):
                n=F.trim(vector[:degree+1]);d=F.trim(vector[degree+1:])
                if not any(d):continue
                ratio=XFunction(n,d)
                if ratio.at(u)!=square:raise AssertionError('fixed-field rational reconstruction failed')
                return ratio.n,ratio.d
        raise WorkLimit('quotient equation exceeds rational reconstruction bound')
