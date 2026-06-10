"""Unit tests for council-diff brier audit math."""
from council_diff.brier import (
    Prediction,
    actual_outcome,
    add_prediction,
    brier_by_domain,
    brier_score,
    mean_brier,
    oracle_brier_score,
    oracle_vs_council,
    predicted_probability,
    resolve_prediction,
)


def _mkpred(**kw):
    """Test helper — minimal Prediction with sane defaults."""
    defaults = dict(
        decision="Should I X?",
        domain="founder",
        recommendation="go",
        agreement_score=0.8,
        voice_scores=[80, 75, 70, 65, 60],
    )
    defaults.update(kw)
    return add_prediction(**defaults)


def test_add_prediction_assigns_id_and_timestamp():
    p = _mkpred()
    assert isinstance(p.id, str) and len(p.id) == 12
    assert p.created_at.startswith("20")  # ISO format
    assert p.outcome is None


def test_resolve_marks_outcome_and_timestamp():
    p = _mkpred()
    resolved = resolve_prediction(p, "go-was-right")
    assert resolved.outcome == "go-was-right"
    assert resolved.resolved_at is not None


def test_predicted_probability_go_with_high_agreement():
    # go base = 0.8, agreement 1.0 → p = 0.5 + (0.8 - 0.5) * 1.0 = 0.8
    p = _mkpred(recommendation="go", agreement_score=1.0)
    assert abs(predicted_probability(p) - 0.8) < 0.01


def test_predicted_probability_split_pins_to_05():
    # split base = 0.5, regardless of agreement → p = 0.5
    p = _mkpred(recommendation="split", agreement_score=0.9)
    assert abs(predicted_probability(p) - 0.5) < 0.01


def test_predicted_probability_kill_with_high_agreement():
    # kill base = 0.2, agreement 1.0 → p = 0.5 + (0.2 - 0.5) * 1.0 = 0.2
    p = _mkpred(recommendation="kill", agreement_score=1.0)
    assert abs(predicted_probability(p) - 0.2) < 0.01


def test_predicted_probability_low_agreement_pulls_to_05():
    # go base = 0.8, agreement 0 → p = 0.5 (coin flip when nobody agrees)
    p = _mkpred(recommendation="go", agreement_score=0.0)
    assert abs(predicted_probability(p) - 0.5) < 0.01


def test_brier_score_perfect_when_p_matches_outcome():
    # go with high agreement (p ≈ 0.8), outcome is "go-was-right" (1)
    # brier = (0.8 - 1)² = 0.04
    p = _mkpred(recommendation="go", agreement_score=1.0)
    resolved = resolve_prediction(p, "go-was-right")
    assert abs(brier_score(resolved) - 0.04) < 0.001


def test_brier_score_max_when_p_opposite_to_outcome():
    # go with high agreement (p ≈ 0.8), but it was wrong → "go-was-wrong" (0)
    # brier = (0.8 - 0)² = 0.64
    p = _mkpred(recommendation="go", agreement_score=1.0)
    resolved = resolve_prediction(p, "go-was-wrong")
    assert abs(brier_score(resolved) - 0.64) < 0.001


def test_brier_score_returns_none_for_unresolved():
    p = _mkpred()
    assert brier_score(p) is None


def test_brier_score_returns_none_for_unresolvable_outcome():
    p = _mkpred()
    resolved = resolve_prediction(p, "unresolvable")
    assert brier_score(resolved) is None


def test_mean_brier_returns_none_for_empty_or_unresolved():
    assert mean_brier([]) is None
    assert mean_brier([_mkpred(), _mkpred()]) is None


def test_mean_brier_edge_vs_random_positive_when_below_025():
    # 3 correct go predictions (brier 0.04 each) → mean = 0.04, edge = 0.21
    preds = [
        resolve_prediction(_mkpred(recommendation="go", agreement_score=1.0), "go-was-right")
        for _ in range(3)
    ]
    audit = mean_brier(preds)
    assert audit is not None
    assert abs(audit["mean"] - 0.04) < 0.001
    assert audit["n"] == 3
    assert audit["edge_vs_random"] > 0.2


def test_brier_by_domain_splits_correctly():
    preds = [
        resolve_prediction(_mkpred(domain="founder"), "go-was-right"),
        resolve_prediction(_mkpred(domain="founder"), "go-was-wrong"),
        resolve_prediction(_mkpred(domain="quant"), "go-was-right"),
    ]
    by_dom = brier_by_domain(preds)
    assert "founder" in by_dom and "quant" in by_dom
    assert by_dom["founder"]["n"] == 2
    assert by_dom["quant"]["n"] == 1


def test_actual_outcome_maps_correctly():
    p = _mkpred()
    assert actual_outcome(p) is None  # unresolved
    assert actual_outcome(resolve_prediction(_mkpred(), "go-was-right")) == 1
    assert actual_outcome(resolve_prediction(_mkpred(), "wait-was-right")) == 1
    assert actual_outcome(resolve_prediction(_mkpred(), "kill-was-wrong")) == 0
    assert actual_outcome(resolve_prediction(_mkpred(), "split-was-wrong")) == 0
    assert actual_outcome(resolve_prediction(_mkpred(), "unresolvable")) is None


def test_high_disagreement_council_split_recommendation_is_calibrated():
    # When council says split (recommendation), the implied probability stays at 0.5,
    # so brier is 0.25 (random) whether actual outcome is 1 or 0.
    p = _mkpred(recommendation="split", agreement_score=0.3)
    resolved_right = resolve_prediction(_mkpred(recommendation="split", agreement_score=0.3), "split-was-right")
    resolved_wrong = resolve_prediction(_mkpred(recommendation="split", agreement_score=0.3), "split-was-wrong")
    # Both should be ~ 0.25 (random baseline)
    assert abs(brier_score(resolved_right) - 0.25) < 0.001
    assert abs(brier_score(resolved_wrong) - 0.25) < 0.001


# ─── Oracle layer (v0.3.0+) ────────────────────────────────────────────


def test_oracle_brier_score_returns_none_when_no_oracle_data():
    p = resolve_prediction(_mkpred(), "go-was-right")
    assert oracle_brier_score(p) is None


def test_oracle_brier_score_perfect_when_confident_and_right():
    # Oracle says go with conf=100, outcome was go-was-right (actual=1)
    # p = 0.5 + (0.8 - 0.5) * 1.0 = 0.8 → brier = (0.8-1)² = 0.04
    p = resolve_prediction(
        _mkpred(oracle_recommendation="go", oracle_score=100, oracle_model="claude-fable-5"),
        "go-was-right",
    )
    assert abs(oracle_brier_score(p) - 0.04) < 0.001


def test_oracle_brier_score_max_when_confident_and_wrong():
    # Same Oracle conf, but outcome was wrong (actual=0) → brier = (0.8-0)² = 0.64
    p = resolve_prediction(
        _mkpred(oracle_recommendation="go", oracle_score=100, oracle_model="claude-fable-5"),
        "go-was-wrong",
    )
    assert abs(oracle_brier_score(p) - 0.64) < 0.001


def test_oracle_brier_score_low_confidence_pulls_to_05():
    # Oracle says go with conf=0 → p=0.5 (coin flip)
    # outcome go-was-right (actual=1) → brier = (0.5-1)² = 0.25
    p = resolve_prediction(
        _mkpred(oracle_recommendation="go", oracle_score=0, oracle_model="claude-fable-5"),
        "go-was-right",
    )
    assert abs(oracle_brier_score(p) - 0.25) < 0.001


def test_oracle_vs_council_returns_none_when_no_oracle_data():
    preds = [resolve_prediction(_mkpred(), "go-was-right")]
    assert oracle_vs_council(preds) is None


def test_oracle_vs_council_counts_overrides_and_wins():
    # Scenario 1: Oracle overrides council and wins
    # Council go (p=0.8) vs Oracle kill (conf=90, p≈0.23); outcome go-was-wrong (actual=0)
    # Council Brier ≈ 0.64, Oracle Brier ≈ 0.053 → Oracle wins the override
    override_win = resolve_prediction(
        _mkpred(
            recommendation="go", agreement_score=1.0,
            oracle_recommendation="kill", oracle_score=90, oracle_model="claude-fable-5",
        ),
        "go-was-wrong",
    )
    # Scenario 2: agreement, both right — counts as neither override nor mismatch
    agree_win = resolve_prediction(
        _mkpred(
            recommendation="go", agreement_score=1.0,
            oracle_recommendation="go", oracle_score=90, oracle_model="claude-fable-5",
        ),
        "go-was-right",
    )
    # Scenario 3: agreement go, right
    no_override = resolve_prediction(
        _mkpred(
            recommendation="go", agreement_score=1.0,
            oracle_recommendation="go", oracle_score=80, oracle_model="claude-fable-5",
        ),
        "go-was-right",
    )
    comp = oracle_vs_council([override_win, agree_win, no_override])
    assert comp is not None
    assert comp["n"] == 3
    assert comp["oracle_overrides"] == 1
    assert comp["oracle_override_wins"] == 1
    # Oracle beats council on this synthetic set
    assert comp["delta"] < 0
