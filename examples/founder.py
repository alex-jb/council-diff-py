#!/usr/bin/env python3
"""Example: founder council deliberating on fundraising.

Usage:
    ANTHROPIC_API_KEY=... python3 examples/founder.py
"""
from council_diff import CouncilDiff
from council_diff.brier import add_prediction


council = CouncilDiff()

result = council.deliberate(
    domain="founder",
    decision="Should I raise a $1M seed round or stay bootstrapped?",
    context="""B2B SaaS for indie developers. $5K MRR, growing 20% MoM for 4 months.
Solo founder, currently coding 60h/week. 12 months personal runway.
Two YC partners have soft-circled $250K each.
Competitor just raised $8M Series A two weeks ago.""",
)

print(f"\n📊 RECOMMENDATION: {result.recommendation.upper()}")
print(f"Agreement: {result.agreement_score * 100:.0f}%\n")
print(f"Consensus:\n{result.consensus}\n")
print("━" * 60)
for v in result.voices:
    print(f"\n{v.voice_display} — {v.score}/100")
    print(f"  {v.verdict}")
    print(f"  + {v.strength}")
    print(f"  - {v.gap}")

# Log for Brier audit at 12mo
pred = add_prediction(
    decision=result.decision,
    domain=result.domain,
    recommendation=result.recommendation,
    agreement_score=result.agreement_score,
    voice_scores=[v.score for v in result.voices],
    resolve_by="2027-06-09",
    notes="Resolves on whether founder closed seed within 6mo OR proved bootstrap path",
)
print(f"\n💾 Brier-audit prediction logged: {pred.id}")
print(f"   resolve_by: {pred.resolve_by}")
