# NX27 — A target can close when a coarse state does not

The multiscale_transport module implements exact finite linear transfer and separately labelled measured temporal-aggregation evidence. The source graph-height series is not presented as a physical heat equation.

## The defect is a failure of commutation

For fine/coarse steps \(A_f,A_c\) and projection \(E\),
\[
D=EA_f-A_cE,\qquad e_{t+1}=A_ce_t+Dx_t.
\]
The identity \(EV=I\) for a reconstruction map \(V\) does not imply \(D=0\).
The four-cell reflecting diffusion pilot has \(A_f=I-L_{\mathrm{path}}/8\),
\[
E=\frac12\begin{pmatrix}1&1&0&0\\0&0&1&1\end{pmatrix},\quad
A_c=\begin{pmatrix}15/16&1/16\\1/16&15/16\end{pmatrix},
\]
and
\[
D=\frac1{32}\begin{pmatrix}1&-1&1&-1\\-1&1&-1&1\end{pmatrix}.
\]
At \(x=(0,1,0,0)\), projected fine evolution is \((7/16,1/16)\), while coarse evolution is \((15/32,1/32)\). Their difference is exactly \((-1/32,1/32)\). Independent cell-flux updates reproduce every matrix entry.

Total mass closes exactly: \(\mathbf1^\top A_f=\mathbf1^\top\). Pair averages do not. Thus target closure and full coarse-state closure are separate design questions. The exact_target_quotient function supplies a rational \(T\) only when \(EA_f=TE\).

## Domains and horizon bounds

For a correlated domain \(x=c+Gz,\ |z_i|\le1\), each defect component has exact range
\[
(Dc)_j\pm\sum_i |(DG)_{ji}|.
\]
Each endpoint is individually attainable. Different component extrema need not share one state. A box is the special case \(G=\operatorname{diag}(r)\). On the unit four-box the infinity-norm defect bound is \(1/8\), independently checked at all sixteen vertices.

With proved reachable-domain defect bounds \(\delta_t\) and induced coarse operator bounds \(L_t\),
\[
b_{t+1}=L_tb_t+\delta_t
\]
is a valid finite-horizon error bound by induction and the triangle inequality. The reachable_zonotopes function preserves initial generator correlations and appends independent per-step forcing generators. It does not replace one persistent disturbance by independent disturbances at every time. Tests compare actual trajectories against these enclosures, including bounded nonzero inputs.

Adding the single coordinate \(D_1x\) to the two pair averages yields an exact three-dimensional quotient:
\[
\widetilde A_c=
\begin{pmatrix}
15/16&1/16&1\\
1/16&15/16&-1\\
1/128&-1/128&5/8
\end{pmatrix}.
\]
The enriched commutation defect is zero, so the old valid positive bound improves to zero for the represented state. This does not remove physical source-model error.

For target compatibility,
\[
|J_f(x_T)-J_c(z_T)|
\le \underbrace{|J_f(x_T)-J_c(Ex_T)|}_{\text{representation mismatch}}
+L_Jb_T.
\]
The two terms are retained separately. Across three scales with \(E_{fc}=E_{mc}E_{fm}\), the exact identity is
\[
D_{fc}=E_{mc}D_{fm}+D_{mc}E_{fm}.
\]
If the direct map differs from the composed map, that discrepancy is another representation term, not a hidden reduction residual. Units and time-step labels are required; actual unit conversion belongs in the numerical map.

## Measured temporal-aggregation pilot

The recovered BOS ASOS source supplies a documented fine/coarse relationship: exact five-minute reports and nonoverlapping means of three complete reports. The frozen target is the next fifteen-minute mean. Separate scalar AR(1) models are fit on training observations only. Current/future samples do not cross the training/evaluation boundary.

| Evaluation quantity | Retained value |
|---|---:|
| Complete coarse blocks in source | 110 |
| Matched held-out target windows | 14 |
| Fine model vs measured target MAE | 0.84612 knots |
| Coarse model vs measured target MAE | 1.16476 knots |
| Coarse prediction vs fine prediction MAE | 0.72246 knots |
| Maximum current last-sample/block-mean mismatch | 2.66667 knots |

The fine prediction is a numerical reference prediction, not truth. Both predictions are also compared with the actual measured window. Only two evaluation days are represented. This is a small temporal scale-transfer benchmark, not a spatial atmospheric transfer theorem. Neither model has a validated uniform physical error bound. Public replay independently fits rational AR coefficients and checks all point metrics; raw source and aggregate hashes are retained.
