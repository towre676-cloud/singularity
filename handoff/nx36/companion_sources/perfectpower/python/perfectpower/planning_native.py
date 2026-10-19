"""Optional C++17 exact binary planner, bounded inputs and work budgets."""
import ctypes as C
import hashlib
import json
import shutil
import subprocess
import tempfile
import weakref
import threading
from pathlib import Path
from math import lcm
from .resources import runtime_root
from .divisor_square import WorkLimit

_LIBRARY = None

def available():
    from .shipped_native import shipped_library
    return _LIBRARY is not None or shipped_library('completion_planner',runtime_root()/'native/completion_planner.cpp') is not None or shutil.which('g++') is not None

def library():
    global _LIBRARY
    if _LIBRARY is None:
        source=runtime_root()/'native/completion_planner.cpp'
        from .shipped_native import shipped_library
        shipped=shipped_library('completion_planner',source)
        temporary=None
        if shipped:
            output,provenance=shipped
            lib=C.CDLL(str(output))
        else:
            compiler=shutil.which('g++')
            if compiler is None: raise WorkLimit('optional native planner requires a C++17 compiler')
            temporary=tempfile.TemporaryDirectory(prefix='perfectpower-planner-')
            output=Path(temporary.name)/'planner.so'
            try:
                subprocess.run([compiler,'-std=c++17','-O3','-fPIC','-shared',str(source),'-o',str(output)],check=True,capture_output=True,timeout=60)
                lib=C.CDLL(str(output))
            except (OSError,subprocess.SubprocessError) as e:
                temporary.cleanup();raise WorkLimit('optional native planner compilation failed') from e
            provenance={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'compiler':subprocess.check_output([compiler,'--version'],text=True).splitlines()[0], 'flags':['-std=c++17','-O3','-fPIC','-shared'],'scope':'tested native execution; no kernel proof of native algorithm'}
        common=[C.c_int,C.c_int,C.POINTER(C.c_uint64),C.POINTER(C.c_uint64),C.POINTER(C.c_uint64),C.POINTER(C.c_int64)]
        lib.pp_create.argtypes=common+[C.c_uint64,C.c_uint64,C.POINTER(C.c_void_p)];lib.pp_create.restype=C.c_void_p
        lib.pp_create_gray.argtypes=lib.pp_create.argtypes;lib.pp_create_gray.restype=C.c_void_p
        lib.pp_query.argtypes=[C.c_void_p,C.c_int,C.c_uint64];lib.pp_query.restype=C.c_void_p
        lib.pp_optimize.argtypes=common+[C.c_uint64];lib.pp_optimize.restype=C.c_void_p
        lib.pp_recursive.argtypes=common+[C.c_uint64];lib.pp_recursive.restype=C.c_void_p
        lib.pp_population.argtypes=common+[C.c_int,C.c_uint64,C.c_uint64,C.c_uint64,C.c_uint64,C.c_int];lib.pp_population.restype=C.c_void_p
        lib.pp_population_fixed.argtypes=common+[C.c_uint64]*5;lib.pp_population_fixed.restype=C.c_void_p
        lib.pp_destroy.argtypes=[C.c_void_p];lib.pp_destroy.restype=None
        lib.pp_free.argtypes=[C.c_void_p];lib.pp_free.restype=None
        lib._temporary=temporary
        lib._provenance=provenance
        _LIBRARY=lib
    return _LIBRARY

def parameters(planner):
    if planner.kind!='allocation' or planner.machine_model is not None or any(v[2:5]!=(0,1,2) for v in planner.variables):
        raise ValueError('native route requires independent original binary variables')
    n,m=len(planner.variables),len(planner.lower)
    scale=lcm(*(v[1].denominator for v in planner.variables));profit=[int(v[1]*scale) for v in planner.variables]
    if sum(abs(p) for p in profit)>2**60:raise WorkLimit('native exact objective scaling exceeds signed integer budget')
    return scale,(n,m,(C.c_uint64*m)(*planner.lower),(C.c_uint64*m)(*planner.upper),(C.c_uint64*(n*m))(*(x for v in planner.variables for x in v[0])),(C.c_int64*n)(*profit))

def result(lib,pointer):
    if not pointer:raise WorkLimit('native result allocation failed')
    try:r=json.loads(C.string_at(pointer))
    finally:lib.pp_free(pointer)
    if 'error' in r:
        error=WorkLimit(r['error']);error.details=r;raise error
    for k in ('count','ties','mask'):r[k]=int(r[k])
    return r

class NativeIndex:
    def __init__(self,planner,exhaustive=False):
        self.lib=library();self.scale,args=parameters(planner);self.n=args[0]
        error=C.c_void_p()
        self.handle=(self.lib.pp_create_gray if exhaustive else self.lib.pp_create)(*args,planner.native_records,planner.native_visits,C.byref(error))
        if not self.handle:
            message=C.string_at(error).decode() if error.value else 'native allocation failed'
            if error.value:self.lib.pp_free(error)
            raise WorkLimit(message)
        self._finalizer=weakref.finalize(self,self.lib.pp_destroy,self.handle)
        self.cache={};self.query_visits=0;self.lock=threading.RLock()
    def query(self,prefix):
        with self.lock:
            return self._query(prefix)
    def _query(self,prefix):
        if len(prefix)>self.n or any(type(x) is not int or x not in (0,1) for x in prefix):raise ValueError('binary original-coordinate prefix required')
        key=tuple(prefix)
        if key not in self.cache:
            mask=0
            for x in prefix:mask=2*mask+x
            r=result(self.lib,self.lib.pp_query(self.handle,len(prefix),mask));self.query_visits+=r['visits']
            if len(self.cache)>=8192:self.cache.clear()
            self.cache[key]=r
        return self.cache[key]

def optimize(planner):
    lib=library();scale,args=parameters(planner)
    r=result(lib,lib.pp_optimize(*args,planner.native_visits))
    return r,scale,lib._provenance


def recursive_reference(planner):
    lib=library();scale,args=parameters(planner)
    return result(lib,lib.pp_recursive(*args,planner.native_visits)),scale


class PopulationIndex:
    """Bounded residual polynomials and disjoint original-identity partitions.

    Each native call has a capped arena. Resource exhaustion splits a free
    original project and sums both populations, never accepting the failed
    call as a count. Completed fixed-coordinate answers and split decisions
    remain available to conditional queries. Python tree size and cumulative
    setup/search work per query have separate explicit limits.
    """
    def __init__(self, planner):
        self.planner = weakref.proxy(planner)
        self.lib = library()
        self.scale, self.args = parameters(planner)
        self.n = self.args[0]
        self.memory = planner.population_memory
        self.states = planner.population_cache_states
        self.visits = planner.native_visits
        self.partition_limit = planner.population_partition_limit
        self.work_limit = planner.population_work_limit
        self.cache, self.fixed_cache, self.partitions = {}, {}, {}
        self.query_visits = self.setup_cells = self.failed_calls = 0
        self.native_calls = 0
        self.order = sorted(range(self.n), key=lambda j: sum(
            v*1000000//max(1, planner.upper[k])
            for k, v in enumerate(planner.variables[j][0])), reverse=True)
        self.lock = threading.RLock()

    @staticmethod
    def combine(a, b):
        if not a['count']:
            return dict(b)
        if not b['count']:
            return dict(a)
        best = max(a['best'], b['best'])
        winners = [r for r in (a, b) if r['best'] == best]
        return {'count': a['count']+b['count'], 'best': best,
                'ties': sum(r['ties'] for r in winners),
                'mask': min(r['mask'] for r in winners), 'visits': 0,
                'records': 0, 'setup_cells': 0}

    def _progress(self):
        callback = self.planner._progress
        if callback:
            callback({"native_calls": self.native_calls, "failed_attempts": self.failed_calls,
                      "completed_nodes": len(self.fixed_cache), "split_nodes": len(self.partitions),
                      "search_visits": self.query_visits, "setup_cells": self.setup_cells,
                      "arena_limit_bytes": self.memory})

    def _room(self):
        if len(self.fixed_cache)+len(self.partitions) >= self.partition_limit:
            raise WorkLimit('population partition node budget exceeded')

    def _fold(self, fixed, values, work):
        key = (fixed, values)
        if key in self.fixed_cache:
            return dict(self.fixed_cache[key])
        if key in self.partitions:
            bit = self.partitions[key]
            a = self._fold(fixed|bit, values, work)
            b = self._fold(fixed|bit, values|bit, work)
            answer = self.combine(a, b)
            self._room()
            self.fixed_cache[key] = answer
            return dict(answer)
        remaining = self.work_limit-work[0]
        if remaining <= 0:
            raise WorkLimit('population cumulative query work budget exceeded')
        self.native_calls += 1
        try:
            answer = result(self.lib, self.lib.pp_population_fixed(
                *self.args, fixed, values, self.states,
                min(self.visits, remaining), self.memory))
        except WorkLimit as error:
            details = getattr(error, 'details', {})
            visits, cells = details.get('visits', 0), details.get('setup_cells', 0)
            self.query_visits += visits
            self.setup_cells += cells
            self.failed_calls += 1
            self._progress()
            work[0] += visits+cells
            if work[0] >= self.work_limit:
                raise WorkLimit('population cumulative query work budget exceeded') from error
            if not str(error).startswith('population '):
                raise
            self._room()
            free = next((j for j in self.order if not fixed & (1 << (self.n-1-j))), None)
            if free is None:
                raise
            bit = 1 << (self.n-1-free)
            self.partitions[key] = bit
            return self._fold(fixed, values, work)
        self.query_visits += answer['visits']
        self.setup_cells += answer.get('setup_cells', 0)
        work[0] += answer['visits']+answer.get('setup_cells', 0)
        self._room()
        self.fixed_cache[key] = answer
        self._progress()
        return dict(answer)

    def _condition_tree(self, fixed, values, query_fixed, query_values, work):
        if (values ^ query_values) & fixed & query_fixed:
            return {'count': 0, 'best': 0, 'ties': 0, 'mask': 0, 'visits': 0, 'records': 0}
        key = (fixed, values)
        if key in self.partitions:
            bit = self.partitions[key]
            if bit & query_fixed:
                return self._condition_tree(fixed|bit, values|(query_values & bit),
                                            query_fixed, query_values, work)
            a = self._condition_tree(fixed|bit, values, query_fixed, query_values, work)
            b = self._condition_tree(fixed|bit, values|bit, query_fixed, query_values, work)
            return self.combine(a, b)
        return self._fold(fixed|query_fixed, values|query_values, work)

    def query(self, prefix):
        if not isinstance(prefix, (list, tuple)) or len(prefix) > self.n or any(type(x) is not int or x not in (0, 1) for x in prefix):
            raise ValueError('binary original-coordinate prefix required')
        key = tuple(prefix)
        with self.lock:
            if key not in self.cache:
                fixed = values = 0
                for j, x in enumerate(prefix):
                    bit = 1 << (self.n-1-j)
                    fixed |= bit
                    if x:
                        values |= bit
                work = [0]
                r = self._condition_tree(0, 0, fixed, values, work)
                if len(self.cache) >= 8192:
                    self.cache.clear()
                self.cache[key] = r
            return dict(self.cache[key])

    def partition_receipt(self):
        """A replayable disjoint-cover tree; native leaf answers are tested data."""
        return {'schema': 'pp-population-partition/1', 'variables': self.n,
                'splits': [{'fixed': f, 'values': v, 'bit': bit}
                           for (f, v), bit in sorted(self.partitions.items())],
                'answers': [{'fixed': f, 'values': v, 'answer': dict(answer)}
                            for (f, v), answer in sorted(self.fixed_cache.items())],
                'native_calls': self.native_calls, 'failed_calls': self.failed_calls,
                'search_visits': self.query_visits, 'setup_cells': self.setup_cells,
                'arena_limit_bytes': self.memory, 'partition_limit': self.partition_limit,
                'query_work_limit': self.work_limit}
