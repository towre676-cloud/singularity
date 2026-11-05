# Uniform window law and later promotions: exact reductions

## The window law is a jet-injectivity theorem

Let W be the new polynomial space at volume V, of dimension d, and suppose parity and vanishing give P=q^e0 (t-1)^V U(t), t=q^2. Let U_W be the resulting d-dimensional subspace of polynomials. Multiplication by (t-1)^V is lower triangular in the coefficients at t=0 with nonzero diagonal. Consequently the consecutive window e0,e0+2,...,e0+2(d-1) is sufficient if and only if

U_W -> K[t]/(t^d)

is injective. Equivalently U_W intersects t^d K[t] trivially. On any basis this is the nonvanishing of the determinant of the first d coefficient columns. This is a finite-dimensional linear-algebra theorem; no novelty is claimed.

The ambient space need not be full. Gaps in leading degrees at infinity do not disprove the window law, because this condition concerns vanishing order at zero. Conversely a bound on pole order at infinity does not prove that determinant is nonzero. A uniform window proof must control the position of W relative to the coefficient flag, not just its dimension.

A positive-definite Gram or total-positivity construction could prove the determinant condition if an actual compatible basis is supplied; no such construction is established here.

## Later promotions: necessary onset, not predicted onset

For the on-site factor of a cubic height model, promoting height 2 to i+2 and removing the extra volume normalization gives tau_i=3i(i+3)/2. The next values are 27,42,60. They are raw promotion exponents, not proved surviving poles.

At fixed pattern size k the usable grouped e22 directions run over E=k+1,...,floor((3k-2)/2); their number is N(k)=floor(k/2)-1. A polynomial amplitude with those consecutive powers that is divisible by (1+f)^nu can be nonzero only if N(k)>=nu+1, hence k>=2nu+4. At jet j this implies the necessary condition

V>=j+2nu+4.

For j=4, nu=3, this gives V>=14. For j=5, retaining only nu>=3 gives V>=15 as a necessary bound; additional earlier rows can make the true onset later or forbid that amplitude entirely. It is not a prediction of onset at 15.

For a candidate pole p at volume V, the target energy is e=3V+2p. Use the full earlier-row kernel on the declared supported columns. A surviving coefficient is certified by a strict rank increase upon adjoining that energy row, or by a vector annihilating all earlier rows and having nonzero target pairing. Certify a maximum separately by proving all higher-energy rows are in the earlier span. The certificate kernel formalized in this package concerns these finite row tests; it does not prove that the input rows have the intended graph-series semantics.
