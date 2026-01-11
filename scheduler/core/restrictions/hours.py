# core/restrictions/hours.py

from pulp import lpSum

from scheduler.config.settings import TURN_HOURS


def add_hour_constraints(model, variables, schedule_request):
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
        model += (
            lpSum(TURN_HOURS[t] * x[(w.id, d, t)] for d in days for t in shifts)
            + viol_max[w.id]
            <= w.max_hours
        )
