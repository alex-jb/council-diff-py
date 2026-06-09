# Changelog

## [Unreleased]

### Added
- CLI (`council "..." --domain career`) planned
- FastAPI server example planned

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
