# core/objective.py

from pulp import lpSum

from scheduler.config.settings import (
    P_COVER,
    P_EMPTY,
    P_FULL,
    P_LESS,
    P_MAX_HOURS,
    P_REST,
    P_SPLIT,
)


def set_objective(
    model,
    variables,
    schedule_request,
):
    (
        x,
        deficit,
        y_full,
        y_split_MT,
        y_split_MN,
        y_split_MnN,
        z,
        work,
        free2,
        viol_rest,
        viol_max,
    ) = variables

    workers = schedule_request.workers
    days = schedule_request.days
    shifts = schedule_request.shifts

    # Penalización por falta de cobertura
    obj = lpSum(P_COVER * deficit[d, t] for d, t in deficit)

    # Penalización por turnos vacíos
    obj += lpSum(P_EMPTY * z[(d, t)] for d, t in z)

    # Penalización por día completo trabajado
    obj += lpSum(P_FULL * y_full[w_d] for w_d in y_full)

    # Penalización por turnos partidos (dos tipos)
    obj += lpSum(
        P_SPLIT * (y_split_MT[w_d] + y_split_MN[w_d] + y_split_MnN[w_d])
        for w_d in y_split_MT
    )

    # Penalización por violación de descanso mínimo de 2 días
    obj += lpSum(P_REST * viol_rest[w] for w in viol_rest)

    # Penalización por exceder horas máximas
    obj += lpSum(P_MAX_HOURS * viol_max[w] for w in viol_max)

    # Maximizar número de horas trabajadas (minimizar diferencia de x)
    obj += lpSum(
        -1 * P_LESS * x[(w.id, d, t)] for w in workers for d in days for t in shifts
    )

    model += obj
