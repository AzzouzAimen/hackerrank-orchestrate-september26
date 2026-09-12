# Evaluation area

`python code/evaluation/main.py saved-summary` reads recorded availability and token
usage from the existing shadow-experiment audit. It performs no model calls and makes
no financial recommendation.

`usage_report.md` is reserved for the required final full-dataset run report: provider
and model names, calls, input/output/total tokens, average tokens per request, and
estimated total/per-request cost. Populate it from the actual run when available.
