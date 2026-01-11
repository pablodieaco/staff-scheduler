from pulp import PULP_CBC_CMD, LpStatus

from scheduler.config.settings import SOLVER_TIME_LIMIT
from scheduler.core.model import create_model
from scheduler.core.objective import set_objective
from scheduler.core.restrictions_manager import apply_restrictions


def solve_schedule(schedule_request, solver=None, restrictions=None):
    model, variables = create_model(schedule_request)

    apply_restrictions(model, variables, schedule_request, restrictions)
    set_objective(model, variables, schedule_request)

    solver = solver or PULP_CBC_CMD(msg=False, timeLimit=SOLVER_TIME_LIMIT)
    model.solve(solver)

    # unpack variables tuple
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

    variables = {
        "x": x,
        "deficit": deficit,
        "y_full": y_full,
        "y_split_MT": y_split_MT,
        "y_split_MN": y_split_MN,
        "y_split_MnN": y_split_MnN,
        "z": z,
        "work": work,
        "free2": free2,
        "viol_rest": viol_rest,
        "viol_max": viol_max,
    }

    return {"status": LpStatus[model.status], "model": model, "variables": variables}
