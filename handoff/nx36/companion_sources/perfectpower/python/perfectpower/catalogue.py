"""SQLite definitions, immutable content addresses and bounded exact joins."""
import json
import sqlite3
from hashlib import sha256
from collections import OrderedDict
from fractions import Fraction
from .divisor_square import WorkLimit


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), default=lambda v: str(v) if isinstance(v, Fraction) else _bad(v), allow_nan=False)


def _bad(value):
    raise TypeError(f'unsupported JSON value: {type(value).__name__}')


def compile_object(kind, specification):
    from .populations import ExactPopulation
    from .population_algebra import PopulationComparison
    from .application_objects import SequenceLibrary, InverseDesign, GraphEnsemble, GeometryWorkbench, CombinatorialDesign
    from .projected_populations import ProjectedPopulation
    from .factorial_library import FactorialLibrary
    from .decision_regions import CalibrationPolicy
    from .diagnostic_programs import DiagnosticPolicy
    from .curve_families import CurveFamily
    from .multi_curve_families import MultiCurveFamily
    from .elliptic_quotients import EllipticQuotientFamily
    from .differential_extensions import DifferentialExtension
    from .symmetry_quotients import SymmetryCurve
    from .differential_modules import DifferentialModule
    from .superelliptic_families import SuperellipticFamily
    from .binomial_periods import BinomialSum
    from .elliptic_arithmetic import EllipticCurve
    constructors = dict(differential_module=DifferentialModule,superelliptic_family=SuperellipticFamily,binomial_sum=BinomialSum,differential_extension=DifferentialExtension,symmetry_curve=SymmetryCurve,multi_curve_family=MultiCurveFamily,elliptic_quotient=EllipticQuotientFamily,curve_family=CurveFamily,calibration_policy=CalibrationPolicy,diagnostic_policy=DiagnosticPolicy,population=ExactPopulation,population_comparison=PopulationComparison, sequence=SequenceLibrary, inverse=InverseDesign,
                        graph=GraphEnsemble, geometry=GeometryWorkbench, combinatorial=CombinatorialDesign,projected=ProjectedPopulation,factorial=FactorialLibrary)
    constructors['elliptic_curve']=EllipticCurve
    from .generating_functions import RationalSeries
    from .budget_populations import BudgetPopulation
    from .holonomic_series import ThetaSeries
    constructors.update(rational_series=RationalSeries, budget_population=BudgetPopulation, theta_series=ThetaSeries)
    from .planning import CompletionPlanner
    constructors['completion_planner'] = CompletionPlanner
    if kind not in constructors:
        raise ValueError('unsupported catalogue kind')
    return constructors[kind](specification)


class Catalogue:
    def __init__(self, path, *, cache_limit=32, allow_thread_change=False):
        if type(cache_limit) is not int or not 1 <= cache_limit <= 256:
            raise ValueError('cache limit 1 through 256 required')
        if type(allow_thread_change) is not bool:raise ValueError('thread option must be Boolean')
        self.db = sqlite3.connect(path,check_same_thread=not allow_thread_change)
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''CREATE TABLE IF NOT EXISTS objects
            (id TEXT PRIMARY KEY, kind TEXT NOT NULL, specification TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS aliases
            (name TEXT PRIMARY KEY, id TEXT NOT NULL REFERENCES objects(id));''')
        self.cache_limit, self.cache = cache_limit, OrderedDict()
        self.compilations = 0

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        self.db.close(); self.cache.clear()

    def _remember(self, identity, obj):
        self.cache[identity] = obj; self.cache.move_to_end(identity)
        while len(self.cache) > self.cache_limit:
            self.cache.popitem(last=False)

    def register(self, kind, specification, name=None, *, replace=False):
        if type(replace) is not bool:
            raise ValueError('replace must be Boolean')
        if name is not None and (not isinstance(name, str) or not name or len(name) > 128):
            raise ValueError('alias must be 1 through 128 characters')
        payload = encoded(specification)
        if len(payload.encode()) > 1000000:
            raise WorkLimit('definition exceeds one-megabyte budget')
        identity = sha256(('pp-catalogue/1\n'+kind+'\n'+payload).encode()).hexdigest()
        if identity not in self.cache:
            obj = compile_object(kind, json.loads(payload)); self.compilations += 1
        else:
            obj = self.cache[identity]
        with self.db:
            if name is not None:
                previous = self.db.execute('SELECT id FROM aliases WHERE name=?', (name,)).fetchone()
                if previous and previous[0] != identity and not replace:
                    raise ValueError('alias exists; explicit replace required')
            self.db.execute('INSERT OR IGNORE INTO objects VALUES (?,?,?)', (identity, kind, payload))
            if name is not None:
                self.db.execute('INSERT INTO aliases VALUES (?,?) ON CONFLICT(name) DO UPDATE SET id=excluded.id', (name, identity))
        self._remember(identity, obj)
        return dict(id=identity, kind=kind, name=name)

    def definition(self, reference):
        row = self.db.execute('SELECT id,kind,specification FROM objects WHERE id=COALESCE((SELECT id FROM aliases WHERE name=?),?)', (reference, reference)).fetchone()
        if row is None:
            raise KeyError('unknown catalogue object')
        return dict(id=row[0], kind=row[1], specification=json.loads(row[2]))

    def get(self, reference):
        definition = self.definition(reference); identity = definition['id']
        if identity not in self.cache:
            obj = compile_object(definition['kind'], definition['specification']); self.compilations += 1
            self._remember(identity, obj)
        self.cache.move_to_end(identity)
        return self.cache[identity]

    def list(self, offset=0, size=100):
        if type(offset) is not int or offset < 0 or type(size) is not int or not 0 <= size <= 1000:
            raise ValueError('nonnegative offset and size 0 through 1000 required')
        rows = self.db.execute('SELECT id,kind FROM objects ORDER BY id LIMIT ? OFFSET ?', (size, offset)).fetchall()
        return [dict(id=i, kind=k, aliases=[r[0] for r in self.db.execute('SELECT name FROM aliases WHERE id=? ORDER BY name', (i,))]) for i, k in rows]

    def join(self, left, right, *, mode='rank', start=0, size=100, left_field=None, right_field=None,
             left_fields=None, right_fields=None, row_limit=10000):
        """Rank zip, or complete bounded value join preserving multiplicities."""
        if any(self.definition(r)['kind'] != 'population' for r in (left, right)):
            raise ValueError('joins require two population objects')
        a, b = self.get(left), self.get(right)
        if type(row_limit) is not int or not 1 <= row_limit <= 100000:
            raise ValueError('row limit 1 through 100000 required')
        if mode == 'rank':
            if type(start) is not int or start < 0 or type(size) is not int or not 0 <= size <= row_limit:
                raise ValueError('bounded nonnegative rank window required')
            return [dict(left=a.select(i), right=b.select(i)) for i in range(start, min(start+size, a.cardinality, b.cardinality))]
        if mode != 'value':
            raise ValueError('join mode rank or value required')
        if a.cardinality+b.cardinality > row_limit:
            raise WorkLimit('complete value join inputs exceed row budget')
        from .projected_populations import join_fields
        def fields(population):
            spec=population.specification
            return spec if spec['kind']=='domain' else dict(fields={'x':None,'y':None})
        lf,rf=join_fields(fields(a),fields(b),left_field,right_field,left_fields,right_fields)
        index = {}
        for r in b.page(0, b.cardinality):
            value = tuple(r['values'][f] for f in rf); index.setdefault(value, []).append(r)
        result = []
        for l in a.page(0, a.cardinality):
            for r in index.get(tuple(l['values'][f] for f in lf), []):
                if len(result) == row_limit:
                    raise WorkLimit('complete join output exceeds row budget; no partial result returned')
                result.append(dict(left=l, right=r))
        return result
