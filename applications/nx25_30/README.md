# NX25–NX30 application boundary

Exact core code is standard-library Python. The public replay is:

    python3 scripts/nx25_30_replay.py --check
    PYTHONPATH=src python3 -m unittest discover -s tests -p test_nx25_30_applications.py

The replay regenerates six exact receipts, independently checks public measured wind/scale point scores using rational normal equations, re-fits the complete exact ozone benchmark and verifies retained source/aggregate hashes.

The optional empirical_pilots.py requires NumPy. Its --wind-source argument accepts the recovered original BOS CSV or the bundled four-day subset; source row/hash metadata differ for the latter but fitted point scores agree. Its --nfl-root argument accepts an authorized private official input directory and refuses source hash mismatches. It never copies raw athlete rows into the repository. Public CI checks the frozen NFL aggregate and source integrity, not restricted raw recomputation.

PILOT_FREEZE.json records the pre-fit configuration and two source/schema amendments. This is an internally retained freeze, not an externally timestamped preregistration. source_manifest.json binds every public fixture and aggregate. R's airquality.tab and COPYING.R-datasets are separately attributed source data; their licence does not describe the new Python code.

Measured findings are deliberately narrow. ASOS point forecasts are not validated atmospheric predictions; temporal aggregation is not spatial scale transfer; daily ozone does not identify reaction constants; an identifiable movement statistic may worsen held-out prediction; robust geometry does not imply a useful scouting score.
