from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import TypedDict

from .constants import MARS_SURFACE_IRRADIANCE_WM2, WIND_SPEED_SENSOR_FALLBACK_MS
from .enums import AlertType, SystemStatus


@dataclass
class Module:
    """A colony subsystem with energy consumption and operational priority."""

    name: str
    nominal_consumption_kw: float   # baseline consumption — source of truth
    current_consumption_kw: float   # actual consumption — may exceed nominal on failure
    priority: int                   # 1 = critical (last to shut down), higher = first to shut down
    active: bool
    sensor_operational: bool


@dataclass
class EnvironmentReading:
    """Sensor readings from the Martian environment for one simulation cycle."""

    wind_speed_ms: float | None           # None if sensor_error is active
    solar_irradiance_wm2: float | None    # None if sensor_error is active
    internal_temperature_c: float | None
    external_temperature_c: float | None
    dust_storm_intensity: float           # 0.0–1.0; always available (redundant sensors)


@dataclass
class EnergyState:
    """Energy generation, consumption, and storage state for one simulation cycle."""

    solar_generation_kw: float
    wind_generation_kw: float
    total_consumption_kw: float       # sum of current_consumption_kw across active modules
    battery_reserve_kwh: float
    solar_dust_accumulation: float    # 0.0–1.0 degradation factor on solar panels
    wind_blade_abrasion: float        # 0.0–1.0 degradation factor on wind turbine blades

    @property
    def balance_kw(self) -> float:
        """Net energy balance: generation minus consumption."""
        return self.solar_generation_kw + self.wind_generation_kw - self.total_consumption_kw


@dataclass
class OnlineRegression:
    """Welford incremental linear regression state. O(1) per update, O(1) memory."""

    count: int = 0
    mean_independent: float = 0.0
    mean_dependent: float = 0.0
    variance_independent: float = 0.0   # running sum of squared deviations (not divided by n)
    covariance: float = 0.0             # running sum of cross-deviations (not divided by n)

    @property
    def slope(self) -> float | None:
        """Regression slope. None if insufficient variance in independent variable."""
        if self.variance_independent == 0.0:
            return None
        return self.covariance / self.variance_independent

    @property
    def intercept(self) -> float | None:
        """Regression intercept. None if slope cannot be computed."""
        computed_slope = self.slope
        if computed_slope is None:
            return None
        return self.mean_dependent - computed_slope * self.mean_independent

    def predict(self, independent_value: float) -> float | None:
        """Predicted dependent value for a given independent value. None if not enough data."""
        computed_slope = self.slope
        computed_intercept = self.intercept
        if computed_slope is None or computed_intercept is None:
            return None
        return computed_intercept + computed_slope * independent_value


@dataclass
class ForecastState:
    """Two independent online regressions tracking energy trends."""

    wind_to_generation: OnlineRegression    # wind speed (m/s) → wind generation (kW)
    cycle_to_balance: OnlineRegression      # cycle number → energy balance (kW)


class AlertEntry(TypedDict):
    """Typed schema for entries in the colony alert queue."""

    type: AlertType
    detail: str
    cycle: int
    is_daytime: bool


@dataclass
class ColonyState:
    """Complete colony state, evolving incrementally across simulation cycles."""

    cycle: int
    is_daytime: bool              # True = solar generation active; False = no solar input
    environment: EnvironmentReading
    energy: EnergyState
    modules: list[Module]
    forecast: ForecastState
    status: SystemStatus
    energy_history: list[float]       # balance_kw per cycle
    wind_history: list[float]         # wind_speed_ms per cycle
    dust_history: list[float]         # solar_dust_accumulation per cycle
    alert_queue: deque[AlertEntry]    # alert entries in arrival order (FIFO)
    active_storm_cycles_remaining: int = 0
    last_valid_solar_irradiance_wm2: float = MARS_SURFACE_IRRADIANCE_WM2
    last_valid_wind_speed_ms: float = WIND_SPEED_SENSOR_FALLBACK_MS
    shutdown_stack: list[str] = field(default_factory=list)
