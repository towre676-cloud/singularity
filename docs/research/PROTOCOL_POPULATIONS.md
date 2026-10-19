# Complete constrained protocol populations (NX12)

A physical protocol consists of an original chronological symbol word and a terminal sensor identity. Different words or sensors remain different original experiments even if their readings coincide. The completion compiler compresses counting, not identity or multiplicity.

A deterministic finite automaton supplies states \(q\), start \(q_0\), transition \(\delta\) and accepting states. Each symbol has a physical scalar amplitude, strictly positive rational elapsed/action cost and nonnegative integer resource increments. A sensor has its own cost and installation requirements. The protocol budget also includes reset cost, a finite horizon and a switch limit. The first symbol does not count as a switch.

## Completion theorem

Scale every rational price by their exact common denominator \(D\), refusing a declared scale budget if necessary. A completion state is

\[
\sigma=(q,B,\mathbf b,h,a_{\rm last},s,\ell),
\]

where \(B\) is remaining scaled cost, \(\mathbf b\) remaining resources, \(h\) remaining horizon, \(s\) remaining switches and \(\ell\) elapsed length. For each feasible symbol, consume its actual resources and one horizon step. The terminal contribution counts legal installed sensors only when the grammar accepts and the empty/nonempty convention permits termination:

\[
C(\sigma)=t(\sigma)+\sum_{a:\text{feasible}}C(\sigma\cdot a).
\]

Induction on \(h\) proves the count. Every word has exactly one DFA path; rejecting duplicate \((q,a)\) transitions prevents counting ambiguous derivations as separate words. Missing transitions make words illegal. Strictly positive symbol cost and finite horizon exclude zero-cost cycles. Zero heater amplitude still consumes one positive-cost elapsed step.

Ranking uses a fixed order: legal terminal sensors in input order, followed by symbol branches in alphabet order. Each branch owns a consecutive interval of completion ranks. Descending the unique interval proves `rank(unrank(i))=i`; summing earlier intervals proves the converse for every legal original protocol. Conditioning on a prefix changes only the completion start state. Conditioning on terminal sensor restricts the terminal term, without deduplicating words.

The number of reachable dynamic states depends on the numeric resource and scaled-cost ranges. Complexity is pseudo-polynomial, not polynomial in arbitrary budget bit length. Explicit materialization checks the exact root count before producing at most the requested number of members. A resource refusal does not imply an empty scientific population.

## Independent tiny acceptance

Alphabet amplitudes are zero and two. Nonempty words have length at most three, total amplitude at most four and at most one adjacent switch. The legal words are two of length one, four of length two and five of length three, eleven in total. Two terminal sensors yield **22 experiments**. Reset one, elapsed cost one, heat charge half the amplitude and sensor cost one give only the words 0, 2 and 00 at total cost four, hence **six experiments**. Independent Cartesian-product tests enumerate all words and sensors without using completion recursion, check every rank, and compare twenty randomized tiny deterministic grammars.

## Physical adapter and exact complete search

The protocol adapter maps symbol IDs to physical amplitudes explicitly. A sensor subset requires an explicit map to the original model's sensor channels; filtering the sensor catalogue must not silently rename a center sensor as channel zero. Each protocol is separately reset. Every output in the retained bounded 4-by-4 population is compared with a conservative neighbour-flux update independent of the production simulator.

A short complete population is passed to the existing exact panel backend and independently enumerated panel oracle. The larger bounded language retains protocols omitted by a matching-horizon step/pulse/alternating subset. That comparison does not alter or relabel the original 112-experiment baseline.

For the cheapest robust scalar observation, sort all legal original experiments by exact total price and rank. Evaluate in that order. A failed experiment retains a concrete target pair whose closed reading intervals overlap. The first feasible price is minimal because every cheaper original protocol has been explicitly excluded. All protocols tied at that price are checked. Once price exceeds the incumbent, later sorted protocols cannot improve it. This cost bound is the only search pruning rule; nominal linear dependence and duplicate nominal readings are not used as robust pruning justifications.

The search still reports the complete root population count. It may conclude that no scalar terminal reading distinguishes every requested target pair; that is distinct from a panel or adaptive-policy impossibility. The initial demonstration uses the named nominal/heater-half pair, plus a complete short panel comparison.

## Portable completion evidence

The `singularity.protocol-population/1` certificate includes the alphabet, DFA, resources, installed sensors, exact scale, root state/count and the reachable completion DAG. Every edge decreases horizon. A local checker verifies each terminal count and sum-of-children equation, so hashes are not substituted for arithmetic proof. Rank witnesses reconstruct original words and sensor identities. Grammar counting establishes population completeness; a separate source binding and output replay establish physical readings.

Run `python scripts/nx_decision_recovery.py --track NX12 --check` and `python -m unittest tests.test_protocol_population`.

The fair retained comparison uses the nominal/heater-half pair, the same radius \(1/1000\), the same grammar/resources/costs and the same allowed terminal sensors. The complete population has 108 original experiments, versus 28 in the matching step/pulse/alternating subset. Both the cheapest robust scalar experiment and the exact finite panel optimum cost three in this instance. Completeness adds 80 legal original protocols without improving this optimum. The short independent exhaustive panel check remains separate from this larger exact backend comparison.
