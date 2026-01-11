# core/restrictions/rest.py


def add_rest_constraints(model, variables, schedule_request):
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

    for w in workers:
        for d in days[:-1]:
            model += x[(w.id, d, 3)] + x[(w.id, d + 1, 0)] <= 1
