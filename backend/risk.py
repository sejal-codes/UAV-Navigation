"""
risk.py
--------
Risk scoring model.

IMPORTANT (for viva honesty): this is a transparent, rule-based weighted
scoring model, not a trained machine-learning model. That is a completely
legitimate and common form of "AI-driven decision making" (it's the same
category of technique used in real aviation risk-assessment checklists),
but you should describe it accurately if asked:

  "It's a deterministic, weighted risk-scoring model informed by
   meteorological thresholds, not a trained ML classifier. We chose
   this because it's explainable and auditable -- you can always see
   exactly why a risk score was produced, which matters for safety
   systems."

If you want to upgrade this later to an actual trained ML model, you'd
need labeled historical flight-incident data, which we don't have, so
don't claim "trained on real flight data" -- that would be a made-up claim.
"""

from dataclasses import dataclass


@dataclass
class WeatherSnapshot:
    wind_speed_kmh: float
    visibility_km: float
    temperature_c: float
    rain_probability_pct: float
    condition: str  # e.g. "Clear", "Rain", "Thunderstorm", "Fog"


@dataclass
class RiskResult:
    score: float          # 0-100
    level: str             # "Safe" | "Caution" | "Danger"
    breakdown: dict        # per-factor contribution, for transparency


# Thresholds based on standard small-UAV operating guidance
# (e.g. DGCA/FAA recreational/light-UAV wind and visibility advisories).
# These are reasonable, defensible reference points -- cite them as
# "general UAV operating guidance thresholds," not as a proprietary model.
WIND_SAFE_KMH = 15
WIND_DANGER_KMH = 35

VISIBILITY_SAFE_KM = 8
VISIBILITY_DANGER_KM = 2

CONDITION_RISK = {
    "Clear": 0,
    "Clouds": 5,
    "Rain": 25,
    "Drizzle": 15,
    "Thunderstorm": 40,
    "Fog": 30,
    "Mist": 15,
    "Snow": 35,
}


def _scale(value: float, safe: float, danger: float) -> float:
    """
    Linearly scales a value into a 0-100 risk contribution.
    At or beyond 'safe' -> 0. At or beyond 'danger' -> 100.
    Handles both ascending (wind) and descending (visibility) scales
    by checking the direction safe->danger.
    """
    if safe == danger:
        return 0.0
    if danger > safe:  # higher value = more risk (wind)
        if value <= safe:
            return 0.0
        if value >= danger:
            return 100.0
        return (value - safe) / (danger - safe) * 100.0
    else:  # lower value = more risk (visibility)
        if value >= safe:
            return 0.0
        if value <= danger:
            return 100.0
        return (safe - value) / (safe - danger) * 100.0


def assess_risk(weather: WeatherSnapshot, storm_override: bool = False) -> RiskResult:
    """
    Computes a 0-100 composite risk score from current weather.

    Weighting rationale (kept simple and explainable on purpose):
      - Wind speed: 35% -- dominant factor for small UAV stability
      - Visibility: 30% -- critical for obstacle/terrain avoidance
      - Weather condition (storm/fog/etc.): 25% -- categorical hazard
      - Rain probability: 10% -- secondary/leading indicator

    storm_override: set True when the user triggers the "Simulate Storm"
    demo button. This forces a high-risk scenario deterministically, so
    the live demo is reliable in front of judges regardless of what the
    real weather happens to be that day.
    """
    if storm_override:
        weather = WeatherSnapshot(
            wind_speed_kmh=42.0,
            visibility_km=1.5,
            temperature_c=weather.temperature_c,
            rain_probability_pct=90.0,
            condition="Thunderstorm",
        )

    wind_risk = _scale(weather.wind_speed_kmh, WIND_SAFE_KMH, WIND_DANGER_KMH)
    vis_risk = _scale(weather.visibility_km, VISIBILITY_SAFE_KM, VISIBILITY_DANGER_KM)
    cond_risk = min(CONDITION_RISK.get(weather.condition, 10), 100)
    rain_risk = min(weather.rain_probability_pct, 100)

    score = (
        wind_risk * 0.35
        + vis_risk * 0.30
        + cond_risk * 0.25
        + rain_risk * 0.10
    )
    score = round(min(score, 100.0), 1)

    if score < 30:
        level = "Safe"
    elif score < 65:
        level = "Caution"
    else:
        level = "Danger"

    return RiskResult(
        score=score,
        level=level,
        breakdown={
            "wind_contribution": round(wind_risk * 0.35, 1),
            "visibility_contribution": round(vis_risk * 0.30, 1),
            "condition_contribution": round(cond_risk * 0.25, 1),
            "rain_contribution": round(rain_risk * 0.10, 1),
        },
    )
