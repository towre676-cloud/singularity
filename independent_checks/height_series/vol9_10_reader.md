# Exact volume-nine and volume-ten readers

For finite simple cubic graphs, supply coefficientwise agreement in the full
height-series polynomials at all lower volumes. The first differing coefficient
of the height series equals the first differing coefficient of its formal
logarithm because the series has constant term 1. The reader uses the existing
volume-eight input schema and returns **B − A**. Negate the recovered research
witness differences before comparing them with this output.

| Volume | Mode | Degrees of the observed coefficients | Coordinates |
| --- | --- | --- | --- |
| 9 | General | 1, 3, …, 19 | 10 research coordinates |
| 9 | Connected | 1, 3, …, 19 | 10 measured coefficients |
| 10 | General | 0, 2, …, 26 | 14 research coordinates |
| 10 | Connected | 2, 4, …, 24 | 12 measured coefficients |

The general matrices in the recovered basis have determinants −6 and 40.
Connected mode uses polynomials normalized on the listed coefficient panel, so
its matrices in that basis are identities. General coordinate values can be
rational even when the full difference polynomial is integral.

## Complete calculations

```bash
python independent_checks/height_series/vol9_10_reader.py 10 pair.json --mode connected
```

The JSON object holds calculation records under `A` and `B`. Each record uses
`schema: singularity.height-calculation.v1`, `graph_class: finite_simple_cubic`,
and `q_convention: vol8_lib`. Use `kind: height` with every volume from 0 through
the requested volume or `kind: log` with every volume from 1 through the requested
volume. Coefficient dictionaries map canonical nonnegative degree strings to
integers or exact rational strings. Missing degrees inside a supplied volume
mean zero. Connected mode requires `connected: true` and a `graph` object with
`n` and a simple cubic edge list on vertices numbered from 0 through `n-1`.

`extract(volume, a, b, mode=...)` checks full lower agreement and reconstructs
every target degree. It checks topology in connected mode, energy parity and
bounds, population totals, and whether supplied log records exponentiate to
nonnegative integer populations. For compatible connected graphs of order at
most the target volume, it also requires a zero target difference. The
certificate is conditional on the supplied records having been calculated
correctly for the stated graphs.

## Panel observations

`reconstruct(volume, observations, mode=...)` takes exact B − A coefficients in
the order in the table. It returns the full polynomial and coordinates as
rational strings. Applicability and lower agreement are caller assumptions for
this entry point.

The compact model is derived from the exact coefficient functions in the
general readers and the connectivity-one entries of the class readers at
research commit `25b212a5ba9ab02f74d8a8b7ff37d9ad8f47d3f5`. Exact quotient
checks cover all coefficient degrees. The general and connected observation
counts are minima for fixed rational linear observations uniformly on the
respective unbounded classes. [Recovered theorem and certificates](https://github.com/towre676-cloud/singularity/tree/25b212a5ba9ab02f74d8a8b7ff37d9ad8f47d3f5/research/week-2026-11-05/volumes9-10).
