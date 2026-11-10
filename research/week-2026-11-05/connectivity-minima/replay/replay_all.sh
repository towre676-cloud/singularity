#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 verify_advance.py
python3 verify_advance.py --witnesses
if [[ "${1:-}" == "--full-search" ]]; then
  g++ -O3 -std=c++17 direct_search.cpp -o direct_search
  for n in 4 6 8 10 12 14 16 18; do
    ./direct_search "cubic${n}.g6" "search${n}.json"
  done
  python3 summarize_search.py
fi
