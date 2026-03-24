"""Recommendation engine for agriculture & climate insights.

Uses very lightweight heuristic rules over the generated insight text
(and optional metadata) to propose actionable recommendations.
"""

from __future__ import annotations

from typing import Iterable, List, Optional


def generate_recommendations(
    insights: str,
    domain: Optional[str] = None,
    entities: Optional[Iterable[str]] = None,
) -> List[str]:
    """Generate actionable recommendations from insight text.

    This intentionally avoids external model dependencies and instead
    applies transparent rule-based templates over the insight text.
    """

    text = (insights or "").lower()
    entities_lower = " ".join((entities or [])).lower()

    recommendations: List[str] = []

    # Climate & water-related guidance
    if "rainfall" in text or "rainfall" in entities_lower:
        recommendations.append(
            "Monitor seasonal rainfall trends and plan irrigation to compensate during low-rainfall periods."
        )
        recommendations.append(
            "Consider moisture-conserving practices such as mulching or contour bunding to stabilise yield under variable rainfall."
        )

    if "drought" in text or "drought" in entities_lower:
        recommendations.append(
            "Adopt drought-tolerant crop varieties and adjust sowing dates to avoid peak water stress periods."
        )

    if "temperature" in text or "heat" in text or "heat" in entities_lower:
        recommendations.append(
            "Use heat-resilient crop varieties and explore shade or micro-climate management where feasible."
        )

    # Soil & nutrient management
    if "soil moisture" in text or "soil" in entities_lower:
        recommendations.append(
            "Regularly monitor soil moisture and organic matter to fine-tune irrigation and fertiliser schedules."
        )

    if "nitrogen" in text or "fertilizer" in text or "fertiliser" in text:
        recommendations.append(
            "Optimise nitrogen and fertiliser use based on soil tests to improve yield while reducing losses."
        )

    # Data / analytics
    if domain and domain.lower().startswith("data"):
        recommendations.append(
            "Evaluate predictive models on recent seasons of data to validate their performance before large-scale adoption."
        )

    if "model" in text and "prediction" in text:
        recommendations.append(
            "Incorporate uncertainty estimates (confidence intervals or scenario ranges) when communicating model-based yield forecasts."
        )

    # General fallback guidance
    if not recommendations:
        recommendations.append(
            "Review local agronomic advisories and historical field data to tailor interventions to your specific region."
        )
        recommendations.append(
            "Use the knowledge graph to explore related factors (climate, soil, management) before making major decisions."
        )

    return recommendations
