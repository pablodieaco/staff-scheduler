import pandas as pd

from scheduler.config.constants import (
    IDX_TO_DAY,
    IDX_TO_SHIFT,
)


def result_to_df(result, schedule_request):
    variables = result["variables"]
    x = variables["x"]
    workers = {w.id: w.name for w in schedule_request.workers}

    rows = []
    for (w, d, t), val in x.items():
        if val.value() == 1:
            rows.append({"Día": d, "Turno": t, "Trabajador": workers[w]})
    df = pd.DataFrame(rows)
    return df


def schedule_pivot(df):
    # Agrupar trabajadores en un string
    agg = df.groupby(["Día", "Turno"])["Trabajador"].apply(lambda x: ", ".join(x))
    pivot = agg.unstack(fill_value="")
    return pivot


def schedule_db_to_pivot(rows, request):
    """
    rows: [
        {"day":0, "shift":1, "worker_id":4},
        ...
    ]
    """
    if not rows:
        return None

    # map worker_id → name
    workers = {w.id: w.name for w in request.workers}

    df = pd.DataFrame(rows)
    df["Trabajador"] = df["worker_id"].map(workers)
    df["Día"] = df["day"].map(IDX_TO_DAY)
    df["Turno"] = df["shift"].map(IDX_TO_SHIFT)

    pivot = (
        df.groupby(["Día", "Turno"])["Trabajador"]
        .apply(lambda x: ", ".join(x))
        .unstack(fill_value="")
    )

    return pivot


def hours_per_worker(df_raw, turn_hours):
    # df_raw: Día, Turno, Trabajador
    # turn_hours: dict(int→float)

    # Añadir columna con horas de ese turno
    df_raw["Horas"] = df_raw["Turno"].map(turn_hours)

    # Agrupar por trabajador
    res = (
        df_raw.groupby("Trabajador")["Horas"]
        .sum()
        .reset_index()
        .sort_values("Horas", ascending=False)
    )

    return res


def day_worker_matrix(df_raw, sort_by_worker=False):
    """
    df_raw:
    Día | Turno | Trabajador
    """
    # Crear columna con valor "Sí"
    df_raw["Asignado"] = "Sí"

    # Pivot → filas (Día, Trabajador), columnas (Turno)
    matrix = df_raw.pivot_table(
        index=["Día", "Trabajador"],
        columns="Turno",
        values="Asignado",
        aggfunc=lambda x: "Sí",
        fill_value="No",
    )

    # Ordenar índices y columnas
    matrix = matrix.sort_index()
    matrix = matrix.sort_index(axis=1)

    if sort_by_worker:
        matrix = matrix.sort_index(level="Trabajador")

    return matrix.reset_index()


def schedule_db_to_df(rows, request):
    """
    rows: list of dicts {day, shift, worker_id}
    return: dataframe Día | Turno | Trabajador
    """
    if not rows:
        return pd.DataFrame(columns=["Día", "Turno", "Trabajador"])

    workers = {w.id: w.name for w in request.workers}

    df = pd.DataFrame(rows)
    df["Trabajador"] = df["worker_id"].map(workers)
    df["Día"] = df["day"]
    df["Turno"] = df["shift"]
    return df[["Día", "Turno", "Trabajador"]]
