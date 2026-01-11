# core/model.py

from pulp import LpBinary, LpContinuous, LpProblem, LpVariable


def build_variables(schedule_request):
    workers = schedule_request.workers
    days = schedule_request.days
    shifts = schedule_request.shifts

    # Decision variables
    x = {
        (w.id, d, t): LpVariable(f"x_{w.id}_{d}_{t}", cat=LpBinary)
        for w in workers
        for d in days
        for t in shifts
    }

    # Slack variables
    deficit = {
        (d, t): LpVariable(f"deficit_{d}_{t}", lowBound=0, cat=LpContinuous)
        for d in days
        for t in shifts
    }

    y_full = {
        (w.id, d): LpVariable(f"y_full_{w.id}_{d}", cat=LpBinary)
        for w in workers
        for d in days
    }

    y_split_MT = {
        (w.id, d): LpVariable(f"y_split_MT_{w.id}_{d}", cat=LpBinary)
        for w in workers
        for d in days
    }

    y_split_MN = {
        (w.id, d): LpVariable(f"y_split_MN_{w.id}_{d}", cat=LpBinary)
        for w in workers
        for d in days
    }

    y_split_MnN = {
        (w.id, d): LpVariable(f"y_split_MnN_{w.id}_{d}", cat=LpBinary)
        for w in workers
        for d in days
    }

    z = {  # Indica si un turno está vacío
        (d, t): LpVariable(f"empty_{d}_{t}", cat=LpBinary) for d in days for t in shifts
    }

    work = {  # Indica si un trabajador trabaja ese día
        (w.id, d): LpVariable(f"work_{w.id}_{d}", lowBound=0, upBound=1, cat=LpBinary)
        for w in workers
        for d in days
    }

    free2 = {  # Ventana de 2 días libres
        (w.id, d): LpVariable(f"free2_{w.id}_{d}", lowBound=0, upBound=1, cat=LpBinary)
        for w in workers
        for d in days
    }

    viol_rest = {  # Violación de descanso mínimo
        w.id: LpVariable(f"viol_rest_{w.id}", lowBound=0, upBound=1, cat=LpBinary)
        for w in workers
    }

    viol_max = {
        w.id: LpVariable(f"viol_max_{w.id}", lowBound=0, upBound=1, cat=LpBinary)
        for w in workers
    }
    # z = LpVariable.dicts("empty", (days, shifts), cat="Binary")

    return (
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
    )


def create_model(schedule_request):
    model = LpProblem("Horario_Camareros_Soft")
    variables = build_variables(schedule_request)
    return model, variables
