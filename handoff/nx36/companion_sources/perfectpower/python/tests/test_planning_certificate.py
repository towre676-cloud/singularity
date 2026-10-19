"""Independent exhaustive semantics and adversarial binary certificate checks."""
import itertools
import random
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from perfectpower.planning_certificate import verify, InvalidCertificate

ROOT=Path(__file__).resolve().parents[2]


class Certificates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work=tempfile.TemporaryDirectory()
        cls.binary=Path(cls.work.name)/'bdd'
        subprocess.run(['g++','-O3','-std=c++17',str(ROOT/'native/independent_planning_bdd.cpp'),'-o',str(cls.binary)],check=True)

    @classmethod
    def tearDownClass(cls):
        cls.work.cleanup()

    def build(self, rows, caps):
        path=Path(self.work.name)/'trace.bin'
        text=f'{len(rows[0])} {len(rows)}\n'+ ' '.join(map(str,caps))+'\n'
        text+='\n'.join(' '.join(map(str,w)) for w in zip(*rows))+'\n0\n'
        run=subprocess.run([str(self.binary),'100000',str(path)],input=text,text=True,capture_output=True)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        return path

    def test_exhaustive(self):
        rng=random.Random(20261015)
        for _ in range(120):
            n=rng.randrange(1,11);m=rng.randrange(1,6)
            rows=[[rng.randrange(8) for _ in range(n)] for _ in range(m)]
            caps=[rng.randrange(-1,sum(r)+1) for r in rows]
            path=self.build(rows,caps)
            actual=verify(path,rows,caps)['count']
            expected=sum(all(sum(w*x for w,x in zip(r,bits))<=c for r,c in zip(rows,caps))
                         for bits in itertools.product((0,1),repeat=n))
            self.assertEqual(actual,expected)

    def test_boundaries(self):
        for rows,caps,expected in [([[0]*62],[0],2**62),([[1]*3],[-1],0),([[]],[0],1)]:
            self.assertEqual(verify(self.build(rows,caps),rows,caps)['count'],expected)

    def test_malformed(self):
        rows=[[3,4,2,5,1],[2,0,5,1,4]];caps=[7,5]
        path=self.build(rows,caps);raw=path.read_bytes()
        start=16+4*len(caps)+4*sum(map(len,rows))
        records=[list(struct.unpack('<8I',raw[i:i+32])) for i in range(start,len(raw),32)]
        def reject(data):
            path.write_bytes(data)
            with self.assertRaises(InvalidCertificate):verify(path,rows,caps)
        def mutate(tag,word,value):
            changed=[r[:] for r in records]
            row=next(r for r in changed if r[0]==tag);row[word]=value(row[word]) if callable(value) else value
            reject(raw[:start]+b''.join(struct.pack('<8I',*r) for r in changed))
        mutate(1,2,2**32-1) # forward child
        mutate(1,1,5) # variable order
        mutate(1,4,lambda x:x^1) # manipulated node count
        mutate(1,3,lambda _:records[0][2]) # unreduced node
        mutate(2,3,lambda x:x+1) # false threshold capacity
        mutate(2,5,2**32-1) # missing proof dependency
        mutate(3,4,2**32-1) # intersection dependency
        mutate(3,3,1) # false reduction/result
        mutate(4,1,1) # missing first resource
        mutate(4,2,0) # wrong threshold root
        mutate(5,2,lambda x:x^1) # final count
        reject(raw[:-1]);reject(raw[:-32]);reject(raw+raw[-32:])
        reject(raw[:16]+struct.pack('<i',caps[0]+1)+raw[20:])
        # Every individual record byte bit flip is either rejected or remains
        # a semantically harmless valid certificate; none can alter the count.
        for i in range(start,len(raw)):
            data=bytearray(raw);data[i]^=1;path.write_bytes(data)
            try:result=verify(path,rows,caps)
            except InvalidCertificate:continue
            self.assertEqual(result['count'],verify_bytes_count(raw,path,rows,caps))


def verify_bytes_count(raw,path,rows,caps):
    path.write_bytes(raw)
    return verify(path,rows,caps)['count']


if __name__=='__main__':unittest.main()
