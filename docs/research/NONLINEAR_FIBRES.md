# NX26 — Ambiguity, curvature and finite witness repairs

The nonlinear_fibres module implements bounded rational polynomial witnesses, not a complete semialgebraic optimizer. Limits are four variables, degree four and 32 monomials per polynomial. Domains contain finite rational boxes and original polynomial equalities/inequalities. Every witness is substituted into those original constraints.

## A pair proves a lower bound

For compact \(D\), observations \(H\), constraints \(C=0\), and target \(T\),
\[
\mathcal F_y=\{x\in D:H(x)=y,\ C(x)=0\},\qquad
A_T(y)=\sup_{x,x'\in\mathcal F_y}|T(x)-T(x')|.
\]
A verified pair proves a target-diameter lower bound. It normally does not prove the diameter. Receipts keep target_gap, diameter_lower_bound and complete_diameter separate. A zero observational residual means exact rational equality.

For \(H(x_1,x_2)=x_1,\ T=x_2^2,\ D=[-1,1]^2\), states \((0,0),(0,1)\) have gap one even though the target gradient at the origin is zero. This special diameter is exactly one because \(0\le x_2^2\le1\), with both endpoints attained. The elementary upper bound is recorded separately; the generic witness verifier does not infer it.

For \(H(x)=x^2,\ T(x)=x,\ D=[-1,1]\), states \(-1,1\) share observation one and have gap two. Observation derivatives are nonzero at both states. Local invertibility therefore does not settle a global branch.

## Exact quadratic constancy

Let \(x=x_0+Nz\) and \(T(x)=g^\top x+\frac12x^\top Qx\). Symmetrize \(Q\), which preserves the polynomial. Substitution gives
\[
T(x_0+Nz)=T(x_0)+z^\top N^\top(g+Qx_0)+\tfrac12z^\top N^\top QNz.
\]
On a parameter domain containing a relatively open neighbourhood, constancy is equivalent to
\[
N^\top(g+Qx_0)=0,\qquad N^\top QN=0.
\]
Necessity follows because a polynomial vanishing on an open set has zero coefficients; sufficiency is immediate. A finite admissible set can make a nonzero polynomial accidentally constant, so a failed criterion without the open-domain hypothesis returns domain_analysis_required. Independent tests directly expand substituted polynomials and compare coefficients.

## Curvature belongs to the fibre too

Write \(K=(H-y,C)\). Along a constraint-preserving curve with tangent \(n\) and acceleration \(a\),
\[
DK\,n=0,\qquad DK\,a+\big(n^\top\nabla^2K_i\,n\big)_i=0.
\]
At a regular stationary point, \(DT=\lambda^\top DK\), so
\[
\frac{d^2}{ds^2}T(x(s))\big|_0
=n^\top\left(\nabla^2T-\sum_i\lambda_i\nabla^2K_i\right)n.
\]
The code checks the point lies on the original constraints, verifies Jacobian rank and tangency, solves the multiplier identity, and supplies a compatible acceleration. Singular points are refused as singular_stratum; regular nonstationary points are not forced into a stationary Hessian formula.

| Fibre and target | Ambient target Hessian | Correct intrinsic variation |
|---|---|---|
| \(y-x^2=0,\ T=y,\ (x,y)=(0,0), n=(1,0)\) | zero | \(2\) |
| \(x^2+y^2=1,\ T=x,\ (x,y)=(1,0), n=(0,1)\) | zero | \(-1\) |
| Same circle, rational charts with tangents \((0,\pm2)\) | zero | \(-4\) in either chart parameter |

Direct parametrization \(T(s,s^2)=s^2\) proves the parabola result independently. The two circle charts
\[
(x,y)=\left(\frac{1-u^2}{1+u^2},\frac{\pm2u}{1+u^2}\right)
\]
obey \((1+u^2)(T(u)-1)=-2u^2\), giving second derivative \(-4\). Parameter scaling matters, so tangent vectors stay in the receipt.

## Finite coverage is not a global theorem

A sensor \(S\) with deterministic radius \(\epsilon\) separates a witness pair only when
\[
|S(x)-S(x')|>2\epsilon.
\]
The finite optimizer enumerates at most six sensors and 256 retained pairs. It returns the least declared cost and explicitly says its scope is retained finite pairs only.

With old observation \(x^2+y^2=1\) and target \(x+y\), sensor \(x\) repairs \((-1,0),(1,0)\). Yet \((0,-1),(0,1)\) still share the old observation and the repair reading while their target gap is two. Removing every sampled witness can leave an unseen branch. This is retained as a permanent regression.

No interval subdivision, numerical candidate finder or general diameter solver is claimed. The synthetic bounded pilot implements affine constancy, exact global branch witnesses, curvature-aware regular analysis and a finite repair whose global limitation is demonstrated.
