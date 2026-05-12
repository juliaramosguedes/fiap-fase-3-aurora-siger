from __future__ import annotations

from .constants import FORECAST_HORIZON_CYCLES, FORECAST_MIN_CYCLES
from .models import ColonyState, OnlineRegression


def update_regression(
    regression: OnlineRegression,
    independent_value: float,
    dependent_value: float,
) -> None:
    """Welford incremental update — O(1). Mutates regression in place. Source: Welford (1962)."""
    regression.count += 1
    delta_independent = independent_value - regression.mean_independent
    regression.mean_independent += delta_independent / regression.count
    regression.mean_dependent += (dependent_value - regression.mean_dependent) / regression.count
    regression.variance_independent += delta_independent * (independent_value - regression.mean_independent)
    regression.covariance += delta_independent * (dependent_value - regression.mean_dependent)


def is_regression_reliable(regression: OnlineRegression) -> bool:
    """True if the regression has enough data points to produce a trustworthy prediction."""
    return regression.count >= FORECAST_MIN_CYCLES


def predict_balance_at_cycle(
    regression: OnlineRegression,
    future_cycle: int,
) -> float | None:
    """Predicted energy balance (kW) at a future cycle. None if regression is not yet reliable."""
    if not is_regression_reliable(regression):
        return None
    return regression.predict(float(future_cycle))


def cycles_until_threshold_crossed(
    regression: OnlineRegression,
    current_cycle: int,
    threshold_kw: float,
) -> int | None:
    """Cycles until balance crosses threshold_kw. None if stable or regression unreliable."""
    if not is_regression_reliable(regression):
        return None

    slope = regression.slope
    intercept = regression.intercept

    if slope is None or intercept is None:
        return None

    if slope >= 0:
        return None

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
    """True if balance will cross threshold_kw within FORECAST_HORIZON_CYCLES cycles."""
    remaining = cycles_until_threshold_crossed(regression, current_cycle, threshold_kw)
    if remaining is None:
        return False
    return remaining <= FORECAST_HORIZON_CYCLES


def update_forecast(state: ColonyState) -> None:
    """Feed current cycle observations into wind_to_generation and cycle_to_balance regressions."""
    energy = state.energy

    wind_speed = state.last_valid_wind_speed_ms

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
