# README illustrations

These self-contained SVG figures are generated from explicit graph examples and retained source-model calculations. They use the README's existing dark palette and remain sharp at any zoom. Every figure contains a descriptive title and accessibility text; the root README also provides Markdown alternative text.

`height-profile.svg` illustrates one labeled profile on the five-cycle: heights `(0,1,3,2,0)`, total height 6, squared-edge energy 10, and nested threshold populations 3, 2, 1. It is an explanatory example, not a new graph-separation result.

`chosen-experiment.svg` reproduces `path_fixture` in [the operator receipt](../../results/operator_experiments.json). The same path has two different terminal placements. Both passive volume-one readings are 5/4 at q=1/2; adding one shared neighbor gives 1 and 9/8. The generator independently verifies those after-attachment readings from the degrees of the actual drawn graphs. The cost-one optimum is the retained theorem-backed result for the declared attachment language.

`thermal-diagnosis.svg` solves the 12×12 source model for eight heater inputs of amplitude two, from zero initial excess temperature, with exact Fraction arithmetic. The fields show the two reflected blocked-bond hypotheses and the same localized left sensor. Exact sensor predictions are checked against [the thermal receipt](../../results/thermal_diagnostics.json), as is the nominal prediction. A common color scale is used. The 20/31/44 diagnostic costs are source-model cost units; fields and faults are synthetic, not measured equipment data. The complete [application description](../../applications/thermal_diagnostics/README.md) states the uncertainty and optimization scope.

Rebuild all three figures from the repository root with `python scripts/build_readme_images.py`. The SVG generation and numerical checks use only the standard library. Optional `--preview` requires Pillow and DejaVu fonts and creates local PNG review images under `previews/`; those review files are not required by the README. [The figure inputs](readme-figures.json) retain the exact rational predictions and cost records used in the images.
