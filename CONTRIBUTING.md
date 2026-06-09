# Contributing

Thanks for considering a contribution. `council-diff-py` is the Python port of [council-diff](https://github.com/alex-jb/council-diff) — keep it small and in sync with the TypeScript version.

## Quick start

```bash
git clone https://github.com/alex-jb/council-diff-py.git
cd council-diff-py
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -v
```

To run an example:
```bash
ANTHROPIC_API_KEY=sk-ant-... python examples/founder.py
```

## What we welcome

- **Parity with TypeScript version** — PRs that align behavior + interfaces with `council-diff` are top priority. When in doubt, mirror the TS API.
- **Brier audit extensions** — persistence adapters (SQLite / Postgres / JSONL helpers), calibration tests, better outcome mappings.
- **CLI** — `council "should I quit my job" --domain career` is on the roadmap. Open a PR with `argparse` or `click` flow.
- **FastAPI server example** — hosted council with a `/deliberate` endpoint.

## What we'll reject

- Pydantic conversion for the public API (dataclasses keep the surface tiny — see open question in README)
- LangChain / LangGraph wrappers (the whole point is single-call, no graph orchestrator)
- New runtime dependencies beyond `anthropic` (we may revisit for type validation; open an issue first)

## Style

- Python 3.10+ (we drop 3.9 because anthropic SDK requires ≥3.10)
- Dataclasses with `from __future__ import annotations`
- Type hints with `Literal` for enums
- Tests via pytest

## Running tests

```bash
pytest tests/ -v
```

15 tests cover the Brier math. Add tests when you touch `brier.py` — the math is opinionated and should stay regression-tested.

## License

By contributing, you agree your contributions are licensed under MIT.
