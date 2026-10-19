#!/usr/bin/env python3
"""Small setup-inclusive period benchmark, deliberately outside exact receipts."""
from pathlib import Path
from fractions import Fraction as Q
import json,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from singularity.period_observations import (legendre_connection,legendre_series,
    differential_closure,RationalConnection,transport_targets,legendre_quadrature)


def main():
    records={}
    start=time.perf_counter();connection=legendre_connection();seed,radii=legendre_series(Q(1,2),48)
    full=transport_targets(connection,((1,0),(0,1)),(Q(1,2),Q(9,16)),seed,radii)
    records['full']={'seconds_including_setup':time.perf_counter()-start,'rank':2,
        'target_interval':full['outputs'][0]['interval']}
    start=time.perf_counter();connection=legendre_connection();closure=differential_closure(connection,((1,0),))
    seed,radii=legendre_series(Q(1,2),48)
    reduced=RationalConnection(closure.reduced_connection,connection.chart,connection.source_revision)
    out=transport_targets(reduced,closure.target_coordinates,(Q(1,2),Q(9,16)),seed,radii)
    records['target_reduced']={'seconds_including_setup':time.perf_counter()-start,'rank':closure.rank,
        'target_interval':out['outputs'][0]['interval']}
    start=time.perf_counter();quad=legendre_quadrature(Q(9,16),128)
    records['direct_euler_quadrature']={'seconds_including_setup':time.perf_counter()-start,'cells':128,'target_interval':quad}
    for record in records.values():
        a,b=record['target_interval'];scale=1<<64
        a=Q(a.numerator*scale//a.denominator,scale)
        b=Q(-(-b.numerator*scale//b.denominator),scale)
        record['width']=[(b-a).numerator,(b-a).denominator]
        record['target_interval']=[[x.numerator,x.denominator]for x in (a,b)]
    record={'schema':'nx31.setup-inclusive-benchmark/1','normalization':'F=2K/pi at9/16; seed at1/2',
        'records':records,'scope':'wall-clock on this machine; rank-two Legendre target has no dimension reduction; not rerun in CI'}
    (ROOT/'results/nx36/nx31_benchmark.json').write_text(json.dumps(record,indent=2,sort_keys=True)+'\n')
    print(json.dumps(record,indent=2))

if __name__=='__main__':main()
