#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
run_dir="$(mktemp -d ./replay_run.XXXXXX)"
cp *.py *.g6 *.cpp requirements.txt "$run_dir/"
cp vol8_law.json defect_certificate.json pure20_fixture.json "$run_dir/"
cd "$run_dir"
python3 vol9_build.py
python3 vol9_connectivity.py
python3 vol9_reader.py
python3 check_automorphisms.py
g++ -O3 -std=c++17 direct9.cpp -o direct9
./direct9 hosts.g6 direct9.json
python3 vol9_verify_hosts.py
python3 vol9_witnesses.py
python3 vol9_girth.py
python3 check_high_girth_law.py
python3 check_pure20.py
python3 vol10_build.py
g++ -O3 -std=c++17 direct10.cpp -o direct10
./direct10 hosts.g6 direct10.json
python3 vol10_certify.py
python3 vol10_reader.py
python3 check_automorphisms10.py
python3 vol10_witnesses.py
python3 reservoir.py
python3 class_readers.py
python3 verify_saved.py
printf 'Fresh outputs: %s\n' "$PWD"
