"""Brier audit for council-diff verdicts. Persistence-agnostic."""
from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

Recommendation = Literal["go", "wait", "kill", "split"]
Outcome = Literal[
    "go-was-right", "go-was-wrong",
    "wait-was-right", "wait-was-wrong",
    "kill-was-right", "kill-was-wrong",
    "split-was-right", "split-was-wrong",
    "unresolvable",
]


@dataclass
class Prediction:
    id: str
    decision: str
    domain: str
    recommendation: Recommendation
    agreement_score: float
    voice_scores: list[int]
    created_at: str
    resolve_by: str | None = None
    outcome: Outcome | None = None
    resolved_at: str | None = None
    notes: str | None = None
    # Oracle layer (v0.3.0+) — set when CouncilResult.oracle was present.
    # Scored separately so we can audit Oracle independent of the council.
    oracle_recommendation: Recommendation | None = None
    oracle_score: int | None = None  # 0-100 — Oracle's own confidence
    oracle_model: str | None = None  # e.g. "claude-fable-5"


def _new_id() -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=12))


def add_prediction(
    decision: str,
    domain: str,
    recommendation: Recommendation,
    agreement_score: float,
    voice_scores: list[int],
    resolve_by: str | None = None,
    notes: str | None = None,
    oracle_recommendation: Recommendation | None = None,
    oracle_score: int | None = None,
    oracle_model: str | None = None,
) -> Prediction:
    return Prediction(
        id=_new_id(),
        decision=decision,
        domain=domain,
        recommendation=recommendation,
        agreement_score=agreement_score,
        voice_scores=voice_scores,
        created_at=datetime.now(timezone.utc).isoformat(),
        resolve_by=resolve_by,
        notes=notes,
        oracle_recommendation=oracle_recommendation,
        oracle_score=oracle_score,
        oracle_model=oracle_model,
    )


def resolve_prediction(pred: Prediction, outcome: Outcome, notes: str | None = None) -> Prediction:
    pred.outcome = outcome
    pred.resolved_at = datetime.now(timezone.utc).isoformat()
    if notes:
        pred.notes = notes
    return pred


def predicted_probability(pred: Prediction) -> float:
    base = {"go": 0.8, "wait": 0.5, "kill": 0.2, "split": 0.5}[pred.recommendation]
    p = 0.5 + (base - 0.5) * max(0.0, min(1.0, pred.agreement_score))
    return max(0.01, min(0.99, p))


def actual_outcome(pred: Prediction) -> int | None:
    if pred.outcome is None or pred.outcome == "unresolvable":
        return None
    return 1 if pred.outcome.endswith("-was-right") else 0


def brier_score(pred: Prediction) -> float | None:
    actual = actual_outcome(pred)
    if actual is None:
        return None
    p = predicted_probability(pred)
    return (p - actual) ** 2


def mean_brier(preds: list[Prediction]) -> dict | None:
    scores = [brier_score(p) for p in preds]
    scores = [s for s in scores if s is not None]
    if not scores:
        return None
    mean = sum(scores) / len(scores)
    return {"mean": mean, "n": len(scores), "edge_vs_random": 0.25 - mean}


def brier_by_domain(preds: list[Prediction]) -> dict[str, dict | None]:
    by_domain: dict[str, list[Prediction]] = {}
    for p in preds:
        by_domain.setdefault(p.domain, []).append(p)
    return {d: mean_brier(ps) for d, ps in by_domain.items()}


def oracle_brier_score(pred: Prediction) -> float | None:
    """Brier score for the Oracle layer of a resolved prediction.

    Same probability map as the council, but driven by `oracle_recommendation`
    and `oracle_score` instead of recommendation + agreement_score. The Oracle's
    own self-reported confidence (0-100) plays the role agreement_score plays
    for the council — high confidence nudges toward the recommendation's base
    probability, low confidence pulls toward 0.5.

    Returns None if there's no Oracle data on this prediction OR if the
    prediction isn't resolved yet OR if the outcome is "unresolvable".
    """
    if pred.oracle_recommendation is None:
        return None
    actual = actual_outcome(pred)
    if actual is None:
        return None
    base = {"go": 0.8, "wait": 0.5, "kill": 0.2, "split": 0.5}[pred.oracle_recommendation]
    conf = max(0, min(100, pred.oracle_score if pred.oracle_score is not None else 50)) / 100
    p = 0.5 + (base - 0.5) * conf
    clamped = max(0.01, min(0.99, p))
    return (clamped - actual) ** 2


def oracle_vs_council(preds: list[Prediction]) -> dict | None:
    """Oracle-vs-council comparison over a set of resolved predictions.

    Honest answer to "is paying $0.10 for Oracle worth it over $0.03 council
    alone?" Lower Brier = better calibrated. `delta = oracle_mean - council_mean`:
      - delta < 0  -> Oracle BEATS council (worth the extra cost)
      - delta = 0  -> tie
      - delta > 0  -> Oracle UNDERPERFORMS council (don't pay for Oracle)

    Counts:
      - oracle_overrides: predictions where Oracle and council disagreed
      - oracle_override_wins: of those, how often Oracle's call beat council's

    Returns None if no resolved predictions have Oracle data.
    """
    with_oracle = [
        p for p in preds
        if p.oracle_recommendation is not None and actual_outcome(p) is not None
    ]
    if not with_oracle:
        return None

    council_scores: list[float] = []
    oracle_scores: list[float] = []
    overrides = 0
    override_wins = 0

    for p in with_oracle:
        c = brier_score(p)
        o = oracle_brier_score(p)
        if c is None or o is None:
            continue
        council_scores.append(c)
        oracle_scores.append(o)
        if p.oracle_recommendation != p.recommendation:
            overrides += 1
            if o < c:
                override_wins += 1

    if not council_scores:
        return None

    c_mean = sum(council_scores) / len(council_scores)
    o_mean = sum(oracle_scores) / len(oracle_scores)
    return {
        "n": len(council_scores),
        "council_mean_brier": c_mean,
        "oracle_mean_brier": o_mean,
        "delta": o_mean - c_mean,
        "oracle_overrides": overrides,
        "oracle_override_wins": override_wins,
    }
