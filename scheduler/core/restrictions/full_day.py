# core/restrictions/full_day.py

from pulp import lpSum


def add_full_day_constraints(model, variables, schedule_request):
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

    for w in workers:
        for d in days:
            model += (
                lpSum(x[(w.id, d, t)] for t in shifts)
                <= len(shifts) + y_full[(w.id, d)]
            )
