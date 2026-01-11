# io/output.py


def print_schedule(result, schedule_request):
    x = result["x"]
    days = schedule_request.days
    shifts = schedule_request.shifts
    workers = {w.id: w for w in schedule_request.workers}

    for d in days:
        print(f"\n=== Día {d} ===")
        for t in shifts:
            assigned = [
                workers[w].name
                for (w, dd, tt) in x
                if dd == d and tt == t and x[(w, d, t)].value() == 1
            ]
            print(f" Turno {t}: {assigned}")
