# PerfectJet

**An exact Math Lab: ask a question, preserve its answer, and compute what matters.**

PerfectJet connects arithmetic, observable dynamics, behavioral equivalence, operator closure and exact populations. Its local Math Lab offers **25 computed tools and a searchable atlas of 464 equations in 24 ranked families**. Start with what you want to know: recover a hidden target, explore feasible choices, choose measurements, check numerical reliability, or reveal algebraic structure. The complete earlier finite-system Observatory remains available in the same window. Python 3.10 or newer is sufficient for the core; no third-party package is required.

## Open Math Lab

After extracting the complete source archive, double-click **Start_Math_Lab.bat** on Windows or run:

```bash
python run_observatory.py
```

The launcher opens `http://127.0.0.1:8765`. Choose a question and run its example; results come from the same exact Python APIs as the command line. Editable inputs, computed geometry, scope and exported records accompany each result. The [Math Lab monograph](docs/MATH_LAB.md) explains the integrated decision workflow and recovered mathematics. Use **Finite systems** for transition graphs, original-model editing, constrained histories, adaptive experiments and remote recurrence queries; the [Observatory account](docs/OBSERVATORY.md) covers that interface.

For installed use:

```bash
python -m pip install -e .
perfectjet lab --open
```

## Complete decisions and recovered mathematics

The decision workflow checks whether measurements determine the requested values, returns a cheapest supplied sensor repair when they do not, counts every feasible original portfolio, and certifies a winner only when its lower value bound exceeds every rival upper bound. Exact ties and uncertain contenders are kept distinct. Example inputs are mathematical models with declared bounds, not live market quotes.

Recovered modules provide exact Moyal products and Hahn gates, cyclic obstruction repair, sector reach algebras, conductor transport, theta coefficients, precision repair, weighted path bounds, branch-channel scheduling, analytic replacements and algebraic partners. The signed Pell asymptotic normalization is corrected. All previous research remains in its existing directories. The original 417 equation IDs retain their meanings; new IDs begin at PJ-E418.

```bash
perfectjet math-lab --lab pipeline
perfectjet math-lab --lab precision
perfectjet math-lab --request examples/mathlab/hahn.json
perfectjet math-lab --all --output results/mathlab/all-examples.json
```

## One system, several sufficient representations

The finite-field interferometer uses two noncommuting shears and the sensor `q = u² + v² mod 13`. Hidden translation and sign symmetries reduce **2,197 absolute phase states to 85 behavior classes**. Different questions admit different linear representations: **57** coordinates preserve numeric sensor and acceptance outputs under every ordered action word; **15** preserve ordered accepted-word outputs; **8** describe the global length-count Krylov space. For the designated start, the scalar generating function has denominator degree **7**. Each dimension has a separate preservation contract.

The retained example has **76,712,911,076,419,434** legal histories of length 80. At length `10**100`, its population modulo `1_000_000_007` is **976449876**, independently reproduced by modular matrix powering. These are exact finite-system calculations. They do not claim a new general theorem or universal speed advantage.

The branching laboratory identifies a hidden target in two actions although no fixed action schedule can guarantee identification. The irreversible laboratory shows why a cheaper reset can destroy the answer: prefix-conditioned planning preserves the initial target and all earlier sensor readings. The Pell laboratory transports a supplied integer unit orbit into a complete finite residue cycle and retains the route to remote original orbit coordinates.

## Use the same engine from Python or JSON

```python
from perfectjet.observatory import compile_system, HistoryPopulation, compile_series
from perfectjet.observatory.examples import arithmetic_interferometer

source = arithmetic_interferometer(13, lifted=True)
compiled = compile_system(source)
population = HistoryPopulation(compiled.system, horizon=80)
print(population.count())
print(population.unrank(10**12))
series = compile_series(compiled.system)
print(series.coefficient(10**100, modulus=1_000_000_007))
```

`perfectjet observe request.json --output answer.json` accepts the same requests as the workbench. A request contains an `operation`, a complete `model`, and query fields. Operations include `compile`, `history`, `pair`, `adaptive`, `closure`, `series` and `pell-point`. The model format includes states, action names and costs, partial transitions, sensor labels, initial target labels, acceptance and the initial state.

## Explore the wider mathematical atlas

The [master monograph](docs/MONOGRAPH.md), [equation atlas](docs/EQUATION_ATLAS.md), [topic map](docs/COVERAGE_MAP.md) and preserved [archival sources](archive/README.md) contain the larger PerfectPower, DynaComp, PSG, SOE, WIND, IMP, Morphonic, conductor, Shadow–Core and Weyl programs. The runnable kernels include exact integer lattices and saturation, polynomial observable closure, one- and several-parameter rank loci, binary-sextic partners and Clebsch invariants, solution-carrying quadratic/Pell populations, cyclotomic coefficients, readout identifiability and deformation obstructions. Existing application research remains preserved in its own directories.

```bash
perfectjet engine
perfectjet lattice
perfectjet quadratic
perfectjet invariants
perfectjet surface
perfectjet strata
perfectjet collision --conductor 7 --index 100000000000000000000000000000000000000000000000000
```

PerfectJet complements [PerfectPower](https://github.com/towre676-cloud/perfectpower) and [DynaComp](https://github.com/towre676-cloud/DynaComp). It does not automatically modify their code or deployments. The Observatory is the executable integration layer for finite systems; infinite arithmetic completeness and unrestricted nonlinear closure retain their own mathematical obligations.

## Reproduce and extend

```bash
PYTHONPATH=src python -m unittest discover -s tests -p 'test_observatory*.py' -v
PYTHONPATH=src python scripts/benchmark_observatory.py
python scripts/check_coverage.py
python scripts/build_release.py
```

The [benchmark receipt](results/observatory/benchmark.json) preserves independent absolute/relative/sign-orbit counts, complete short-word enumeration, original-coordinate rank round trips, operator bases, the remote modular comparison and the adaptive-versus-fixed experiment. [Pell transport](results/observatory/pell.json) and [destructive-prefix calculations](results/observatory/destructive-prefix.json) are retained separately. [Validation](docs/OBSERVATORY_VALIDATION.md) states executed checks and interface verification limits.

The [complete source archive](https://github.com/towre676-cloud/PerfectJet/archive/refs/heads/main.zip) follows `main`. The release builder makes a deterministic ZIP with a SHA256 manifest and creates split parts if needed. The current release is **0.15.0**. Computational identities, independent checks, historical claims and open proposals remain distinct; this release does not add Lean proofs.

## Sextic research integration — v0.17.0

PR #2's incidence and modular engines are integrated with the v0.16.0 Math Lab and all 450 original equation records. The catalogue now has 464 unique entries across the same 24 families. The partners tool computes exact supplied-form kernels through degree 20, with activity checked separately. Global classifications retain their optional external-solver assumptions; degrees 21 and above remain open. See [partner incidence](docs/PARTNER_INCIDENCE.md), [integration record](docs/SEXTIC_INTEGRATION.md), and the [monograph](docs/MONOGRAPH.md).
