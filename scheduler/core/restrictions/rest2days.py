# core/restrictions/rest2days.py

from pulp import lpSum


def add_rest2days_constraints(model, variables, schedule_request):
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

    # 1) work[w,d] = 1 si trabaja cualquier turno
    for w in workers:
        for d in days:
            # si hay cualquier turno asignado => work=1
            model += (
                lpSum(x[(w.id, d, t)] for t in shifts) <= len(shifts) * work[(w.id, d)]
            )
            # si no hay turnos => work=0
            # model += (
            #     lpSum(x[(w.id, d, t)] for t in shifts) >= work[(w.id, d)]
            # )

    # 2) detectar bloques de 2 días de descanso consecutivos
    for w in workers:
        for d in days[:-1]:
            # free2 = 1 si no trabaja ni d ni d+1
            model += free2[(w.id, d)] <= 1 - work[(w.id, d)]
            model += free2[(w.id, d)] <= 1 - work[(w.id, d + 1)]
            # model += free2[(w.id, d)] >= 1 - work[(w.id, d)]
            # model += free2[(w.id, d)] >= 1 - work[(w.id, d + 1)]
            # model += free2[(w.id, d)] >= 1 - 0.5 * (
            #     work[(w.id, d)] + work[(w.id, d + 1)]
            # )

        # ultimo dia y primer dia (es modular)
        d = days[-1]
        model += free2[(w.id, d)] <= 1 - work[(w.id, d)]
        model += free2[(w.id, d)] <= 1 - work[(w.id, days[0])]
        # model += free2[(w.id, d)] >= 1 - 0.5 * (work[(w.id, d)] + work[(w.id, days[0])])

    # 3) al menos una ventana libre, o viol_rest = 1
    for w in workers:
        model += lpSum(free2[(w.id, d)] for d in days) + viol_rest[w.id] >= 1
