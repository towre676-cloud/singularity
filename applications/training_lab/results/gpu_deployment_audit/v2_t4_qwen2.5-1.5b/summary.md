# Deployment audit v2: Qwen/Qwen2.5-1.5B

Revision `8faed761d45a263340a0528343f099c05c9a4323`, float16 on Tesla T4; protocol `0ecf6e6d1cc7b8b0` frozen 2026-10-19T19:50:37.579112+00:00. Supersedes version 1 (protocol 47b381aacf9182f3), which is preserved.

| Panel | Tokens | Construction variants with 2 separators | Held-out detected | Missed held-out | False alarms (validation) |
|---|---:|---:|---:|---|---|
| exact | 261 | 6/6 | 8/9 | truncate_to_72 | none |
| pruned_greedy | 261 | 6/6 | 8/9 | truncate_to_72 | none |
| greedy | 272 | 6/6 | 8/9 | truncate_to_72 | none |
| typical | 286 | 4/6 | 7/9 | crlf_newlines, right_padding_generation | none |

Full pool: 667 tokens. Exact versus optimally pruned greedy: 0.00% fewer tokens. Random panels at the exact budget meeting the requirement: 0/1000.
Continuation tokens compared after calibration: {'full_science': 8, 'pad_born': 8, 'pad_river': 8, 'pad_capital': 8, 'short_population': 8, 'uni_ligature': 8, 'nl_code': 8, 'nl_list': 8}.
Excluded construction variants (fewer than two separating probes): {'positions_not_offset_for_left_padding': 0}.
Numerical-health failures (non-finite values by probe): {'candidate/eager_attention': {'full_history': 228, 'full_science': 200, 'full_sport': 216, 'full_music': 198, 'pad_born': 38, 'pad_river': 23, 'pad_capital': 23, 'pad_church': 18, 'short_population': 26, 'short_first': 18, 'short_known': 15, 'uni_ligature': 56, 'uni_accents': 36, 'uni_padded': 30, 'uni_width': 57, 'nl_code': 62, 'nl_list': 47, 'nl_header': 57}}.
Skipped: none.

Candidate configurations:

- eager_attention: not_approved_numerical_health_failure (1348 non-finite values; 18 probes flagged)

Resident: full pool 2.0283s vs panel check 0.9329s (2.17x). Break-even: 89 checks (construction), 173 (construction + audit).
Cold checks: [33.1, 27.7] seconds.
Package verified: True.

Separating probes in the full pool (r = retest from version 1, n = new in version 2):

- candidate/eager_attention: 18
- construction/half_precision_export_swap: 18 [r]
- construction/int8_bitsandbytes: 18 [r]
- construction/padding_mask_dropped: 4 [r]
- construction/positions_not_offset_for_left_padding: 0 [r]
- construction/temperature_1.3: 18 [r]
- construction/truncate_to_48: 4 [r]
- construction/unicode_nfkc: 3 [r]
- heldout/crlf_newlines: 3 [r]
- heldout/kv_cache_positions_reset: 8 [r]
- heldout/nf4_4bit_bitsandbytes: 18 [r]
- heldout/prefix_token_injected: 18 [n]
- heldout/repetition_penalty_1.2: 8 [n]
- heldout/right_padding_generation: 4 [r]
- heldout/rope_base_halved: 18 [r]
- heldout/temperature_1.1: 18 [r]
- heldout/truncate_to_72: 2 [r]
- validation/cached_batch_size_3: 0
- validation/reversed_order: 0
- validation/same_dtype_export_roundtrip: 0
- validation/uncached_batch_size_4: 0

Exact coverage of the declared construction table only; held-out detection, false alarms and timings are measurements on this run.
