from core.solve import solve_schedule


class DummyWorker:
    def __init__(self, id, max_hours=40):
        self.id = id
        self.max_hours = max_hours


def test_integration_basic():
    workers = [DummyWorker(0), DummyWorker(1)]
    availability = {
        0: {0: {0: 1, 1: 1}, 1: {0: 1, 1: 1}},
        1: {0: {0: 1, 1: 1}, 1: {0: 1, 1: 1}},
    }
    demand = {
        0: {0: 1, 1: 1},
        1: {0: 1, 1: 1},
    }

    req = type(
        "Req",
        (object,),
        {
            "workers": workers,
            "availability": availability,
            "demand": demand,
            "days": [0, 1],
            "shifts": [0, 1],
        },
    )

    result = solve_schedule(req)

    assert result["status"] in ("Optimal", "Feasible")
