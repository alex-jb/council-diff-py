# council-diff-py

> Python port of [council-diff](https://github.com/alex-jb/council-diff) — 5-voice AI council for any decision.
> [English](README.md) · [中文](README.zh-CN.md)

This is the Python port of the TypeScript [`council-diff`](https://github.com/alex-jb/council-diff) library. Same architecture, same 6 built-in domains, same Brier audit math.

## Install

```bash
pip install council-diff
```

## Quickstart

```python
from council_diff import CouncilDiff

council = CouncilDiff(api_key=None)  # falls back to ANTHROPIC_API_KEY env

result = council.deliberate(
    domain="founder",
    decision="Should I raise a $1M seed round or stay bootstrapped?",
    context="B2B SaaS, $5K MRR, growing 20% MoM, solo founder, 12mo runway",
)

print(result.recommendation)       # "go" | "wait" | "kill" | "split"
print(result.agreement_score)      # 0-1
print(result.consensus)            # 1-paragraph synthesis

for v in result.voices:
    print(f"{v.voice_display} ({v.score}/100): {v.verdict}")
    print(f"  + {v.strength}")
    print(f"  - {v.gap}")
```

## Brier audit

```python
from council_diff.brier import add_prediction, resolve_prediction, brier_score, mean_brier

pred = add_prediction(
    decision=result.decision,
    domain=result.domain,
    recommendation=result.recommendation,
    agreement_score=result.agreement_score,
    voice_scores=[v.score for v in result.voices],
    resolve_by="2027-06-09",
)

# 12mo later when outcome is known:
resolved = resolve_prediction(pred, outcome="go-was-right")
score = brier_score(resolved)  # 0 = perfect, 1 = worst, 0.25 = random

# Aggregate over many resolutions:
audit = mean_brier(all_resolved_preds)
print(audit["edge_vs_random"])  # positive = council adds calibration value
```

## Roadmap

- [x] Scaffold + spec parity with TypeScript version
- [ ] `pip install council-diff` published
- [ ] CLI: `council "should I quit my job" --domain career`
- [ ] FastAPI server for hosting

## License

MIT
