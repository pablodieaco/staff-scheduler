# core/restrictions/split_shifts.py


def add_split_shift_constraints(model, variables, schedule_request):
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

    # Mañana-Tarde sin Mediodía
    for w in workers:
        for d in days:
            model += (
                x[(w.id, d, 0)] + x[(w.id, d, 2)] - x[(w.id, d, 1)]
                <= 1 + y_split_MT[(w.id, d)]
            )

    # Mediodía-Noche sin Tarde
    for w in workers:
        for d in days:
            model += (
                x[(w.id, d, 1)] + x[(w.id, d, 3)] - x[(w.id, d, 2)]
                <= 1 + y_split_MN[(w.id, d)]
            )

    # Mañana-Noche prohibido
    for w in workers:
        for d in days:
            model += x[(w.id, d, 0)] + x[(w.id, d, 3)] <= 1 + y_split_MnN[(w.id, d)]
