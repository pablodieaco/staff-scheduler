# scheduler/io/loader.py

from scheduler.config.settings import DEFAULT_MAX_HOURS
from scheduler.core.domain import ScheduleRequest, Worker
from scheduler.services.repository import SchedulerRepository


def load_data(db_path: str = "scheduler.db") -> ScheduleRequest:
    """
    Carga workers, availability y demand desde SQLite
    y construye un ScheduleRequest para el solver.
    """
    repo = SchedulerRepository(db_path)

    # 1. Load raw dicts from DB
    workers_data = repo.load_workers()
    availability = repo.load_availability()
    demand = repo.load_demand()

    # 2. Build Workers (domain objects)
    workers = [
        Worker(
            id=w["id"],
            name=w["name"],
            max_hours=w.get("max_hours", DEFAULT_MAX_HOURS),
        )
        for w in workers_data
    ]

    # 3. Create ScheduleRequest
    return ScheduleRequest(workers, availability, demand)


# import json

# from scheduler.config.settings import DEFAULT_MAX_HOURS
# from scheduler.core.domain import ScheduleRequest, Worker


# def _str_dict_to_int(d):
#     """Convierte recursivamente claves string de dict a int"""
#     if isinstance(d, dict):
#         return {int(k): _str_dict_to_int(v) for k, v in d.items()}
#     return d


# def load_data(av_file, demand_file, workers_file):
#     # Load availability
#     with open(av_file, encoding="utf-8") as f:
#         availability_raw = json.load(f)
#     availability = _str_dict_to_int(availability_raw)

#     # Load demand
#     with open(demand_file, encoding="utf-8") as f:
#         demand_raw = json.load(f)
#     demand = _str_dict_to_int(demand_raw)

#     # Load workers
#     with open(workers_file, encoding="utf-8") as f:
#         workers_data = json.load(f)

#     workers = [
#         Worker(
#             id=w["id"], name=w["name"], max_hours=w.get("max_hours", DEFAULT_MAX_HOURS)
#         )
#         for w in workers_data
#     ]

#     return ScheduleRequest(workers, availability, demand)
