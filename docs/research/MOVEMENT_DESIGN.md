# NX29 — Identify the requested capability, then test whether it predicts

The exact movement_design module treats a declared bilinear response model. Its optional measured NFL pilot tests predictive usefulness separately. Identification, extraction stability and prediction are not interchangeable.

## Target-specific design

With normalized conditions \(s,a\),
\[
\eta(s,a)=\beta_0+\beta_1s+\beta_2a+\beta_3sa,\qquad
\phi(s,a)=(1,s,a,sa).
\]
The requested capability is a row \(h^\top\beta\), possibly obtained from an externally defined demand distribution. For observations \(r=X_D\beta+e\),
\[
h\in\operatorname{row}(X_D)
\quad\Longleftrightarrow\quad
\ker X_D\subseteq\ker h^\top.
\]
A full profile rank requirement is unnecessary when the target uses only a known direction. Conversely, repeated rows do not reveal a missing interaction.

At conditions \((0,0),(1,0),(0,1)\), the invisible coefficient direction is \(n=(0,0,0,1)\). Direct polynomial substitution proves \(X_Dn=0\), while target \((1,1)\) has \(h^\top n=1\). Adding that fourth condition gives determinant one and identifies all coefficients. The restricted target \((1,1,0,0)\) is already identifiable from the original design.

For deterministic measurement box radii \(\epsilon_i\), a decoder satisfying \(X_D^\top w=h\) has attained error radius \(\sum_i|w_i|\epsilon_i\). The minimum_drill_repair function supports original measurement radii, candidate admissibility, costs and a finite error cap. It returns new drill names separately from the full estimator sensor order. As in NX25, its affine offset and raw-reading contract must be preserved.

| Repair type | Structural rank | Error statement |
|---|---|---|
| Repeat an existing condition | unchanged | Requires an explicit dependence model |
| New interaction condition | can increase | Target-specific decoder and box bound replay |
| Full rank but weakly scaled condition | sufficient noiselessly | May amplify noise badly |
| Missing normalization or response definition | rejected | Units and model meaning cannot be inferred |

The retained repeat model is independent symmetric two-point error, for which mean variance is \(\epsilon^2/k\). Its adversarial worst-case radius stays \(\epsilon\). Persistent calibration bias would not gain the same variance reduction. The API does not turn repeated bounded-error samples into unjustified \(1/\sqrt{k}\) worst-case bounds.

## Recovered official data and honest negative prediction

The actual restricted NFL source archives were recovered from the user's backups. Four consumed files match the pinned PerfectJet official adapter hashes exactly: combine results, combine tracking, games and player-play outcomes. Unused game tracking files are not ingested. Raw athlete trajectories, linked individual outputs and private fitted rows remain outside the public repository.

The public source manifest records the owned archive identities, source hashes, official adapter revision and ingestion boundary. The join uses the official nfl_id namespace exactly; recruiting identifiers are not guessed to match numerically. Event and attempt identifiers remain distinct. Nullified plays and unknown/missing outcomes are excluded explicitly.

The pre-fit pilot selects ten eligible athletes in the 2023 combine cohort and ten in 2024. The former train; the latter evaluate. No athlete crosses folds through another attempt. The frozen external outcome is mean non-nullified player_get_off from games in or after the draft season. All compared models use the same twenty athletes. This is a small selected sample, not a cohort-wide population estimate.

For each athlete, the bilinear response uses raw measured acceleration, fixed speed normalization \(s/10\), and a declared turning increment normalized by 180 degrees. The target condition is \((1/2,1/2)\). Exact reported-decimal row checks verify target identifiability; numerical least squares estimates the coefficients. Residual size is empirical model mismatch, not a certified measurement-error radius. No claim identifies the fitted score with intrinsic athletic ability.

| Model | Held-out MSE |
|---|---:|
| Conventional combine measurements | 0.0457271 |
| Conventional plus identified capability estimate | 0.0745024 |
| Conventional plus residual-adjusted capability | 0.0690224 |

Conventional fields are forty, vertical, broad jump and combine weight. Standardization uses training data only; ridge penalty one is fixed rather than tuned on evaluation players. The added capability worsens this frozen task. A formally identifiable statistic can add no predictive value, and the negative result is retained.

The receipt also reports training-residual interval radii, held-out coverage and descriptive player bootstrap intervals. Those are empirical diagnostics, not distribution-free guarantees. The earlier historical 93.2-percent rank statistic is not reused on this new population. Likewise the historical predictive deterioration is context, not a substitute for the newly computed values.

## Replay scope

Exact algebra and independent direct-substitution/repair tests run without athlete data. Public CI verifies restricted-source hash declarations and frozen aggregate integrity; it does not reconstruct restricted raw rows. Authorized owners can rerun the optional empirical_pilots.py with their private input directory. The original execution consumed real measurements and independently recorded game outcomes; publishing only aggregates does not relabel them as synthetic.
