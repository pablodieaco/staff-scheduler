# core/restrictions/coverage.py

from pulp import lpSum


def add_coverage_constraints(model, variables, schedule_request):
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
    m = schedule_request.demand
    days = schedule_request.days
    shifts = schedule_request.shifts

    for d in days:
        for t in shifts:
            model += (
                lpSum(x[(w.id, d, t)] for w in workers) + deficit[(d, t)] >= m[d][t]
            )


def add_empty_turn_penalty(model, variables, schedule_request):
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

    # Para cada turno
    # if sum(x_wdt) == 0 → z=1
    #
    # Con Big-M:
    for d in days:
        for t in shifts:
            model += lpSum(x[(w.id, d, t)] for w in workers) + z[(d, t)] >= 1
            # model += lpSum(x[(w.id, d, t)] for w in workers)  <= (len(workers)) * (
            #     1 - z[(d, t)]
            # )
