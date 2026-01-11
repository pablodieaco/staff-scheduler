# core/domain.py

from typing import Dict, List


class Worker:
    def __init__(self, id: int, name: str, max_hours: int):
        self.id = id
        self.name = name
        self.max_hours = max_hours


class ScheduleRequest:
    """
    Representa la información necesaria para generar un horario:
    - workers
    - disponibilidad
    - demanda mínimos m[d][t]
    """

    def __init__(self, workers: List[Worker], availability: Dict, demand: Dict):
        self.workers = workers
        self.availability = availability  # a[w][d][t]
        self.demand = demand  # m[d][t]

    @property
    def days(self):
        return list(sorted(self.demand.keys()))

    @property
    def shifts(self):
        # asumimos todos los días tienen todos los turnos cargados
        d0 = self.days[0]
        return list(sorted(self.demand[d0].keys()))
