"""Fault injection for complete, sealed training evidence."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

try:
    import torch
except ImportError:
    torch = None


@unittest.skipIf(torch is None, 'optional training tests require PyTorch')
class TrainingLogPersistenceTests(unittest.TestCase):
    def test_sealing_recovers_records_dropped_by_the_progress_stream(self):
        from singularity.training.runner import run
        original_open = Path.open

        class DroppedWrites:
            def __init__(self, handle): self.handle, self.writes = handle, 0
            def __enter__(self): return self
            def write(self, text):
                self.writes += 1
                if self.writes == 1: self.handle.write(text)
                return len(text)
            def flush(self): self.handle.flush()
            def __exit__(self, *args): self.handle.close()

        def opened(path, mode='r', *args, **kwargs):
            handle = original_open(path, mode, *args, **kwargs)
            return DroppedWrites(handle) if path.name == 'metrics.jsonl' and mode == 'w' else handle

        cfg = {'task':'modular_addition','p':7,'seed':83,
            'split':{'train_orbits_per_label':2,'tune_orbits_per_label':1,'test_orbits_per_label':1},
            'model':{'name':'mlp','hidden':8},'steps':5,'batch_size':8,
            'eval_every':5,'evaluate_test':False,'threads':1}
        with tempfile.TemporaryDirectory() as folder, patch.object(Path, 'open', opened):
            result = run(cfg, folder)
            raw = (Path(folder)/'metrics.jsonl').read_bytes()
            rows = [json.loads(line) for line in raw.splitlines()]
            self.assertEqual([row['step'] for row in rows], [1,2,3,4,5])
            self.assertEqual(hashlib.sha256(raw).hexdigest(), result['metrics_sha256'])
            self.assertEqual(result['optimizer_updates'], 5)
            self.assertFalse(list(Path(folder).glob('.metrics.final.*')))


if __name__ == '__main__':
    unittest.main()
