from pathlib import Path
import subprocess,sys
ROOT=Path(__file__).resolve().parent
scripts=['imbalance_correction.py','moment_certificates.py','short_spine.py','partial_decontamination.py','family_base.py','family_symbolic.py','verify.py','low_volume_symbolic.py','verify_low_volume.py','two_parameter_base.py','two_parameter_volume.py','two_parameter_verify.py','certify_factorization.py']
for script in scripts:
    print('Running',script,flush=True)
    subprocess.run([sys.executable,str(ROOT/script)],check=True,cwd=ROOT)
print('All exact checks passed.',flush=True)
(ROOT/'REPLAY_STATUS.json').write_text(__import__('json').dumps({'completed':True,'scripts':scripts,'arithmetic':'exact integers and rational polynomials','terminal_status':'All exact checks passed.'},indent=2)+'\n')
