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
