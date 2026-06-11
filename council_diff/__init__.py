"""council_diff — 5-voice AI council for any decision.

Python port of github.com/alex-jb/council-diff (TypeScript). Same architecture.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Literal

Domain = Literal["founder", "engineer", "investor", "career", "product", "quant", "custom"]
Recommendation = Literal["go", "wait", "kill", "split"]


@dataclass
class CouncilVoice:
    voice: str
    voice_display: str
    score: int  # 0-100
    verdict: str
    strength: str
    gap: str


@dataclass
class OracleVerdict:
    """Mythos-class adjudication over the 5-voice council.

    Returned on CouncilResult.oracle when `oracle="fable-5"` is passed to
    deliberate(). Brier-audited separately at resolution.
    """
    model: str  # e.g. "claude-fable-5" or "claude-sonnet-4-6" if downgraded
    recommendation: Recommendation
    score: int  # 0-100 — Oracle's own confidence the decision is correct
    verdict: str  # 2-3 sentences naming which voices it sided with
    override_reason: str | None = None  # set only when Oracle disagrees with the council
    # v0.3.1 disclosure: per Anthropic policy, Mythos-class models enforce
    # 30-day server-side retention; Sonnet 4.6 / Haiku 4.5 do not.
    # Source: support.claude.com/en/articles/15425996
    data_retention: Literal["30day-mythos", "zero"] = "30day-mythos"
    downgraded: bool = False  # True if safe_mode forced Fable 5 -> Sonnet 4.6


# Mythos-class models that carry Anthropic's 30-day data retention policy.
# Keep in sync with the official Anthropic announcement.
MYTHOS_MODELS: set[str] = {
    "claude-fable-5",
    "claude-opus-4-7-mythos",
}


@dataclass
class CouncilResult:
    domain: Domain
    decision: str
    voices: list[CouncilVoice]
    consensus: str
    agreement_score: float
    recommendation: Recommendation
    computed_at: str
    oracle: OracleVerdict | None = None  # set when deliberate(oracle="fable-5") was used


DOMAIN_VOICES: dict[Domain, list[dict[str, str]]] = {
    "founder": [
        {"slug": "yc_partner",   "display": "YC Partner",          "role": "Pattern matches 4000+ portcos. Bias: 'make something people want'. Push: distribution before polish."},
        {"slug": "vc_skeptic",   "display": "Tier-1 VC Skeptic",   "role": "Moat, capital efficiency, founder-market fit. Bias: most startups die from lack of revenue, not product."},
        {"slug": "lawyer",       "display": "Startup Lawyer",      "role": "Contract / equity / IP / liability. Bias: don't lock future optionality. Flag legal landmines."},
        {"slug": "accountant",   "display": "Indie CFO",           "role": "Burn rate / runway / unit econ. Bias: cash discipline > growth-at-all-costs for solo."},
        {"slug": "spouse",       "display": "Pragmatic Spouse",    "role": "Lifestyle / family / mental health. Bias: burnout kills more startups than competition."},
    ],
    "engineer": [
        {"slug": "rust_maintainer", "display": "Rust Core Maintainer",        "role": "Performance, safety, zero-cost. Bias: types catch bugs."},
        {"slug": "sre_oncall",      "display": "SRE Oncall",                  "role": "Reliability, observability, blast radius. Bias: simple > clever."},
        {"slug": "recruiter",       "display": "Tech Recruiter",              "role": "Hiring + talent market. Bias: ecosystem maturity matters."},
        {"slug": "junior_dev",      "display": "Junior Dev Just Onboarded",   "role": "Onboarding cost + cognitive load. Bias: docs > theoretical purity."},
        {"slug": "cto_5y_later",    "display": "CTO 5 Years From Now",        "role": "Migration cost + tech debt. Bias: today's choice is tomorrow's legacy."},
    ],
    "investor": [
        {"slug": "macro",          "display": "Macro Strategist",       "role": "Rates / cycle / regime. Bias: macro tide lifts/sinks individual picks."},
        {"slug": "sector_analyst", "display": "Sector Analyst",         "role": "Industry structure. Bias: rate the sector before the company."},
        {"slug": "pm",             "display": "Portfolio Manager",      "role": "Position sizing, correlation, hedging. Bias: good ideas at wrong size lose money."},
        {"slug": "vc_growth",      "display": "Growth VC",              "role": "Network effects, retention, moat. Bias: durability > growth rate."},
        {"slug": "short_seller",   "display": "Activist Short Seller",  "role": "Bear case, accounting risks. Bias: most stocks have a fault line."},
    ],
    "career": [
        {"slug": "mentor_20y",     "display": "Mentor with 20y Career Capital", "role": "Long-arc reputation. Bias: which doors does this open in 5 years?"},
        {"slug": "recruiter",      "display": "Top-Firm Recruiter",             "role": "Market value + signal quality. Bias: brand-name > obscure prestige."},
        {"slug": "peer_doing_well","display": "Peer Who's Doing Well",          "role": "Counterfactual benchmark. Bias: someone in your cohort is making the opposite call."},
        {"slug": "cso",            "display": "Chief Strategy Officer (yours)", "role": "Your 1-year plan. Bias: cash now vs option later."},
        {"slug": "future_you_5y",  "display": "You, 5 Years Older",             "role": "Regret minimization. Bias: optionality + experiences > marginal salary."},
    ],
    "product": [
        {"slug": "real_user",   "display": "Real User in the ICP",            "role": "JTBD. Bias: I will or won't pay."},
        {"slug": "competitor",  "display": "Competitor's PM",                 "role": "Threat assessment. Bias: am I scared of this move?"},
        {"slug": "internal_dev","display": "Internal Dev Who Has To Ship It", "role": "Engineering cost / debt. Bias: scope creep kills momentum."},
        {"slug": "garry_tan",   "display": "YC Partner — Garry-style",        "role": "Distribution + craft + ship velocity. Bias: ship faster, polish less."},
        {"slug": "naval",       "display": "Naval-style Skeptic",             "role": "First principles + leverage. Bias: what's the irreducible insight?"},
    ],
    "quant": [
        {"slug": "jane_street",         "display": "Jane Street MD",      "role": "Statistical rigor + calibration. Bias: distribution-of-outcomes > point estimate."},
        {"slug": "citadel",             "display": "Citadel Quant",       "role": "Real money in real markets. Bias: backtest fits ≠ live performance."},
        {"slug": "two_sigma",           "display": "Two Sigma ML",        "role": "Modern ML + nonstationarity. Bias: regime change breaks every model."},
        {"slug": "anthropic_researcher","display": "Anthropic Researcher","role": "LLM + agent depth. Bias: tools, not magic."},
        {"slug": "hft_engineer",        "display": "HFT Engineer",        "role": "Latency, kernel, deterministic systems. Bias: nanoseconds matter."},
    ],
    "custom": [],  # filled by user
}


def _build_system(domain: Domain, custom_voices: list[dict[str, str]] | None = None) -> str:
    voices = custom_voices if domain == "custom" and custom_voices else DOMAIN_VOICES[domain]
    voice_lines = "\n".join(
        f"{i+1}. {v['display'].upper()} — {v['role']}" for i, v in enumerate(voices)
    )
    return (
        "You are a council of 5 specialist voices evaluating a single decision. Output STRICT JSON.\n\n"
        f"The 5 voices:\n{voice_lines}\n\n"
        "For each voice, output a verdict grounded in their bias.\n"
        "- score: 0=strongly oppose, 50=neutral, 100=strongly support\n"
        "- verdict: 1-2 sentences in their voice\n"
        "- strength: single strongest signal supporting\n"
        "- gap: single biggest risk from their lens\n"
        '- when citing evidence, end with [src:context] if from user context, [src:domain_norm] for general\n\n'
        'Then output:\n'
        '- consensus: 1-paragraph synthesis (60-100 words)\n'
        '- recommendation: "go" if avg score ≥65, "wait" if 40-64, "kill" if ≤39, "split" if voices differ by >40\n\n'
        'Schema:\n'
        '{"voices": [{"voice":"<slug>","voice_display":"<display>","score":<0-100>,"verdict":"...","strength":"...","gap":"..."},...5],"consensus":"...","recommendation":"go|wait|kill|split"}'
    )


@dataclass
class CouncilDiff:
    api_key: str | None = None
    model: str = "claude-sonnet-4-6"
    # v0.3.1 privacy guard: when True, any oracle="fable-5" request silently
    # downgrades to claude-sonnet-4-6. Returned OracleVerdict.downgraded
    # tells the caller what actually ran. Opt in for any product with a
    # privacy claim that conflicts with 30-day retention.
    safe_mode: bool = False
    _client: object = field(default=None, init=False, repr=False)

    def __post_init__(self):
        key = self.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY not set")
        try:
            import anthropic
        except ImportError as e:
            raise RuntimeError("anthropic SDK not installed — pip install anthropic") from e
        self._client = anthropic.Anthropic(api_key=key)

    def deliberate(
        self,
        domain: Domain,
        decision: str,
        context: str | None = None,
        custom_voices: list[dict[str, str]] | None = None,
        oracle: str | None = None,  # "fable-5" or any Anthropic model ID
    ) -> CouncilResult:
        system = _build_system(domain, custom_voices)
        user = f"DECISION: {decision}\n\nCONTEXT:\n{context or '(no additional context)'}\n\nDeliberate."
        msg = self._client.messages.create(
            model=self.model,
            max_tokens=2500,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = msg.content[0].text if msg.content else ""
        parsed = json.loads(_strip_fences(text))
        voices = [CouncilVoice(**v) for v in parsed["voices"]]
        scores = [v.score for v in voices]
        mean = sum(scores) / len(scores)
        var = sum((s - mean) ** 2 for s in scores) / len(scores)
        stddev = var**0.5
        agreement = max(0.0, min(1.0, 1 - stddev / 50))
        result = CouncilResult(
            domain=domain,
            decision=decision,
            voices=voices,
            consensus=parsed["consensus"],
            agreement_score=round(agreement, 2),
            recommendation=parsed["recommendation"],
            computed_at=datetime.now(timezone.utc).isoformat(),
        )
        if oracle:
            result.oracle = self._adjudicate(
                decision=decision,
                context=context,
                council=result,
                oracle_model=oracle,
            )
        return result

    def _adjudicate(
        self,
        decision: str,
        context: str | None,
        council: CouncilResult,
        oracle_model: str,
    ) -> OracleVerdict:
        """Mythos-class adjudication over the council. Authority to override.

        Why: 5 mid-tier voices often hit "split" on hard calls. A flagship
        model reads all 5 verdicts and either ratifies or overrides. Brier-
        audited separately so we see when Oracle beats vs underperforms.
        """
        requested = "claude-fable-5" if oracle_model == "fable-5" else oracle_model
        # v0.3.1 safe_mode silently downgrades Mythos -> Sonnet 4.6
        downgraded = self.safe_mode and requested in MYTHOS_MODELS
        model_id = "claude-sonnet-4-6" if downgraded else requested
        voices_summary = "\n".join(
            f"- {v.voice_display} ({v.score}/100): {v.verdict}\n    strength: {v.strength}\n    gap: {v.gap}"
            for v in council.voices
        )
        system = (
            "You are the Oracle. The council of 5 specialists has deliberated. Your job: read the 5 verdicts, "
            "weigh which voice has the strongest grounding, and issue a single adjudication. You have authority "
            "to OVERRIDE the council if their consensus misses something a flagship-tier reasoner would catch.\n\n"
            "Output STRICT JSON. Be concrete. No hedging.\n\n"
            "Schema:\n"
            '{"recommendation":"go|wait|kill|split","score":<0-100>,"verdict":"<2-3 sentences naming which voices you side with>","override_reason":"<only if your recommendation differs from the council. Empty string otherwise.>"}'
        )
        user = (
            f"DECISION: {decision}\n\n"
            f"CONTEXT:\n{context or '(no additional context)'}\n\n"
            f"COUNCIL CONSENSUS: {council.recommendation} (agreement {council.agreement_score})\n"
            f"{council.consensus}\n\n"
            f"THE 5 VOICES:\n{voices_summary}\n\nAdjudicate."
        )
        msg = self._client.messages.create(
            model=model_id,
            max_tokens=800,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        text = msg.content[0].text if msg.content else ""
        parsed = json.loads(_strip_fences(text))
        override = parsed.get("override_reason") or None
        return OracleVerdict(
            model=model_id,
            recommendation=parsed["recommendation"],
            score=int(parsed["score"]),
            verdict=parsed["verdict"],
            override_reason=override if override else None,
            data_retention="30day-mythos" if model_id in MYTHOS_MODELS else "zero",
            downgraded=downgraded,
        )


def _strip_fences(text: str) -> str:
    cleaned = text.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    elif cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    return cleaned.strip()


__all__ = ["CouncilDiff", "CouncilResult", "CouncilVoice", "OracleVerdict", "DOMAIN_VOICES", "MYTHOS_MODELS"]
