# config/settings.py

P_COVER = 100.0  # penalización déficit cobertura
P_FULL = 100.0  # penalización día completo
P_SPLIT = 5.0  # penalización turno partido
P_EMPTY = 1000  # o 1000 según pesos
P_REST = 10.0  # penalización violación descanso mínimo
P_MAX_HOURS = 10.0  # penalización exceder horas máximas
P_LESS = 0.5  # penalización horas menos que mínimo
DEFAULT_MAX_HOURS = 40
TURN_HOURS = {
    0: 4,  # mañana de 8 a 13
    1: 3,  # mediodía de 13 a 16
    2: 5,  # tarde de 16 a 21
    3: 3,  # noche de 21 a 24
}

M_BIG = 4  # Big-M turnos por día
SOLVER_TIME_LIMIT = 120  # segundos límite de tiempo del solver
