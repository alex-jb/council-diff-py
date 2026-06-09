# council-diff-py — Python-specific launch drafts

3 channels where Python developers actually hang out and the TypeScript launch wouldn't have hit.

---

## r/Python

**Title**: I built a 5-voice AI council in Python — paste any decision, get 5 specialist verdicts + Brier audit

**Body**:

Hey r/Python — I open-sourced council-diff-py earlier today after porting the TypeScript original.

The pattern: paste a decision, one Claude Sonnet 4.6 call produces 5 specialist verdicts in parallel. For "should I raise a seed?":

```python
from council_diff import CouncilDiff

council = CouncilDiff()
result = council.deliberate(
    domain="founder",
    decision="Should I raise $1M seed or stay bootstrapped?",
    context="$5K MRR, 20% MoM, solo, 12mo runway",
)

print(result.recommendation)       # "go" | "wait" | "kill" | "split"
print(result.agreement_score)      # 0.42 — voices disagree

for v in result.voices:
    print(f"{v.voice_display} ({v.score}/100): {v.verdict}")
```

6 built-in domains: `founder` / `engineer` / `investor` / `career` / `product` / `quant`. Plus `custom` for fully user-defined voice rosters.

Counter-intuitive thing I learned: asking for 5 voices in 1 LLM call produces better disagreement than 5 parallel calls. The voices "see" each other in the model's context and push back. With 5 parallel calls, each persona is alone and converges to the median answer. 1/5 the cost too.

Brier audit module (`council_diff.brier`) lets you log predictions, resolve at known timestamps, and score yourself honestly:

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
# 12mo later:
resolved = resolve_prediction(pred, "go-was-right")
score = brier_score(resolved)  # 0 = perfect, 1 = worst, 0.25 = random
```

15 unit tests cover the Brier math (predicted_probability for all 4 recommendations, edge_vs_random calc, persistence-agnostic interface).

- GitHub: github.com/alex-jb/council-diff-py
- TypeScript original: github.com/alex-jb/council-diff
- MIT license
- Bilingual README (EN + 中文)
- Anthropic SDK only dep
- `pip install council-diff` (publishing this week)

Drop a decision in the comments — I'll run the council on it.

---

## r/LearnPython

**Title**: Built a small Python package that demonstrates a "5-persona in 1 LLM call" pattern + Brier audit math — feedback welcome

**Body**:

I'm a M.S. CS student. Just published council-diff-py (the Python port of my TypeScript original) as a small case study in two patterns I think are worth learning:

**1. Single-call multi-persona structured output**

Instead of making 5 separate Anthropic API calls for 5 personas, you make 1 call with a structured JSON schema that produces all 5 verdicts. The personas argue with each other inside the model's context window. This is counter-intuitively better than 5 parallel calls because the voices push back on each other.

The whole technique is in `council_diff/__init__.py` — about 100 lines including the system prompt that defines the 5 voices.

**2. Brier audit as persistence-agnostic interface**

`council_diff/brier.py` is ~100 lines of pure functions:
- `add_prediction(...)` — make a Prediction dataclass
- `resolve_prediction(pred, outcome)` — mark outcome
- `predicted_probability(pred)` — map (recommendation, agreement_score) to p
- `brier_score(pred)` — `(p - actual)²`
- `mean_brier(preds)` — aggregate + `edge_vs_random`
- `brier_by_domain(preds)` — per-domain breakdown

No database, no I/O — you pass in a list of dataclasses, you get a dict back. Bring your own JSONL, SQLite, or Postgres.

15 pytest tests cover the math. They use a `_mkpred` helper that defaults sensible values and lets each test override one field — a pattern I think is way more readable than fixture stacking.

Code: github.com/alex-jb/council-diff-py

Looking for feedback on:
- Are the dataclass type hints + Literal types idiomatic, or should I use Pydantic?
- The single-call multi-persona pattern — does anyone know prior literature on this?
- The Brier audit interface — would you rather have an object-oriented API (`Council.audit().score()`) or stay functional?

---

## dev.to (Python crowd)

**Title**: A 100-line Python pattern that produces better LLM verdicts than parallel calls

**Tags**: python, ai, claude, opensource

**Body**:

I just open-sourced [council-diff-py](https://github.com/alex-jb/council-diff-py) — a 100-line library that produces 5 specialist verdicts on any decision in a single Anthropic API call. Counter-intuitively, this works better than 5 parallel calls.

## The pattern in one screenshot

```python
from council_diff import CouncilDiff

council = CouncilDiff()
result = council.deliberate(
    domain="engineer",
    decision="Use Postgres or DynamoDB for this new service?",
    context="10K writes/sec peak, eventual consistency OK, team knows SQL well",
)

# 5 voices argue, then synthesize
print(f"Recommendation: {result.recommendation}")     # go | wait | kill | split
print(f"Agreement: {result.agreement_score:.0%}")     # how united they are

for v in result.voices:
    print(f"\n{v.voice_display} ({v.score}/100)")
    print(f"  {v.verdict}")
    print(f"  + Strength: {v.strength}")
    print(f"  - Gap: {v.gap}")
```

Each voice is a real persona with a hardcoded prior:

- **Rust Core Maintainer** — "types catch bugs, push for static guarantees"
- **SRE Oncall** — "simple > clever, push back on novel infra"
- **Tech Recruiter** — "ecosystem maturity matters"
- **Junior Dev Just Onboarded** — "docs > theoretical purity"
- **CTO 5 Years From Now** — "today's choice is tomorrow's legacy"

## Why one call beats five

If you do 5 parallel API calls, each persona sits alone in its own context window. They tend to converge to the median answer because none of them has anything to react against.

If you do 1 call with all 5 voices in the same prompt, the voices "see" each other in the model's working context. The lawyer cites a tax issue, the CFO responds. You get real disagreement.

Bonus: 1 call instead of 5 = 1/5 the cost. ~$0.03 per deliberation with Sonnet 4.6.

## Brier audit is the moat

Anyone can build a council. The differentiation is publishing your predictions with timestamps and getting them scored honestly at resolution.

```python
from council_diff.brier import add_prediction, resolve_prediction, brier_score, mean_brier

# At deliberation time
pred = add_prediction(
    decision=result.decision,
    domain=result.domain,
    recommendation=result.recommendation,
    agreement_score=result.agreement_score,
    voice_scores=[v.score for v in result.voices],
    resolve_by="2027-06-09",
)
# Persist `pred` to JSONL / SQLite / Postgres of your choice.

# Months later when outcome is known
resolved = resolve_prediction(pred, "go-was-right")
score = brier_score(resolved)  # 0 = perfect, 1 = worst, 0.25 = random
```

The math: `predicted_probability` maps recommendation + agreement_score to a probability between 0.01 and 0.99. `brier_score` is `(p - actual)²`. `mean_brier` returns `{mean, n, edge_vs_random}` where `edge_vs_random = 0.25 - mean`. Positive = you have calibration edge over coin-flipping.

## Open questions I'd love feedback on

1. **Should the voices be Pydantic models or plain dataclasses?** I went with dataclasses because the public API is "pass dict → get dict back" with no validation surface to worry about. But Pydantic would give nicer error messages.

2. **Streaming voice-by-voice output?** Currently the API call returns all 5 voices at once. Streaming each voice as it lands would feel more dynamic but breaks the "they argue in shared context" insight (you'd have to send tokens to the user as they generate, which means voices haven't read each other's outputs yet).

3. **Has anyone seen literature on single-call multi-persona vs parallel-call setups for calibration?** This feels like it should be a known result but I can't find anything that names the pattern.

## Links

- GitHub: [github.com/alex-jb/council-diff-py](https://github.com/alex-jb/council-diff-py)
- TypeScript original (15 days older): [github.com/alex-jb/council-diff](https://github.com/alex-jb/council-diff)
- MIT, bilingual README (EN + 中文)
- 15 pytest tests covering the Brier math
- `pip install council-diff` (publishing this week)

If you build with it, drop me a link — I'd love to see the custom voice rosters people invent.
