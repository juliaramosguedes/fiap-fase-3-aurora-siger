"""
Forecast module for the MGAB — Autonomous Base Management Module.

Implements incremental (online) linear regression using the Welford method.
O(1) per update, O(1) memory — no history stored, no batch recomputation.

Two independent regressions are maintained in ForecastState:
  1. wind_to_generation: wind speed (m/s) -> wind generation (kW)
     Physical relationship; helps predict generation from forecast wind speed.
  2. cycle_to_balance: cycle number -> energy balance (kW)
     Operational trend; detects deteriorating balance over time.

Predictions are only used when count >= FORECAST_MIN_CYCLES.
Below that threshold the system operates on current state only.
"""

from src.constants import FORECAST_HORIZON_CYCLES, FORECAST_MIN_CYCLES
from src.models import ColonyState, OnlineRegression


# ---------------------------------------------------------------------------
# Welford incremental update
# ---------------------------------------------------------------------------


def update_regression(
    regression: OnlineRegression,
    independent_value: float,
    dependent_value: float,
) -> None:
    """
    Update a running linear regression with one new observation. O(1).

    Welford method — numerically stable incremental update.
    Mutates regression in place.

    Variables follow Welford (1962):
      variance_independent accumulates sum of squared deviations (not divided by n).
      covariance accumulates sum of cross-deviations (not divided by n).
      slope = covariance / variance_independent when variance_independent > 0.
    """
    regression.count += 1
    delta_independent = independent_value - regression.mean_independent
    regression.mean_independent += delta_independent / regression.count
    regression.mean_dependent += (dependent_value - regression.mean_dependent) / regression.count
    regression.variance_independent += delta_independent * (independent_value - regression.mean_independent)
    regression.covariance += delta_independent * (dependent_value - regression.mean_dependent)


# ---------------------------------------------------------------------------
# Forecast queries
# ---------------------------------------------------------------------------


def is_regression_reliable(regression: OnlineRegression) -> bool:
    """True if the regression has enough data points to produce a trustworthy prediction."""
    return regression.count >= FORECAST_MIN_CYCLES


def predict_balance_at_cycle(
    regression: OnlineRegression,
    future_cycle: int,
) -> float | None:
    """
    Predicted energy balance (kW) at a future cycle number.

    Returns None if regression is not yet reliable.
    Uses OnlineRegression.predict() which returns None when slope is undefined.
    """
    if not is_regression_reliable(regression):
        return None
    return regression.predict(float(future_cycle))


def cycles_until_threshold_crossed(
    regression: OnlineRegression,
    current_cycle: int,
    threshold_kw: float,
) -> int | None:
    """
    Estimate how many cycles until the balance crosses threshold_kw.

    Returns None if regression is unreliable or slope is non-negative
    (balance is stable or improving — no crossing expected).
    Returns 0 if balance has already crossed the threshold.
    """
    if not is_regression_reliable(regression):
        return None

    slope = regression.slope
    intercept = regression.intercept

    if slope is None or intercept is None:
        return None

    if slope >= 0:
        return None  # trend is stable or improving

    # Solve: intercept + slope * cycle = threshold_kw
    crossing_cycle = (threshold_kw - intercept) / slope
    remaining = crossing_cycle - current_cycle

    if remaining <= 0:
        return 0

    return max(0, int(remaining))


def will_cross_threshold_soon(
    regression: OnlineRegression,
    current_cycle: int,
    threshold_kw: float,
) -> bool:
    """
    True if the regression predicts the balance will cross threshold_kw
    within FORECAST_HORIZON_CYCLES cycles.
    """
    remaining = cycles_until_threshold_crossed(regression, current_cycle, threshold_kw)
    if remaining is None:
        return False
    return remaining <= FORECAST_HORIZON_CYCLES


# ---------------------------------------------------------------------------
# Main forecast update — called once per cycle
# ---------------------------------------------------------------------------


def update_forecast(state: ColonyState) -> None:
    """
    Feed the current cycle's observations into both regressions.

    Called after update_energy_state so energy values are already computed.
    Updates:
      wind_to_generation: wind speed -> wind generation
      cycle_to_balance: cycle number -> energy balance
    """
    energy = state.energy

    wind_speed = state.last_valid_wind_speed_ms  # already resolved in energy.py

    update_regression(
        state.forecast.wind_to_generation,
        independent_value=wind_speed,
        dependent_value=energy.wind_generation_kw,
    )

    update_regression(
        state.forecast.cycle_to_balance,
        independent_value=float(state.cycle),
        dependent_value=energy.balance_kw,
    )
