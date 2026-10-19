"""Streaming source-bound pp-bdd-trace/1 checker, independent of BDD construction.

This is external verification, NOT a Lean-kernel proof of the parsed bytes.
Only packed node/count and current-stage claim arrays are retained in memory.
"""
from array import array
import gzip
import hashlib
import lzma
import struct
from pathlib import Path

RECORD = struct.Struct('<8I')


class InvalidCertificate(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise InvalidCertificate(message)


def verify(path, rows, capacities):
    n = len(rows[0]) if rows else 0
    m = len(rows)
    require(0 <= n <= 62 and 1 <= m <= 16, 'source dimensions')
    require(len(capacities) == m and all(len(r) == n for r in rows), 'source shape')
    require(all(0 <= x <= 1000000 for r in rows for x in r), 'source costs')
    require(all(-1000000 <= c <= 1000000 for c in capacities), 'source capacities')
    suffix = [[sum(r[i:]) for i in range(n+1)] for r in rows]
    nodes = array('I', [n, 0, 0, n, 1, 1])
    counts = array('Q', [0, 1])
    thresholds, applies = array('I'), array('I')
    stage, previous, finished = 0, 1, False
    totals = [0]*6

    def node(i):
        require(i < len(counts), 'incorrect child/node reference')
        return nodes[3*i:3*i+3]

    def mk_matches(result, level, lo, hi):
        node(lo); node(hi); r = node(result)
        if lo == hi:
            require(result == lo, 'false reduction')
        else:
            require(list(r) == [level, lo, hi], 'branch/reduction mismatch')

    def threshold_result(proof, row, level, cap):
        if cap < 0:
            require(proof == 0, 'noncanonical rejecting threshold proof')
            return 0
        if cap >= suffix[row][level]:
            require(proof == 0, 'noncanonical accepting threshold proof')
            return 1
        require(0 < proof <= len(thresholds)//4, 'threshold proof reference')
        r, i, b, result = thresholds[4*(proof-1):4*proof]
        require((r, i, b) == (row, level, cap), 'threshold state/source mismatch')
        return result

    def conjunction_result(proof, a, b):
        node(a); node(b)
        if a == 0 or b == 0:
            expected = 0
        elif a == 1 or a == b:
            expected = b
        elif b == 1:
            expected = a
        else:
            require(0 < proof <= len(applies)//3, 'intersection proof reference')
            x, y, result = applies[3*(proof-1):3*proof]
            require((x, y) == tuple(sorted((a, b))), 'intersection operands')
            return result
        require(proof == 0, 'noncanonical base intersection proof')
        return expected

    opener = gzip.open if str(path).endswith('.gz') else lzma.open if str(path).endswith('.xz') else open
    payload_hash = hashlib.sha256()
    payload_bytes = 0
    with opener(path, 'rb') as source:
        def read(size):
            nonlocal payload_bytes
            data = source.read(size)
            payload_hash.update(data); payload_bytes += len(data)
            return data
        require(read(8) == b'PPBDD001', 'magic/version')
        dimensions = read(8)
        require(len(dimensions) == 8 and struct.unpack('<2I', dimensions) == (n,m), 'source dimensions mismatch')
        expected = b''.join(struct.pack('<i', x) for x in capacities)
        expected += b''.join(struct.pack('<I', x) for r in rows for x in r)
        require(read(len(expected)) == expected, 'literal source mismatch')
        while True:
            block = read(32*32768)
            if not block:
                break
            require(len(block) % 32 == 0, 'truncated record')
            for record in RECORD.iter_unpack(block):
                require(not finished, 'trailing records after finalization')
                tag, a, b, c, d, e, f, g = record
                require(1 <= tag <= 5, 'unknown tag')
                totals[tag] += 1
                if tag == 1:
                    require(stage < m and f == g == 0, 'node padding/stage')
                    level, lo, hi, count = a, b, c, d+(e<<32)
                    l = node(lo); h = node(hi)
                    require(level < n and l[0] > level and h[0] > level, 'variable-order violation')
                    require(lo != hi, 'unreduced node')
                    actual = (counts[lo] << (l[0]-level-1)) + (counts[hi] << (h[0]-level-1))
                    require(count == actual and count <= 1 << (n-level), 'manipulated node count')
                    nodes.extend((level,lo,hi)); counts.append(count)
                elif tag == 2:
                    row, level, cap, result, lp, hp = a,b,c,d,e,f
                    require(g == 0 and stage < m and row == stage and level < n and cap < suffix[row][level], 'threshold rule/state')
                    lo = threshold_result(lp,row,level+1,cap)
                    hi = threshold_result(hp,row,level+1,cap-rows[row][level])
                    mk_matches(result,level,lo,hi)
                    thresholds.extend((row,level,cap,result))
                elif tag == 3:
                    require(f == g == 0 and stage < m, 'intersection padding/stage')
                    x,y = node(a),node(b)
                    require(a > 1 and b > 1 and a != b, 'nonrecursive intersection')
                    level = min(x[0],y[0])
                    lo = conjunction_result(d,x[1] if x[0] == level else a,y[1] if y[0] == level else b)
                    hi = conjunction_result(e,x[2] if x[0] == level else a,y[2] if y[0] == level else b)
                    mk_matches(c,level,lo,hi)
                    applies.extend((*sorted((a,b)),c))
                elif tag == 4:
                    require(a == stage and stage < m, 'missing/repeated resource stage')
                    require(b == threshold_result(c,stage,0,capacities[stage]), 'resource root not source-bound')
                    require(d == conjunction_result(e,previous,b), 'resource conjunction chain')
                    require(f+(g<<32) == counts[d] << node(d)[0], 'stage count')
                    previous=d; stage+=1
                    thresholds=array('I'); applies=array('I')
                else:
                    require(stage == m and a == previous and d == e == f == g == 0, 'incomplete final chain')
                    require(b+(c<<32) == counts[a] << node(a)[0], 'manipulated final count')
                    finished=True
    require(finished, 'missing finalization')
    return {'schema':'pp-bdd-trace-check/1', 'status':'externally_checked_source_bound',
            'variables':n, 'resources':m, 'count':counts[previous] << node(previous)[0],
            'allocated_nodes':len(counts), 'records_by_tag':totals[1:],
            'uncompressed_sha256':payload_hash.hexdigest(), 'uncompressed_bytes':payload_bytes,
            'full_population_kernel_proved':False,
            'trust_boundary':'Python parser, packed tables, arithmetic and rule implementation; local rules have separate Lean proofs.'}


def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            h.update(block)
    return h.hexdigest()
