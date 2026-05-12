import argparse
import random

from src.constants import RANDOM_SEED
from src.models import ColonyState
from src.scenarios import default_scenario, random_scenario
from src.simulation import run_simulation


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="main",
        description="MGAB — Módulo de Gerenciamento Autônomo de Base · Aurora Siger",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=48,
        help="Número de ciclos a simular (default: 48; cada ciclo = meio sol marciano)",
    )
    parser.add_argument(
        "--random",
        action="store_true",
        help="Iniciar com condições aleatórias dentro dos limites marcianos reais",
    )
    parser.add_argument(
        "--anomaly",
        type=float,
        default=0.0,
        help="Probabilidade de anomalia por ciclo, entre 0.0 e 1.0 (default: 0.0)",
    )
    parser.add_argument(
        "--stress",
        action="store_true",
        help=(
            "Modo stress: força tempestade global contínua desde o início. "
            "Simula tempestade global marciana (semanas a meses). "
            "Default: 200 ciclos (~100 sols)."
        ),
    )
    return parser.parse_args()


def _apply_stress_mode(state: ColonyState, cycles: int) -> None:
    """Force a global dust storm lasting the full simulation. Source: ScienceDirect (2024)."""
    intensity = random.uniform(0.7, 1.0)
    state.environment.dust_storm_intensity = intensity
    state.active_storm_cycles_remaining = cycles


if __name__ == "__main__":
    args = _parse_args()

    random.seed(RANDOM_SEED)

    if args.anomaly < 0.0 or args.anomaly > 1.0:
        print("Erro: --anomaly deve estar entre 0.0 e 1.0")
        raise SystemExit(1)

    cycles = args.cycles
    if args.stress and cycles == 48:
        cycles = 200

    state = random_scenario() if args.random else default_scenario()

    if args.stress:
        _apply_stress_mode(state, cycles)

    anomaly_probability = args.anomaly if not args.stress else 0.15

    run_simulation(state, cycles=cycles, anomaly_probability=anomaly_probability)
