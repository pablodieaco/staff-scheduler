import pandas as pd
import streamlit as st

from scheduler.config.constants import (
    DAY_NAMES,
    DAY_TO_IDX,
    IDX_TO_DAY,
    IDX_TO_SHIFT,
    SHIFT_NAMES,
    SHIFT_TO_IDX,
    SHIFT_UI_NAMES,
)
from scheduler.config.settings import TURN_HOURS
from scheduler.core.solve import solve_schedule
from scheduler.interface.utils import (
    day_worker_matrix,
    hours_per_worker,
    result_to_df,
    schedule_db_to_df,
    schedule_pivot,
)
from scheduler.services.builder import RequestBuilder
from scheduler.services.repository import SchedulerRepository

# ------------------------------------------
# Configuración inicial
# ------------------------------------------
st.title("🧮 Generador de Horarios")

repo = SchedulerRepository()

# print(repo.load_workers())
# ------------------------------------------
# 1. Definir trabajadores
# ------------------------------------------
st.header("👤 Trabajadores")

workers = repo.load_workers()
df_workers = (
    pd.DataFrame(workers)
    if workers
    else pd.DataFrame(columns=["id", "name", "max_hours"])
)

edited = st.data_editor(df_workers, num_rows="dynamic")

if st.button("💾 Guardar trabajadores"):
    repo.save_workers(edited.to_dict(orient="records"))
    st.success("Trabajadores guardados.")


# ------------------------------------------
# 2. Demanda mínima
# ------------------------------------------
st.header("📦 Demanda mínima por turno")

demand = repo.load_demand()

# Construir DataFrame amigable para el usuario
if demand:  # si hay datos guardados
    rows = []
    for d_idx, shifts in demand.items():
        for t_idx, val in shifts.items():
            rows.append(
                {
                    "Día": IDX_TO_DAY[d_idx],
                    "Turno": IDX_TO_SHIFT[t_idx],
                    "Mínimo": val,
                }
            )
    df_dem = pd.DataFrame(rows)
else:  # crear tabla completa vacía (7x4)
    df_dem = pd.DataFrame(
        [{"Día": d, "Turno": s, "Mínimo": None} for d in DAY_NAMES for s in SHIFT_NAMES]
    )

# Editor interactivo
edited_dem = st.data_editor(df_dem, num_rows="dynamic")

# Botón de guardado
if st.button("💾 Guardar demanda"):
    dem_dict = {}
    # print(edited_dem)
    for _, row in edited_dem.iterrows():
        dia = row.get("Día")
        turno = row.get("Turno")
        minimo = row.get("Mínimo")

        if isinstance(minimo, list):
            minimo = minimo[0]

        # saltar filas sin día o turno
        if not dia or not turno:
            continue

        # convertir nombre → índice entero
        day_idx = DAY_TO_IDX.get(dia)
        shift_idx = SHIFT_TO_IDX.get(turno)

        # si algo no cuadra, saltar fila
        if day_idx is None or shift_idx is None:
            continue

        # convertir mínimo a int (si está vacío o mal, saltar)
        try:
            min_workers = int(minimo)
        except Exception:
            continue

        dem_dict.setdefault(day_idx, {})[shift_idx] = min_workers

    # guardar en SQLite
    repo.save_demand(dem_dict)
    st.success("Demanda guardada.")

# ==============================
# Disponibilidad (solo NO disponible)
# ==============================
st.header("🕒 No Disponibiles")

# load workers for name mapping
workers = repo.load_workers()
worker_map = {w["id"]: w["name"] for w in workers}
worker_name_to_id = {v: k for k, v in worker_map.items()}

# load availability
availability = repo.load_availability()

if availability:
    rows = []
    for wid, days in availability.items():
        for d_idx, shifts in days.items():
            for t_idx in shifts.keys():
                rows.append(
                    {
                        "Trabajador": worker_map[wid],
                        "Día": IDX_TO_DAY[d_idx],
                        "Turno": IDX_TO_SHIFT[t_idx],
                    }
                )
    df_av = pd.DataFrame(rows)
else:
    df_av = pd.DataFrame(columns=["Trabajador", "Día", "Turno"])

# UI editor
edited_av = st.data_editor(
    df_av,
    num_rows="dynamic",
    column_config={
        "Trabajador": st.column_config.SelectboxColumn(
            options=list(worker_map.values())
        ),
        "Día": st.column_config.SelectboxColumn(options=DAY_NAMES),
        "Turno": st.column_config.SelectboxColumn(options=SHIFT_UI_NAMES),
    },
)

# Save
if st.button("💾 Guardar disponibilidad"):
    av_dict = {}
    for _, row in edited_av.iterrows():
        name = row.get("Trabajador")
        day = row.get("Día")
        shift = row.get("Turno")
        if not name or not day or not shift:
            continue
        wid = worker_name_to_id[name]
        d_idx = DAY_TO_IDX[day]
        if turno == "Todo el día":
            # marcar los 4 turnos como NO disponibles
            for t_idx in range(4):  # 0,1,2,3
                av_dict.setdefault(wid, {}).setdefault(d_idx, {})[t_idx] = 0
        else:
            t_idx = SHIFT_TO_IDX[turno]
            av_dict.setdefault(wid, {}).setdefault(d_idx, {})[t_idx] = 0

    repo.save_availability(av_dict)
    st.success("Disponibilidad guardada.")

# ------------------------------------------
# 4. Resolver
# ------------------------------------------
st.header("🧠 Resolver planificación")

workers = repo.load_workers()
availability = repo.load_availability()
demand = repo.load_demand()

# (A) intentar cargar horario existente
loaded = repo.load_schedule()
if loaded:
    request = RequestBuilder.from_dict(workers, availability, demand)

    # reconstruir DF
    df_loaded = schedule_db_to_df(loaded, request)

    # pivot
    pivot_loaded = schedule_pivot(df_loaded.copy())
    pivot_loaded.index = pivot_loaded.index.map(IDX_TO_DAY)
    pivot_loaded.columns = pivot_loaded.columns.map(IDX_TO_SHIFT)

    st.subheader("📅 Horario guardado en base de datos")
    st.dataframe(pivot_loaded)

    # resumen de horas
    summary_loaded = hours_per_worker(df_loaded.copy(), TURN_HOURS)
    st.subheader("🕒 Horas totales por trabajador")
    st.dataframe(summary_loaded)

    # matriz día × trabajador
    matrix_loaded = day_worker_matrix(df_loaded.copy())
    matrix_loaded["Día"] = matrix_loaded["Día"].map(IDX_TO_DAY)
    matrix_loaded.rename(columns=IDX_TO_SHIFT, inplace=True)

    st.subheader("📋 Detalle Día × Trabajador")
    styled_loaded = matrix_loaded.style.applymap(
        lambda v: "background-color: #6ee757"
        if v == "Sí"
        else "background-color: #f78282"
    )
    st.dataframe(styled_loaded)

    st.divider()

else:
    st.info("No hay horario guardado todavía.")

# (B) crear uno nuevo
if st.button("🚀 Crear horario"):
    if not (workers and demand):
        st.error("Faltan datos: trabajadores, disponibilidad o demanda.")
    else:
        request = RequestBuilder.from_dict(workers, availability, demand)
        result = solve_schedule(request)
        st.session_state["result"] = result
        st.session_state["request"] = request

        if True:
            variables = result["variables"]

            (x, deficit, y_full, y_split_MT, y_split_MN, z, work, free2, viol_rest) = (
                variables.values()
            )

            print("\n===== REST VARIABLES =====")

            # Violación del descanso mínimo
            print("\n-- viol_rest[w] (1 = penalizado) --")
            print(viol_rest)
            for wid, var in viol_rest.items():
                print(f"Trabajador {wid}: viol_rest = {var.value()}")

            # Ventanas de 2 días libres
            print("\n-- free2[w,d] (1 = d y d+1 libres) --")
            for (wid, d), var in free2.items():
                print(f"Trabajador {wid}, días {d}-{d + 1}: free2 = {var.value()}")

            # Día trabajado
            print("\n-- work[w,d] (1 = trabaja) --")
            for (wid, d), var in work.items():
                print(f"Trabajador {wid}, día {d}: work = {var.value()}")


if "result" in st.session_state and "request" in st.session_state:
    result = st.session_state["result"]
    request = st.session_state["request"]
    st.subheader(f"Estado solver: {result['status']}")
    df_raw = result_to_df(result, request)
    pivot = schedule_pivot(df_raw)

    st.subheader("📅 Horario generado")
    st.dataframe(pivot)

    summary = hours_per_worker(df_raw.copy(), TURN_HOURS)
    st.subheader("🕒 Horas totales por trabajador")
    st.dataframe(summary)

    matrix = day_worker_matrix(df_raw.copy())
    matrix["Día"] = matrix["Día"].map(IDX_TO_DAY)
    matrix.rename(columns=IDX_TO_SHIFT, inplace=True)

    st.subheader("📋 Detalle Día × Trabajador")
    styled = matrix.style.applymap(
        lambda v: "background-color: #6ee757"
        if v == "Sí"
        else "background-color: #f78282"
    )
    st.dataframe(styled)

    st.session_state["result"] = result

    # Guardar en DB
    if st.button("💾 Guardar horario en base de datos"):
        st.write("Guardando horario...")
        repo.save_schedule_from_result(result)
        st.success("Horario guardado en base de datos.")

    csv = pivot.to_csv().encode("utf-8")
    st.download_button(
        "⬇️ Descargar CSV",
        data=csv,
        file_name="horario.csv",
        mime="text/csv",
    )
