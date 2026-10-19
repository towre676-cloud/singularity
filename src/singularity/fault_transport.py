"""Exact finite-horizon Woodbury transport for sparse discrete thermal models.

A removed bond adds +delta*b*b.T to A.  All series have a formal unit
constant denominator; no evaluation at a possibly singular z is performed.
The small Volterra recurrence below is coefficient-wise Woodbury, not another
full faulted state simulation. Candidate identities are retained by callers.
"""
from dataclasses import dataclass
from fractions import Fraction
from .thermal_diagnostics import AffineCandidate


def _q(x):
    if isinstance(x, bool) or not isinstance(x, (int, Fraction)):
        raise TypeError('exact int or Fraction required')
    return Fraction(x)


def _nat(x, minimum=0):
    if isinstance(x, bool) or not isinstance(x, int) or x < minimum:
        raise ValueError('integer outside allowed range')
    return x


@dataclass(frozen=True)
class BondFault:
    u: int
    v: int
    removed_conductance: Fraction

    def __post_init__(self):
        u, v = _nat(self.u), _nat(self.v)
        if u == v:
            raise ValueError('bond endpoints must differ')
        object.__setattr__(self, 'u', min(u, v))
        object.__setattr__(self, 'v', max(u, v))
        delta = _q(self.removed_conductance)
        if delta < 0:
            raise ValueError('removed conductance must be nonnegative')
        object.__setattr__(self, 'removed_conductance', delta)


def _checked_faults(candidate, faults):
    data = {(i, j): a for i, j, a in candidate.entries}
    total = {}
    for fault in faults:
        if not isinstance(fault, BondFault) or fault.v >= candidate.dimension:
            raise ValueError('invalid bond fault')
        key = fault.u, fault.v
        nominal = data.get(key, 0)
        if nominal <= 0 or nominal != data.get(key[::-1], 0):
            raise ValueError('fault requires an existing symmetric positive coupling')
        total[key] = total.get(key, Fraction()) + fault.removed_conductance
        if total[key] > nominal:
            raise ValueError('removed conductance exceeds available bond')
    return tuple(BondFault(u, v, d) for (u, v), d in sorted(total.items()))


def apply_faults(candidate, faults, identifier='transported_fault'):
    """Independent original sparse model constructor; heaters/sensors unchanged."""
    faults = _checked_faults(candidate, faults)
    data = {(i, j): a for i, j, a in candidate.entries}
    for f in faults:
        u, v, d = f.u, f.v, f.removed_conductance
        for key, sign in (((u,u),1), ((v,v),1), ((u,v),-1), ((v,u),-1)):
            data[key] = data.get(key, Fraction()) + sign*d
    return AffineCandidate(identifier, candidate.dimension,
        tuple((i,j,a) for (i,j),a in sorted(data.items()) if a),
        candidate.heater, candidate.sensors)


class NominalTransferCache:
    """Shared nominal powers; bond-column powers are constructed lazily.

    Bounds are explicit finite-horizon resource guards. The original source
    dimension and exact entries are preserved; no dense homogeneous lift.
    """
    def __init__(self, candidate, horizon, max_faults=16, max_cells=2_000_000):
        if not isinstance(candidate, AffineCandidate):
            raise TypeError('AffineCandidate required')
        self.candidate = candidate
        self.horizon = _nat(horizon)
        self.max_faults = _nat(max_faults, 1)
        self.max_cells = _nat(max_cells, 1)
        if candidate.dimension*(horizon+1) > self.max_cells:
            raise ValueError('nominal cache resource limit')
        self._columns = {}
        self._input = {}
        self.nominal = self._responses(candidate.heater)

    def _step(self, x):
        out = [Fraction() for _ in x]
        for i,j,a in self.candidate.entries:
            if x[j]:
                out[i] += a*x[j]
        return tuple(out)

    def _powers(self, vector):
        vector = tuple(map(_q, vector))
        if len(vector) != self.candidate.dimension:
            raise ValueError('input dimension mismatch')
        powers = [vector]
        for _ in range(self.horizon):
            powers.append(self._step(powers[-1]))
        return tuple(powers)

    def _responses(self, vector):
        powers = self._powers(vector)
        readings = tuple(tuple(sum((c*x for c,x in zip(sensor,p)), Fraction())
                               for p in powers) for sensor in self.candidate.sensors)
        return powers, readings

    def column(self, u, v):
        key = u, v
        if key not in self._columns:
            cells = (len(self._columns)+2)*self.candidate.dimension*(self.horizon+1)
            if cells > self.max_cells:
                raise ValueError('bond-column cache resource limit')
            b = tuple(Fraction(int(i==u)-int(i==v)) for i in range(self.candidate.dimension))
            self._columns[key] = self._responses(b)
        return self._columns[key]


def fault_set_transfer(cache, faults, input_vector=None):
    """Return exact CA_f^r B for r=0..H, using a k-state Volterra system.

    Coupling order is G*D, never commuted to D*G. Zero severities and linearly
    dependent bond columns are legitimate because the formal inverse starts I.
    """
    if not isinstance(cache, NominalTransferCache):
        raise TypeError('NominalTransferCache required')
    faults = _checked_faults(cache.candidate, tuple(faults))
    if len(faults) > cache.max_faults:
        raise ValueError('fault set resource limit')
    H = cache.horizon
    powers, nominal = cache.nominal if input_vector is None else cache._responses(input_vector)
    columns = [cache.column(f.u, f.v) for f in faults]
    v = [[p[f.u]-p[f.v] for p in powers] for f in faults]
    gram = [[[p[f.u]-p[f.v] for p in col[0]] for col in columns] for f in faults]
    w = [[Fraction() for _ in range(H+1)] for _ in faults]
    for t in range(H+1):
        for j in range(len(faults)):
            w[j][t] = v[j][t] + sum((faults[i].removed_conductance * gram[j][i][t-1-r]*w[i][r]
                for r in range(t) for i in range(len(faults))), Fraction())
    output = []
    for s, row in enumerate(nominal):
        output.append(tuple(row[t] + sum((f.removed_conductance * columns[i][1][s][t-1-r]*w[i][r]
            for r in range(t) for i,f in enumerate(faults)), Fraction()) for t in range(H+1)))
    return tuple(output)


def bond_transfer(cache, fault, input_vector=None):
    return fault_set_transfer(cache, (fault,), input_vector)


def protocol_from_impulse(impulse, word, initial_response=0):
    """y_T=sum CA^(T-1-t)B*u_t + CA^T*x0; caller supplies initial term."""
    word = tuple(map(_q, word)); impulse = tuple(map(_q, impulse))
    if len(word) > len(impulse):
        raise ValueError('protocol exceeds retained impulse horizon')
    return _q(initial_response) + sum((impulse[len(word)-1-t]*u for t,u in enumerate(word)), Fraction())


def bond_transfer_factors(cache,fault):
    """Sign-correct scalar Sherman--Morrison factors as truncated exact series.

    denominator encodes 1-z*delta*b.T*R0*b and has constant coefficient 1.
    Every sensor correction numerator is z*delta*(C R0 b)*(b.T R0 B).
    """
    (fault,)=_checked_faults(cache.candidate,(fault,));H=cache.horizon
    columns,readings=cache.column(fault.u,fault.v)
    self_response=tuple(p[fault.u]-p[fault.v] for p in columns)
    input_response=tuple(p[fault.u]-p[fault.v] for p in cache.nominal[0])
    denominator=(Fraction(1),)+tuple(-fault.removed_conductance*self_response[t-1] for t in range(1,H+1))
    numerators=tuple((Fraction(),)+tuple(fault.removed_conductance*sum((row[j]*input_response[t-1-j] for j in range(t)),Fraction())
                                              for t in range(1,H+1)) for row in readings)
    return {'self_response':self_response,'input_response':input_response,
            'sensor_response':readings,'denominator':denominator,'correction_numerators':numerators,
            'representation':'formal series truncated through declared horizon; unit constant denominator'}
