# Deployment audit: Qwen/Qwen2.5-1.5B

Revision `8faed761d45a263340a0528343f099c05c9a4323`, float16 on Tesla T4; protocol `16b658137ff946d2` frozen 2026-10-19T20:12:40.660803+00:00.

| Panel | Tokens | Construction variants with 2 separators | Held-out detected | False alarms |
|---|---:|---:|---:|---|
| exact | 261 | 6/6 | 6/7 | control/eager_attention_backend, control/kv_cache_disabled |
| pruned_greedy | 261 | 6/6 | 6/7 | control/eager_attention_backend, control/kv_cache_disabled |
| greedy | 272 | 6/6 | 6/7 | control/eager_attention_backend, control/kv_cache_disabled |
| typical | 286 | 4/6 | 5/7 | control/eager_attention_backend, control/kv_cache_disabled |

Full pool: 667 tokens. Exact panel saves 0.00% of tokens versus optimally pruned greedy. Random panels at the exact budget meeting the requirement: 0/1000.
Excluded construction variants (fewer than two separating probes): {'positions_not_offset_for_left_padding': 0}.
Skipped variants: none.
Configurations emitting non-finite log-probabilities: {'control/eager_attention_backend': 1348}.

Resident: full pool 2.0546s vs panel check 0.9390s (2.19x). Break-even: 93 checks (construction), 181 (construction + audit).
Cold checks: [] seconds.
Package verified: True.

Per-variant separators in the full pool:

- construction/half_precision_export_swap: 18
- construction/int8_bitsandbytes: 18
- construction/padding_mask_dropped: 4
- construction/positions_not_offset_for_left_padding: 0
- construction/temperature_1.3: 18
- construction/truncate_to_48: 4
- construction/unicode_nfkc: 3
- control/eager_attention_backend: 18
- control/kv_cache_disabled: 4
- control/reversed_order: 0
- control/same_dtype_export_roundtrip: 0
- heldout/crlf_newlines: 3
- heldout/kv_cache_positions_reset: 8
- heldout/nf4_4bit_bitsandbytes: 18
- heldout/right_padding_generation: 4
- heldout/rope_base_halved: 18
- heldout/temperature_1.1: 18
- heldout/truncate_to_72: 2

Exact coverage of the declared construction table only; held-out detection, false alarms and timings are measurements on this run.
