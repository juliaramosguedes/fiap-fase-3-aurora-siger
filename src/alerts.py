"""Alert queue management for the MGAB — Autonomous Base Management Module."""

from src.enums import AlertType
from src.models import AlertEntry, ColonyState


def enqueue_alert(state: ColonyState, alert_type: AlertType, detail: str) -> None:
    """Append a typed alert entry to the colony alert queue (FIFO)."""
    state.alert_queue.append(AlertEntry(
        type=alert_type,
        detail=detail,
        cycle=state.cycle,
        is_daytime=state.is_daytime,
    ))
