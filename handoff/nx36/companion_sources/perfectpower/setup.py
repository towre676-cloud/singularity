"""Build an installed package with the same runtime evidence as a checkout."""
from pathlib import Path
import hashlib
import json
from setuptools import setup
from setuptools.command.build_py import build_py

ROOT=Path(__file__).resolve().parent
RECEIPTS=(
    'mordell_registry.json','plan_certificates.json','oeis_auto.json',
    'mordell_branch.json','thue_graph.json',
    'm22_interactions/nonet_higgs_exact_loop_algebra.json',
    'industrial_replication_summary_20261008.json',
    'polynomial_population_queries.json',
    'global_population_queries.json',
    'extended_population_queries.json',
    'family_population_queries.json',
    'mordell_descent_atlas.json',
    'mordell_parity_atlas.json',
    'orbit_reduction_queries.json',
    'new_work_lean/verification.json',
    'descent_bridges/verification.json',
    'descent_bridges/instances.json',
    'isogeny_point_groups/verification.json',
    'period_bridge/summary.json',
    'period_bridge/results.json',
    'period_bridge_deep/summary.json',
    'period_bridge_deep/results.json',
    'period_bridge_deep/e8_lift.json',
    'period_bridge_deep/observability.json',
    'period_bridge_deep/coxeter.json',
    'period_bridge_deep/dirichlet.json',
    'period_bridge_deep/atlas.json',
)


def assets():
    for folder in ('certs','data','research/dresden','native'):
        for path in sorted((ROOT/folder).rglob('*')):
            if path.is_file() and '__pycache__' not in path.parts:
                yield path
    yield from sorted((ROOT/'PerfectPower').rglob('*.lean'))
    for name in RECEIPTS:yield ROOT/'receipts'/name
    for name in ('python/make_mordell_registry.py',
                 'web/room-of-possibilities/PerfectPower-Room-of-Possibilities.html',
                 'web/budget-lab/index.html',
                 'contracts/current_frontier.json','contracts/release_features.json'):
        yield ROOT/name


class RuntimeBuild(build_py):
    def run(self):
        super().run()
        destination=Path(self.build_lib)/'perfectpower/_assets'
        manifest={}
        for source in assets():
            relative=source.relative_to(ROOT)
            target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
            self.copy_file(str(source),str(target))
            manifest[relative.as_posix()]=hashlib.sha256(source.read_bytes()).hexdigest()
        (destination/'runtime_manifest.json').write_text(json.dumps(manifest,sort_keys=True),encoding='utf-8')


setup(cmdclass={'build_py':RuntimeBuild})
