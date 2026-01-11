# scheduler/services/repository.py

import sqlite3
from typing import Any, Dict, List

from scheduler.config.settings import DEFAULT_MAX_HOURS


class SchedulerRepository:
    """
    Repository simple basado en SQLite para cargar y guardar:
    - workers
    - availability
    - demand
    """

    def __init__(self, db_path: str = "scheduler.db"):
        self.db_path = db_path
        self._init_schema()

    # -----------------------------------------
    # Conexión
    # -----------------------------------------
    def _connect(self):
        return sqlite3.connect(self.db_path)

    # -----------------------------------------
    # Crear tablas si no existen
    # -----------------------------------------
    def _init_schema(self):
        conn = self._connect()
        cur = conn.cursor()

        # Tabla de trabajadores
        cur.execute("""
        CREATE TABLE IF NOT EXISTS workers (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            max_hours INTEGER NOT NULL
        );
        """)

        # Disponibilidad: worker-day-shift
        cur.execute("""
        CREATE TABLE IF NOT EXISTS availability (
            worker_id INTEGER,
            day INTEGER,
            shift INTEGER,
            available INTEGER,
            PRIMARY KEY(worker_id, day, shift),
            FOREIGN KEY(worker_id) REFERENCES workers(id)
        );
        """)

        # Demanda por day-shift
        cur.execute("""
        CREATE TABLE IF NOT EXISTS demand (
            day INTEGER,
            shift INTEGER,
            min_workers INTEGER,
            PRIMARY KEY(day, shift)
        );
        """)

        # Horario generado
        cur.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            day INTEGER,
            shift INTEGER,
            worker_id INTEGER,
            FOREIGN KEY(worker_id) REFERENCES workers(id)
        );
        """)

        conn.commit()
        conn.close()

    # -----------------------------------------
    # Métodos de persistencia
    # -----------------------------------------
    def save_workers(self, workers: List[Dict[str, Any]]):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("DELETE FROM workers;")

        # print(workers)

        for w in workers:
            # cleanup de tipos
            wid = w.get("id")
            name = w.get("name")
            maxh = w.get("max_hours", DEFAULT_MAX_HOURS)

            if isinstance(maxh, list):
                maxh = maxh[0] if maxh else DEFAULT_MAX_HOURS
            if isinstance(name, list):
                name = name[0] if name else None
            if isinstance(wid, list):
                wid = wid[0] if wid else None

            # saltar filas incompletas
            if wid is None or name is None:
                continue

            # convertir a tipos soportados
            try:
                wid = int(wid)
            except:  # noqa: E722
                continue

            try:
                maxh = int(maxh)
            except:  # noqa: E722
                maxh = DEFAULT_MAX_HOURS

            # trim name
            name = str(name).strip()
            if not name:
                name = f"Worker_{wid}"

            # print(f"Inserting worker: id={wid}, name={name}, max_hours={maxh}")

            cur.execute(
                """
                INSERT INTO workers(id, name, max_hours)
                VALUES (?, ?, ?)
            """,
                (wid, name, maxh),
            )

        conn.commit()
        conn.close()

    def save_availability(self, availability):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("DELETE FROM availability")

        for wid, days in availability.items():
            for day_idx, shifts in days.items():
                for shift_idx in shifts.keys():
                    cur.execute(
                        """
                        INSERT INTO availability(worker_id, day, shift, available)
                        VALUES (?, ?, ?, ?)
                        """,
                        (int(wid), int(day_idx), int(shift_idx), 0),
                    )

        conn.commit()
        conn.close()

    def save_demand(self, demand: Dict[int, Dict[int, int]]):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("DELETE FROM demand;")
        print(demand)
        for d, shifts in demand.items():
            for t, val in shifts.items():
                cur.execute(
                    """
                    INSERT INTO demand(day, shift, min_workers)
                    VALUES (?, ?, ?)
                """,
                    (d, t, val),
                )

        conn.commit()
        conn.close()

    # -----------------------------------------
    # Métodos de lectura
    # -----------------------------------------
    def load_workers(self) -> List[Dict[str, Any]]:
        conn = self._connect()
        cur = conn.cursor()

        rows = cur.execute("SELECT id, name, max_hours FROM workers").fetchall()
        conn.close()

        return [{"id": r[0], "name": r[1], "max_hours": r[2]} for r in rows]

    def load_availability(self) -> Dict[int, Dict[int, Dict[int, int]]]:
        conn = self._connect()
        cur = conn.cursor()

        rows = cur.execute(
            "SELECT worker_id, day, shift, available FROM availability"
        ).fetchall()
        conn.close()

        result = {}
        for wid, d, t, val in rows:
            result.setdefault(wid, {}).setdefault(d, {})[t] = val

        return result

    def load_demand(self) -> Dict[int, Dict[int, int]]:
        conn = self._connect()
        cur = conn.cursor()

        rows = cur.execute("SELECT day, shift, min_workers FROM demand").fetchall()
        conn.close()

        result = {}
        for d, t, val in rows:
            result.setdefault(d, {})[t] = val

        return result

    def save_schedule(self, df):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("DELETE FROM schedule;")

        for _, row in df.iterrows():
            cur.execute(
                """
                INSERT INTO schedule(day, shift, worker_id)
                VALUES (?, ?, ?)
                """,
                (int(row["Día"]), int(row["Turno"]), int(row["worker_id"])),
            )

        conn.commit()
        conn.close()

    def save_schedule_from_result(self, result):
        variables = result["variables"]
        x = variables["x"]
        conn = self._connect()
        cur = conn.cursor()

        # print(variables)

        cur.execute("DELETE FROM schedule;")

        for (wid, d, t), val in x.items():
            if val.value() == 1:
                cur.execute(
                    """
                    INSERT INTO schedule(day, shift, worker_id)
                    VALUES (?,?,?)
                    """,
                    (d, t, wid),
                )

        conn.commit()
        conn.close()

    def load_schedule(self):
        conn = self._connect()
        cur = conn.cursor()

        cur.execute("""
            SELECT day, shift, worker_id
            FROM schedule
            ORDER BY day, shift
        """)

        rows = cur.fetchall()
        conn.close()

        # devolver una lista de dicts
        return [{"day": r[0], "shift": r[1], "worker_id": r[2]} for r in rows]
