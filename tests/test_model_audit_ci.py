"""CI trust boundary, independent subset oracle and real local HF execution."""
import copy
import io
import itertools
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from singularity.model_audit import build_package, package_digest
from singularity.model_audit.ci import evaluate, main, read_json, replay, validate_package, write_json


def fixture():
    probes = [{"id": str(i), "text": str(i), "cost": c} for i,c in enumerate([4,1,1,3])]
    good = {"argmax": [1], "top_logprob": [-.1]}
    bad = {"argmax": [2], "top_logprob": [-.8]}
    reference = [good]*4
    package = build_package(probes, reference, [reference],
       {"a": [bad,bad,good,bad], "b": [bad,good,bad,bad]}, contract={"test": 1}, requirement=2)
    return package, good, bad


class BoundaryTests(unittest.TestCase):
    def test_minimum_cost_against_independent_exhaustive_oracle(self):
        package, _, _ = fixture()
        costs = [4,1,1,3]
        covers = [{0,1,3}, {0,2,3}]
        oracle = min(sum(costs[i] for i in subset)
            for k in range(5) for subset in itertools.combinations(range(4), k)
            if all(len(set(subset)&cover) >= 2 for cover in covers))
        self.assertEqual(oracle, sum(p['cost'] for p in package['probes']))
        self.assertTrue(validate_package(package, package['package_sha256'])['verified'])

    def test_externally_pinned_digest_and_corrupt_fault_flags(self):
        package, _, _ = fixture()
        changed = copy.deepcopy(package)
        changed['metadata']['edited'] = True
        changed['package_sha256'] = package_digest(changed)
        with self.assertRaises(ValueError):
            validate_package(changed, package['package_sha256'])
        changed = copy.deepcopy(package)
        changed['fault_evidence']['a']['1']['flags'] = False
        changed['package_sha256'] = package_digest(changed)
        with self.assertRaises(ValueError):
            validate_package(changed, changed['package_sha256'])

    def test_missing_guarantee_and_identity_changes(self):
        package, good, bad = fixture()
        observe = lambda probes: [good]*len(probes)
        self.assertEqual(evaluate(package, observe, {'test':1})[2], 'pass')
        self.assertEqual(evaluate(package, observe, {'test':2})[2], 'changed')
        self.assertEqual(evaluate(package, observe, {'test':1}, ['1'])[2], 'pass')
        self.assertEqual(evaluate(package, observe, {'test':1}, ['1','2'])[2], 'incomplete')
        report, _, status = evaluate(package, lambda probes: [bad]*len(probes), {'test':1}, ['1'])
        self.assertEqual(status, 'changed')
        with self.assertRaises(ValueError):
            evaluate(package, lambda probes: [], {'test':1})

    def test_failure_writes_diagnostics_before_model_loading(self):
        package, _, _ = fixture()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_json(root/'package.json', package)
            out = root/'out'
            out.mkdir()
            (out/'observations.json').write_text('stale')
            with patch('singularity.model_audit.ci.hf_adapter') as loader, redirect_stdout(io.StringIO()):
                code = main(['check','--package',str(root/'package.json'), '--model','absent',
                    '--execution','absent','--expected-package-sha256','0'*64,'--output',str(out)])
            loader.assert_not_called()
            self.assertEqual(code,1)
            self.assertEqual(read_json(out/'report.json')['status'],'error')
            self.assertFalse((out/'observations.json').exists())
            self.assertTrue((out/'report.md').exists())

    def test_model_free_replay_detects_changed_observations(self):
        package, good, bad = fixture()
        report, rows, status = evaluate(package, lambda probes:[good]*len(probes), {'test':1})
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write_json(root/'certificate.json', package)
            write_json(root/'observations.json', rows)
            write_json(root/'report.json', {'check':report,'status':status,'deployed_contract':{'test':1},
                        'expected_package_sha256':package['package_sha256']})
            self.assertTrue(replay(root,package['package_sha256'])['replayed'])
            rows[0]=bad
            write_json(root/'observations.json', rows)
            with self.assertRaises(ValueError):
                replay(root,package['package_sha256'])


try:
    import torch, transformers
    HF = True
except ImportError:
    HF = False


@unittest.skipUnless(HF, 'optional pretrained dependencies unavailable')
class LocalHFIntegration(unittest.TestCase):
    def test_fresh_process_pass_and_fault_and_replay(self):
        import importlib.util
        import os
        import subprocess
        import sys
        root = Path(__file__).resolve().parents[1]
        spec = importlib.util.spec_from_file_location('create_reference',root/'examples/model_audit/create_reference.py')
        example = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(example)
        with tempfile.TemporaryDirectory() as d:
            directory = Path(d)
            model = directory/'model'
            reference = directory/'ref'
            package = example.create(model, reference, tiny=True)
            args = [sys.executable,'-m','singularity.model_audit.ci','check','--model',str(model),
                '--package',str(reference/'reference.json'),'--execution',str(reference/'execution.json'),
                '--expected-package-sha256',package['package_sha256'],'--output',str(directory/'healthy')]
            env = dict(os.environ, OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
            healthy = subprocess.run(args, capture_output=True, text=True, env=env, timeout=90)
            self.assertEqual(healthy.returncode,0,healthy.stdout+healthy.stderr)
            self.assertTrue(replay(directory/'healthy',package['package_sha256'])['replayed'])
            # Keep file/config identity fixed while perturbing actual runtime behavior:
            # use a direct adapter to exercise the declared temperature fault.
            from singularity.model_audit.ci import hf_adapter
            from singularity.model_audit.adapters import HuggingFaceCausalAdapter
            from singularity.model_audit import settings_from_contract
            adapter = hf_adapter(model,None,package,read_json(reference/'execution.json'))
            settings = settings_from_contract(package['contract'])
            settings['temperature']=1.3
            fault = HuggingFaceCausalAdapter(adapter.model,adapter.tokenizer,
                provenance=package['contract']['checkpoint_provenance'], declared_contract=package['contract'], **settings)
            self.assertEqual(evaluate(package,fault.observe,fault.contract())[2],'changed')
            # A deployment weight replacement must also fail the public CLI.
            with torch.no_grad():
                adapter.model.transformer.wte.weight[0].add_(1)
            adapter.model.save_pretrained(model)
            args[-1]=str(directory/'fault')
            changed = subprocess.run(args,capture_output=True,text=True,env=env,timeout=90)
            self.assertEqual(changed.returncode,1,changed.stdout+changed.stderr)
            result = read_json(directory/'fault/report.json')
            self.assertEqual(result['status'],'changed')
            self.assertTrue(any(m['key']=='checkpoint_provenance' for m in result['check']['contract_mismatches']))
            self.assertTrue(replay(directory/'fault',package['package_sha256'])['replayed'])


if __name__ == '__main__':
    unittest.main()
