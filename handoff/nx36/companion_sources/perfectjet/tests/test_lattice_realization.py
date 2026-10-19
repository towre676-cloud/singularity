import unittest,itertools,random
from fractions import Fraction as Q
from perfectjet.exact import rank,matmul
from perfectjet.lattice import (smith_form,invariant_factors,determinantal_divisors,integer_solve,
                                integer_kernel,saturation,integer_inverse)
from perfectjet.realization import LinearRepresentation,realize,held_out,coarsest_lumping,words
from perfectjet.populations import weighted_quotient_replay


def random_matrix(rng,m,n,lo=-6,hi=6):
    return [[rng.randint(lo,hi) for _ in range(n)] for _ in range(m)]


def det(a):
    from perfectjet.lattice import _determinant
    return _determinant(a)


class LatticeTests(unittest.TestCase):
    def test_smith_shape_and_unimodularity(self):
        rng=random.Random(7)
        for _ in range(60):
            m,n=rng.randint(1,4),rng.randint(1,4);a=random_matrix(rng,m,n)
            if rng.random()<.3:a.append([x+y for x,y in zip(a[0],a[-1])])
            u,d,v=smith_form(a)
            self.assertEqual(matmul(matmul(u,a),v),[[Q(x) for x in row] for row in d])
            self.assertEqual(abs(det(u)),1);self.assertEqual(abs(det(v)),1)
            diag=[d[i][i] for i in range(min(len(d),len(d[0])))]
            self.assertTrue(all(d[i][j]==0 for i in range(len(d)) for j in range(len(d[0])) if i!=j))
            nz=[x for x in diag if x];self.assertTrue(all(x>0 for x in nz))
            self.assertEqual(diag[:len(nz)],nz)
            self.assertTrue(all(nz[i+1]%nz[i]==0 for i in range(len(nz)-1)))
            self.assertEqual(len(nz),rank(a))

    def test_invariants_match_determinantal_divisors(self):
        # Independent route: d1*...*dk = gcd of k-by-k minors.
        rng=random.Random(11)
        for _ in range(40):
            a=random_matrix(rng,rng.randint(1,4),rng.randint(1,4));f=invariant_factors(a);prod=1
            for k in range(1,min(len(a),len(a[0]))+1):
                if k<=len(f):prod*=f[k-1];self.assertEqual(determinantal_divisors(a,k),prod)
                else:self.assertEqual(determinantal_divisors(a,k),0)
        self.assertEqual(invariant_factors([[2,4,4],[-6,6,12],[10,-4,-16]]),[2,6,12])

    def test_integer_solve_against_box_search(self):
        rng=random.Random(5)
        for _ in range(80):
            m,n=rng.randint(1,3),rng.randint(1,3);a=random_matrix(rng,m,n,-3,3)
            b=[rng.randint(-4,4) for _ in range(m)];r=integer_solve(a,b)
            if r['solvable']:
                self.assertEqual([sum(x*y for x,y in zip(row,r['solution'])) for row in a],b)
            else:
                y=r['certificate']
                ya=[sum((y[i]*a[i][j] for i in range(m)),Q(0)) for j in range(n)]
                self.assertTrue(all(x.denominator==1 for x in ya))
                yb=sum((p*q for p,q in zip(y,b)),Q(0))
                if r['rational']:self.assertNotEqual(yb.denominator,1)
                else:self.assertFalse(any(ya));self.assertNotEqual(yb,0)
                for x in itertools.product(range(-6,7),repeat=n):
                    self.assertNotEqual([sum(p*q for p,q in zip(row,x)) for row in a],b)

    def test_rational_span_is_not_integer_span(self):
        r=integer_solve([[2,0],[0,3]],[1,3])
        self.assertFalse(r['solvable']);self.assertTrue(r['rational'])
        self.assertEqual(integer_solve([[1,1],[1,1]],[1,2])['rational'],False)

    def test_integer_kernel_basis(self):
        rng=random.Random(3)
        for _ in range(40):
            a=random_matrix(rng,rng.randint(1,3),rng.randint(2,4),-4,4);k=integer_kernel(a);n=len(a[0])
            self.assertEqual(len(k),n-rank(a))
            for v in k:self.assertTrue(all(sum(x*y for x,y in zip(row,v))==0 for row in a))
            if k:  # basis of the full integer kernel: saturated in Z^n
                self.assertEqual(saturation(k)['index'],1)
                for x in itertools.product(range(-2,3),repeat=n):
                    if all(sum(p*q for p,q in zip(row,x))==0 for row in a):
                        self.assertTrue(integer_solve([list(c) for c in zip(*k)],list(x))['solvable'])

    def test_saturation_index_and_witness(self):
        rng=random.Random(13)
        for _ in range(40):
            g=random_matrix(rng,rng.randint(1,3),3,-5,5)
            if rank(g)<len(g):continue
            s=saturation(g);self.assertEqual(s['index'],determinantal_divisors(g,len(g)))
            if s['index']>1:
                w=s['witness'];self.assertEqual(rank(g+[w]),rank(g))
                self.assertFalse(integer_solve([list(c) for c in zip(*g)],w)['solvable'])
        self.assertEqual(saturation([[2,0],[0,1]])['witness'],[1,0])

    def test_integer_inverse_rejects_nonunimodular(self):
        self.assertEqual(integer_inverse([[2,1],[1,1]]),[[1,-1],[-1,2]])
        with self.assertRaises(ValueError):integer_inverse([[2,0],[0,1]])
        with self.assertRaises(ValueError):smith_form([[Q(1,2)]])


class RealizationTests(unittest.TestCase):
    def random_rep(self,rng,dim,letters):
        r=lambda:Q(rng.randint(-3,3),rng.randint(1,3))
        return LinearRepresentation([r() for _ in range(dim)],
                                    [[[r() for _ in range(dim)] for _ in range(dim)] for _ in range(letters)],
                                    [r() for _ in range(dim)])

    def test_recovers_generic_dimension(self):
        rng=random.Random(17)
        for dim in (1,2,3):
            f=self.random_rep(rng,dim,2);model,info=realize(f,2,dim)
            self.assertEqual(info['rank'],dim);self.assertIsNone(held_out(model,f,2,7))

    def test_redundant_states_are_removed(self):
        # Two copies of the same one-dimensional behaviour plus an unreachable state.
        f=LinearRepresentation([1,1,0],[[[2,0,0],[0,2,0],[0,0,5]],[[1,0,0],[0,1,0],[0,0,7]]],[1,1,1])
        model,info=realize(f,2,3);self.assertEqual(info['rank'],1)
        self.assertIsNone(held_out(model,f,2,7))

    def test_sequence_realization(self):
        from perfectjet.exact import hankel
        # x_n=x_{n-1}+x_{n-3}-x_{n-4}; the impulse needs all four states, 1,0,0,1 only three.
        for start,expected in (([0,0,0,1],4),([1,0,0,1],3)):
            seq=list(start)
            for _ in range(30):seq.append(seq[-1]+seq[-3]-seq[-4])
            f=lambda w,seq=seq:seq[len(w)]
            model,info=realize(f,1,4);self.assertEqual(info['rank'],expected)
            self.assertEqual(info['rank'],rank(hankel(seq,10,10)))
            self.assertIsNone(held_out(model,f,1,30))

    def test_insufficient_block_returns_witness(self):
        f=lambda w:int(len(w)==5)
        model,info=realize(f,1,1);self.assertEqual(info['rank'],0)
        self.assertEqual(held_out(model,f,1,8)['word'],(0,)*5)
        model,info=realize(f,1,5);self.assertIsNone(held_out(model,f,1,12))

    def test_hankel_rank_matches_brute_rank(self):
        count=lambda w:sum(1 for i in range(len(w)-1) if w[i:i+2]==(0,1))
        ws=words(2,3)
        self.assertEqual(realize(count,2,3)[1]['rank'],rank([[count(p+s) for s in ws] for p in ws]))


def set_partitions(items):
    if not items:yield [];return
    first,rest=items[0],items[1:]
    for p in set_partitions(rest):
        yield [[first]]+p
        for i in range(len(p)):yield p[:i]+[[first]+p[i]]+p[i+1:]


def valid_lumping(actions,output,blocks):
    r=[[int(j in b) for j in range(len(actions[0]))] for b in blocks]
    for a in actions:
        for b in blocks:
            for c in blocks:
                if len({sum(a[i][j] for i in b) for j in c})>1:return False
    return all(len({row[j] for j in b})==1 for row in output for b in blocks)


class LumpingTests(unittest.TestCase):
    def test_coarsest_against_all_partitions(self):
        rng=random.Random(23)
        for _ in range(25):
            n=rng.randint(2,5);k=rng.randint(1,n);labels=[rng.randrange(k) for _ in range(n)]
            actions=[]
            for _ in range(rng.randint(1,2)):
                # Plant lumpability: column totals into each label-block depend only on the source label.
                totals={(b,c):rng.randint(0,3) for b in range(k) for c in range(k)}
                a=[[0]*n for _ in range(n)]
                for j in range(n):
                    for b in range(k):
                        members=[i for i in range(n) if labels[i]==b]
                        if members:
                            t=totals[(b,labels[j])];split=rng.randrange(len(members))
                            a[members[split]][j]+=t
                actions.append(a)
            output=[[labels[j]%2 for j in range(n)]]
            r=coarsest_lumping(actions,output)
            for a,ab in zip(actions,r['reduced']):self.assertTrue(weighted_quotient_replay(a,r['aggregation'],ab))
            found={j:i for i,b in enumerate(r['blocks']) for j in b}
            for p in set_partitions(list(range(n))):
                if valid_lumping(actions,output,p):
                    self.assertTrue(all(len({found[j] for j in b})==1 for b in p))
            self.assertTrue(valid_lumping(actions,output,r['blocks']))

    def test_series_preserved(self):
        a=[[0,1,1],[1,0,0],[1,1,1]];h=[[1,0,0]];s=[2,3,-1]
        r=coarsest_lumping([a],h);self.assertEqual(r['blocks'],[[0],[1,2]])
        ab=r['reduced'][0];sb=[sum(Q(x)*y for x,y in zip(row,s)) for row in r['aggregation']]
        x,y=[[Q(v)] for v in s],[[v] for v in sb]
        for _ in range(8):
            self.assertEqual(matmul(h,x),matmul(r['output'],y));x=matmul(a,x);y=matmul(ab,y)

    def test_initial_labels_refine(self):
        r=coarsest_lumping([[[1,0],[0,1]]],None,initial=['a','b'])
        self.assertEqual(r['blocks'],[[0],[1]])
        self.assertEqual(coarsest_lumping([[[1,0],[0,1]]])['blocks'],[[0,1]])


if __name__=='__main__':unittest.main()
