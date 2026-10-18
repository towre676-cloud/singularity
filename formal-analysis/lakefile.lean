import Lake
open Lake DSL

package SingularityAnalysis where

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "v4.12.0"

require Singularity from "../formal"

@[default_target]
lean_lib SingularityAnalysis where
