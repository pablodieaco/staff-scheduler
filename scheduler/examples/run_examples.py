from scheduler.core.solve import solve_schedule
from scheduler.io.loader import load_data
from scheduler.io.output import print_schedule

if __name__ == "__main__":
    request = load_data(
        "scheduler/data/availability.json",
        "scheduler/data/demand.json",
        "scheduler/data/workers.json",
    )

    result = solve_schedule(request)

    print("Estado:", result["status"])
    print_schedule(result, request)
