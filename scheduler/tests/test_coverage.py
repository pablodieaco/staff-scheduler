from core.model import create_model
from core.restrictions.availability import add_availability_constraints
from core.restrictions.coverage import add_coverage_constraints
from pulp import PULP_CBC_CMD


class DummyWorker:
    def __init__(self, id, max_hours=40):
        self.id = id
        self.max_hours = max_hours


def test_coverage_minimum():
    workers = [DummyWorker(0), DummyWorker(1)]
    availability = {0: {0: {0: 1}}, 1: {0: {0: 1}}}
    demand = {0: {0: 1}}  # demand = 1

    request = type(
        "Req",
        (object,),
        {
            "workers": workers,
            "availability": availability,
            "demand": demand,
            "days": [0],
            "shifts": [0],
        },
    )

    model, variables = create_model(request)
    add_availability_constraints(model, variables, request)
    add_coverage_constraints(model, variables, request)

    model += 0
    model.solve(PULP_CBC_CMD(msg=False))
    x, *_ = variables

    # al menos uno asignado
    assert (x[(0, 0, 0)].value() + x[(1, 0, 0)].value()) >= 1
