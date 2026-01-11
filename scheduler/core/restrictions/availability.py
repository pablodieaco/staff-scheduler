# core/restrictions/availability.py


def add_availability_constraints(model, variables, schedule_request):
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
    av = schedule_request.availability
    workers = schedule_request.workers
    days = schedule_request.days
    shifts = schedule_request.shifts

    for w in workers:
        for d in days:
            for t in shifts:
                # default = available
                available = 1

                if w.id in av and d in av[w.id] and t in av[w.id][d]:
                    available = av[w.id][d][t]  # = 0

                model += x[(w.id, d, t)] <= available

                # a[str(w.id)][str(d)][str(t)]
