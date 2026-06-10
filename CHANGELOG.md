# Changelog

## [Unreleased]

### Added
- CLI (`council "..." --domain career`) planned
- FastAPI server example planned

## [0.3.0] — 2026-06-10

### Added
- **Fable 5 Oracle mode** — `oracle="fable-5"` kwarg on `CouncilDiff.deliberate()`. After the 5-voice council deliberates, [Claude Fable 5](https://www.anthropic.com/news/claude-fable-5) (Mythos-class flagship, 95% SWE-Bench, 1M context) reads every verdict + the consensus and issues a single adjudication with override authority. Returned on `CouncilResult.oracle` (`OracleVerdict` dataclass: `model`, `recommendation`, `score`, `verdict`, optional `override_reason`).
- **Brier audit Oracle layer** in `council_diff.brier`: `oracle_brier_score()` for single-prediction Oracle scoring + `oracle_vs_council()` for honest cost-justification comparison (returns `delta`, `oracle_overrides`, `oracle_override_wins`).
- `Prediction` dataclass gains optional `oracle_recommendation` / `oracle_score` / `oracle_model` fields, scored separately from the council layer.
- **6 new pytest tests** covering Oracle Brier math + override-win counting (21 total tests, all green).

### Why
Anthropic shipped Claude Fable 5 on 2026-06-10. A single-LLM answer hides its own uncertainty; a 5-voice council exposes disagreement; a flagship adjudicator picks the side that holds up. Both layers Brier-audited separately so users see when Oracle wins vs underperforms the council, not just claim it.

### Cost
- Council only: ~$0.03/call (Sonnet 4.6)
- Council + Fable 5 Oracle: ~$0.10/call total

### Skipped
- 0.2.0 was reserved on the TypeScript port for the initial Brier audit module. Python port jumps 0.1.0 → 0.3.0 to track TypeScript versioning. No 0.2.0 ever published on PyPI.

## [0.1.0] — 2026-06-09

### Added
- Initial Python port of [council-diff](https://github.com/alex-jb/council-diff).
- `CouncilDiff` class with 6 built-in domains: `founder` / `engineer` / `investor` / `career` / `product` / `quant`.
- `custom` domain for fully user-defined voice rosters.
- Single Claude Sonnet 4.6 call produces 5 verdicts in 1 JSON response.
- `agreement_score` computed as `1 − normalized_stddev(voice_scores)`.
- Recommendation: `go` / `wait` / `kill` / `split`.
- **Brier audit module** (`council_diff.brier`): `add_prediction`, `resolve_prediction`, `predicted_probability`, `brier_score`, `mean_brier`, `brier_by_domain`. Persistence-agnostic.
- **15 pytest tests** covering Brier math (`tests/test_brier.py`).
- `examples/founder.py` — real fundraising deliberation with Brier logging.
- `.github/workflows/test.yml` — pytest matrix on 3.10/3.11/3.12.
- `.github/workflows/release.yml` — PyPI Trusted Publisher on `v*` tag.
- Bilingual README (EN + 中文).
- MIT license.

[Unreleased]: https://github.com/alex-jb/council-diff-py/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/alex-jb/council-diff-py/releases/tag/v0.1.0
