"""Enumerations for the MGAB — Autonomous Base Management Module."""

from __future__ import annotations

from enum import Enum


class SystemStatus(str, Enum):
    OPERATIONAL = "OPERACIONAL"
    ALERT       = "EM ALERTA"
    CRITICAL    = "CRÍTICO"
    RECOVERING  = "RECUPERANDO"

    def __str__(self) -> str:
        return self.value


class AlertType(str, Enum):
    ENERGY_DEFICIT       = "DÉFICIT ENERGÉTICO"
    PREDICTIVE_WARNING   = "ALERTA PREDITIVO"
    DUST_ACCUMULATION    = "ACÚMULO DE POEIRA"
    EQUIPMENT_FAILURE    = "FALHA DE EQUIPAMENTO"
    SENSOR_ERROR         = "ERRO DE SENSOR"
    MAINTENANCE_REQUIRED = "MANUTENÇÃO NECESSÁRIA"

    def __str__(self) -> str:
        return self.value


class AnomalyType(str, Enum):
    DUST_STORM        = "TEMPESTADE DE POEIRA"
    EQUIPMENT_FAILURE = "FALHA DE EQUIPAMENTO"
    SENSOR_ERROR      = "ERRO DE SENSOR"

    def __str__(self) -> str:
        return self.value


class ModuleName(str, Enum):
    LIFE_SUPPORT   = "LSS-01 Life Support"
    POWER_SYSTEMS  = "PWR-01 Power Systems"
    HABITAT        = "HAB-01 Habitat"
    MEDICAL        = "MED-01 Medical"
    COMMUNICATIONS = "COM-01 Communications"
    SCIENCE        = "SCI-01 Science Lab"
    LOGISTICS      = "LOG-01 Logistics"
    MINING         = "MIN-01 ISRU Mining"

    def __str__(self) -> str:
        return self.value
