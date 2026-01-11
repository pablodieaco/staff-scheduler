# scheduler/services/builder.py

from scheduler.core.domain import ScheduleRequest, Worker


class RequestBuilder:
    @staticmethod
    def from_dict(workers, availability, demand):
        """
        Construye un ScheduleRequest a partir de tres estructuras en memoria:
        - workers: lista de dicts [{id, name, max_hours}]
        - availability: dict {worker_id -> {day -> {shift -> 0/1}}}
        - demand: dict {day -> {shift -> min_workers}}
        """
        worker_objs = [
            Worker(
                id=w["id"],
                name=w["name"],
                max_hours=w.get("max_hours", 40),
            )
            for w in workers
        ]

        return ScheduleRequest(
            workers=worker_objs, availability=availability, demand=demand
        )
