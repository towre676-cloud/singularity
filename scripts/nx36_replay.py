#!/usr/bin/env python3
"""Replay all NX36 retained acceptance fixtures, without network access.

Actual marked period-loop continuation is an additional slower check. Measured
NFL rows stay private: its public replay checks frozen aggregate/provenance
evidence and exact structural examples, not hidden raw observations.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = (
    'candidate_box_thermal', 'joint_thermal', 'fault_population_diagnostics',
    'thermal_severity', 'adaptive_thermal', 'history_thermal',
    'nx_decision_recovery', 'target_recovery', 'horizon_design',
    'typed_contexts', 'parameter_module_receipts', 'realizable_interfaces',
    'incremental_locality', 'fault_transport', 'recovery_metrics',
    'integer_quotients', 'arithmetic_automata', 'symmetry_channels',
    'phase_probes', 'population_geometry', 'prefix_certificates',
    'nx25_30_replay', 'nx_analytic_decisions',
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', required=True,
                        help='compare retained evidence; never rewrite fixtures')
    parser.add_argument('--slow', action='store_true',
                        help='also replay both marked Legendre continuation paths')
    parser.add_argument('--log-directory', type=Path,
                        default=ROOT / 'tmp/nx36-validation/receipts')
    args = parser.parse_args()
    args.log_directory.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ)
    env['PYTHONPATH'] = str(ROOT / 'src')
    records = []
    for name in SCRIPTS:
        command = [sys.executable, str(ROOT / 'scripts' / (name + '.py')), '--check']
        if name == 'nx_analytic_decisions' and args.slow:
            command.append('--slow')
        result = subprocess.run(command, cwd=ROOT, env=env, text=True,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        log = args.log_directory / (name + '.log')
        log.write_text(result.stdout)
        records.append({'script': name, 'exit_code': result.returncode})
        print(name + ': ' + ('passed' if result.returncode == 0 else 'FAILED'), flush=True)
        if result.returncode:
            print(result.stdout[-8000:])
            raise SystemExit(result.returncode)
    report = {'schema': 'singularity.nx36-replay/1', 'checks': records,
              'period_loop_continuation_replayed': args.slow,
              'network_required': False,
              'empirical_nfl': 'aggregate/provenance replay; restricted raw rerun excluded'}
    (args.log_directory / 'summary.json').write_text(
        json.dumps(report, indent=2, sort_keys=True) + '\n')
    print('All ' + str(len(records)) + ' NX36 receipt routes passed.')


if __name__ == '__main__':
    main()
