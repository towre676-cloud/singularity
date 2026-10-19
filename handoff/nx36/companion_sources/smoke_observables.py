"""Check existing target-relative scalar extraction APIs; this is not NX31 implementation."""
from perfectpower.curve_families import CurveFamily
from perfectpower.differential_modules import DifferentialModule


module = DifferentialModule({"matrix": [[0, 1], [0, 0]], "label": "NX31 source smoke"})
first = module.observable([1, 0])
second = module.observable([0, 1])
assert first["order"] == 2 and first["operator_identity_checked"]
assert second["order"] == 1 and second["operator_identity_checked"]
legendre = CurveFamily({"coefficients": [[0], [0, 1], [-1, -1], [1]]})
operator = legendre.observable([1, 0])
assert operator["order"] == 2
assert operator["polynomial_operator"] == [[1], [-4, 8], [0, -4, 4]]
print("Existing DifferentialModule.observable orders 2/1 and Legendre CurveFamily.observable checked.")
