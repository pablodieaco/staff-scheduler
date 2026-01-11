from core.model import create_model
from core.restrictions.availability import add_availability_constraints
from core.restrictions.rest import add_rest_constraints
from pulp import PULP_CBC_CMD


class DummyWorker:
    def __init__(self, id, max_hours=40):
        self.id = id
        self.max_hours = max_hours


def test_rest_night_to_morning():
    worker = DummyWorker(0)
    availability = {
        0: {0: {3: 1}, 1: {0: 1}}  # night day0, morning day1 both available
    }
    demand = {
        0: {3: 0},
        1: {0: 0},
    }

    req = type(
        "Req",
        (object,),
        {
            "workers": [worker],
            "availability": availability,
            "demand": demand,
            "days": [0, 1],
            "shifts": [0, 3],
        },
    )

    model, variables = create_model(req)
    add_availability_constraints(model, variables, req)
    add_rest_constraints(model, variables, req)

    # Try to maximize assignments to "break" constraint if possible
    x, *_ = variables
    model += x[(0, 0, 3)] + x[(0, 1, 0)]

    model.solve(PULP_CBC_CMD(msg=False))

    # constraint should prevent both =1
    assert x[(0, 0, 3)].value() + x[(0, 1, 0)].value() <= 1
