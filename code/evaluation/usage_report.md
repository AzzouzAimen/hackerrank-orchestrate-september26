# Final full-dataset usage report

Accepted decision artifact: repository archive `archive/cleanup_20260913/code/prototype/extraction_artifacts/full_run_05`. It replays the exact model bundles saved by `full_run_03` after the scheduled-salary finance correction and made zero additional model calls. This saved run is provenance evidence only; production can perform fresh inference and does not depend on the archive.

The final `output.csv` was generated for 250 requests with the guarded semantic architecture. Fifty structured-only requests required no model call. Text evidence used one extraction call; the 11 image-bearing requests also used a separate image-scoped call. Invalid model output was retried once and then failed closed.

| Item | Actual value |
| --- | ---: |
| Provider | Featherless |
| Model | `zai-org/GLM-5.3-Flash` |
| Requests | 250 |
| Model calls | 217 |
| Retries | 6 |
| Input tokens | 2,870,137 |
| Cached input tokens (included above) | 17,472 |
| Output tokens | 220,555 |
| Total tokens | 3,090,692 |
| Calls per request | 0.868 |
| Input tokens per request | 11,480.55 |
| Output tokens per request | 882.22 |
| Total tokens per request | 12,362.77 |
| Input tokens per model call | 13,226.44 |
| Output tokens per model call | 1,016.38 |
| Total tokens per model call | 14,242.82 |
| Mean / median call latency | 21.43 s / 16.64 s |
| p95 / maximum call latency | 47.99 s / 122.17 s |

Featherless listed GLM-5.3-Flash at $0.15 per million fresh input tokens, $0.03 per million cached input tokens, and $0.50 per million output tokens when checked on 2026-09-13. Pricing sources: <https://featherless.ai/models/zai-org/GLM-5.3-Flash> and <https://featherless.ai/docs/request-pricing-and-credits>.

Cost calculation:

```text
fresh input = 2,870,137 - 17,472 = 2,852,665 tokens
input cost  = 2.852665 * $0.15 + 0.017472 * $0.03 = $0.4284239
output cost = 0.220555 * $0.50 = $0.1102775
total       = $0.5387014
per request = $0.0021548
per call    = $0.0024825
```

The provider responses reported `zai-org/GLM-5.3-Flash` for all 217 calls. All calls ended with `finish_reason=stop`; one request still had no usable schema/target-valid bundle after its allowed retry and was explicitly blocked. The output audit found zero pipeline exceptions.
