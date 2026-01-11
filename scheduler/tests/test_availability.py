from core.model import create_model
from core.restrictions.availability import add_availability_constraints
from pulp import PULP_CBC_CMD


class DummyWorker:
    def __init__(self, id, max_hours=40):
        self.id = id
        self.max_hours = max_hours


def test_availability_not_assigned():
    # Datos mínimos
    worker = DummyWorker(0)
    availability = {0: {0: {0: 0}}}  # worker=0, day=0, shift=0 -> not available
    demand = {0: {0: 0}}  # no demand
    request = type(
        "Req",
        (object,),
        {
            "workers": [worker],
            "availability": availability,
            "demand": demand,
            "days": [0],
            "shifts": [0],
        },
    )

    # modelo
    model, variables = create_model(request)
    add_availability_constraints(model, variables, request)

    # objective dummy
    model += 0

    model.solve(PULP_CBC_CMD(msg=False))
    x, *_ = variables

    assert x[(0, 0, 0)].value() == 0
