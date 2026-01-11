import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import colorsys

from scheduler.config.constants import (
    DAY_COLORS,
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


def pastel_colors(names):
    colors = {}
    n = len(names)
    for i, name in enumerate(names):
        hue = i / max(n, 1)
        r, g, b = colorsys.hsv_to_rgb(hue, 0.25, 0.95)
        # Evita verdes y rojos muy claros
        if g > 0.8 and r < 0.6:
            g = 0.7
        if r > 0.8 and g < 0.6:
            r = 0.7

        colors[name] = (
            f"background-color: rgb({int(r * 255)}, {int(g * 255)}, {int(b * 255)})"
        )
    return colors


# ------------------------------------------
# Configuración inicial
# ------------------------------------------
st.set_page_config(page_title="Generador de Horarios", layout="wide")
st.title("🧮 Generador de Horarios")

repo = SchedulerRepository()


# -------------------------
# Helpers
# -------------------------
def get_worker_map():
    workers = repo.load_workers()
    wid_to_name = {w["id"]: w["name"] for w in workers}
    name_to_wid = {w["name"]: w["id"] for w in workers}
    return workers, wid_to_name, name_to_wid


def save_one_worker(name: str, max_hours: int):
    workers = repo.load_workers() or []
    # si ya existe, actualiza; si no, añade
    existing = next((w for w in workers if w.get("name") == name), None)
    if existing:
        existing["max_hours"] = max_hours
    else:
        # si tu repo crea ids automáticamente, puedes omitir id aquí.
        # si NO lo hace, te conviene generar uno (por ejemplo, max+1).
        max_id = max([w.get("id", 0) for w in workers], default=0)
        workers.append({"id": max_id + 1, "name": name, "max_hours": max_hours})

    repo.save_workers(workers)


def normalize_cell(x):
    # Convierte cosas como ["Lunes"] -> "Lunes", [] -> None, NaN -> None
    if x is None:
        return None
    if isinstance(x, list):
        return x[0] if len(x) > 0 else None
    if isinstance(x, float) and pd.isna(x):
        return None
    x = str(x).strip()
    return x if x else None


def save_no_availability(worker_id: int, no_av_rows: list[dict]):
    current = repo.load_availability() or {}
    av_dict = current.copy()

    for r in no_av_rows:
        day = normalize_cell(r.get("day"))
        shift = normalize_cell(r.get("shift"))

        if not day or not shift:
            continue

        # Solo aceptamos días válidos
        if day not in DAY_TO_IDX:
            continue

        d_idx = DAY_TO_IDX[day]

        if shift == "Todo el día":
            for t_idx in range(4):
                av_dict.setdefault(worker_id, {}).setdefault(d_idx, {})[t_idx] = 0
        else:
            # Solo aceptamos turnos válidos
            if shift not in SHIFT_TO_IDX:
                continue
            t_idx = SHIFT_TO_IDX[shift]
            av_dict.setdefault(worker_id, {}).setdefault(d_idx, {})[t_idx] = 0

    repo.save_availability(av_dict)


def worker_no_availability_to_df(availability: dict, worker_id: int) -> pd.DataFrame:
    """
    availability[wid][d_idx][t_idx] = 0  (solo guardamos NO disponibles)
    Devuelve filas: Día, Turno (texto UI)
    """
    rows = []
    days = availability.get(worker_id, {})
    for d_idx, shifts in days.items():
        for t_idx in shifts.keys():
            rows.append({"Día": IDX_TO_DAY[d_idx], "Turno": IDX_TO_SHIFT[t_idx]})
    # opcional: ordenar
    if rows:
        df = pd.DataFrame(rows)
        df["Día"] = pd.Categorical(df["Día"], categories=DAY_NAMES, ordered=True)
        df = df.sort_values(["Día", "Turno"]).reset_index(drop=True)
        return df
    return pd.DataFrame(columns=["Día", "Turno"])


def replace_worker_no_availability(
    repo: SchedulerRepository, worker_id: int, df_no_av: pd.DataFrame
):
    """
    Reemplaza TODAS las NO disponibilidades del trabajador por lo que venga en df_no_av.
    """
    availability = repo.load_availability() or {}

    # borrar lo anterior de ese worker
    if worker_id in availability:
        availability.pop(worker_id)

    # construir lo nuevo
    av_dict = availability
    for _, r in df_no_av.iterrows():
        day = normalize_cell(r.get("Día"))
        shift = normalize_cell(r.get("Turno"))
        if not day or not shift:
            continue
        if day not in DAY_TO_IDX:
            continue

        d_idx = DAY_TO_IDX[day]

        if shift == "Todo el día":
            for t_idx in range(4):
                av_dict.setdefault(worker_id, {}).setdefault(d_idx, {})[t_idx] = 0
        else:
            if shift not in SHIFT_TO_IDX:
                continue
            t_idx = SHIFT_TO_IDX[shift]
            av_dict.setdefault(worker_id, {}).setdefault(d_idx, {})[t_idx] = 0

    repo.save_availability(av_dict)


def build_full_demand_df(demand_dict):
    # demanda: demand_dict[day_idx][shift_idx] = minimo
    rows = []
    for d in DAY_NAMES:
        for s in SHIFT_NAMES:
            d_idx = DAY_TO_IDX[d]
            s_idx = SHIFT_TO_IDX[s]
            val = None
            if demand_dict and d_idx in demand_dict and s_idx in demand_dict[d_idx]:
                val = demand_dict[d_idx][s_idx]
            rows.append({"Día": d, "Turno": s, "Mínimo": val})
    return pd.DataFrame(rows)


def demand_df_to_dict(df):
    dem_dict = {}
    for _, row in df.iterrows():
        day = row.get("Día")
        shift = row.get("Turno")
        minimo = row.get("Mínimo")

        if not day or not shift:
            continue
        if pd.isna(minimo):
            continue
        try:
            min_workers = int(minimo)
        except Exception:
            continue

        d_idx = DAY_TO_IDX[day]
        t_idx = SHIFT_TO_IDX[shift]
        dem_dict.setdefault(d_idx, {})[t_idx] = min_workers
    return dem_dict


# =========================================================
# PASO 1 — Alta y gestión de trabajadores
# =========================================================
st.header("PASO 1 👤 Registrar y gestionar trabajadores")

# Cargar estado
workers, wid_to_name, name_to_wid = get_worker_map()
availability_all = repo.load_availability() or {}

# =========================
# (A) Alta de trabajador (uno a uno)
# =========================
st.subheader("Alta de trabajador")

with st.form("form_worker_create", clear_on_submit=True):
    col1, col2 = st.columns([2, 1])
    with col1:
        new_name = st.text_input("Nombre del trabajador")
    with col2:
        new_max_hours = st.number_input(
            "Máx. horas/semana", min_value=0, max_value=80, value=40, step=1
        )

    st.markdown("### 🕒 No disponibilidad (marca solo lo que NO puede)")
    no_av_df_create = st.data_editor(
        pd.DataFrame(columns=["Día", "Turno"]),
        num_rows="dynamic",
        column_config={
            "Día": st.column_config.SelectboxColumn(options=DAY_NAMES),
            "Turno": st.column_config.SelectboxColumn(options=SHIFT_UI_NAMES),
        },
        key="no_av_editor_create",
        use_container_width=True,
    )

    create_submit = st.form_submit_button("✅ Guardar trabajador")

if create_submit:
    if not new_name.strip():
        st.error("El nombre no puede estar vacío.")
    else:
        save_one_worker(new_name.strip(), int(new_max_hours))

        # recargar id del trabajador
        workers, wid_to_name, name_to_wid = get_worker_map()
        wid = name_to_wid.get(new_name.strip())

        if wid is not None:
            # normalizar df antes de guardar
            df_clean = no_av_df_create.copy()
            df_clean["Día"] = df_clean["Día"].apply(normalize_cell)
            df_clean["Turno"] = df_clean["Turno"].apply(normalize_cell)
            df_clean = df_clean.dropna().reset_index(drop=True)

            replace_worker_no_availability(repo, wid, df_clean)

        st.success(f"Trabajador '{new_name.strip()}' guardado.")


# =========================
# (B) Revisión global de NO disponibilidades (expander)
# =========================
with st.expander("🔎 Revisar NO disponibilidades (todas)"):
    # construir una tabla global (Trabajador, Día, Turno)
    rows = []
    for wid, days in availability_all.items():
        for d_idx, shifts in days.items():
            for t_idx in shifts.keys():
                rows.append(
                    {
                        "Trabajador": wid_to_name.get(wid, f"ID {wid}"),
                        "Día": IDX_TO_DAY[d_idx],
                        "Turno": IDX_TO_SHIFT[t_idx],
                    }
                )
    df_global = (
        pd.DataFrame(rows)
        if rows
        else pd.DataFrame(columns=["Trabajador", "Día", "Turno"])
    )
    if not df_global.empty:
        df_global["Día"] = pd.Categorical(
            df_global["Día"], categories=DAY_NAMES, ordered=True
        )
        df_global = df_global.sort_values(["Trabajador", "Día", "Turno"]).reset_index(
            drop=True
        )
    st.dataframe(df_global, use_container_width=True)


# =========================
# (C) Modificar / eliminar un trabajador
# =========================
with st.expander("🛠️ Modificar / eliminar un trabajador", expanded=False):
    workers, wid_to_name, name_to_wid = get_worker_map()
    if not workers:
        st.info("Aún no hay trabajadores registrados.")
    else:
        worker_names = [w["name"] for w in workers]
        selected_name = st.selectbox(
            "Selecciona un trabajador", worker_names, key="select_worker_manage"
        )
        selected_wid = name_to_wid[selected_name]
        selected_worker = next(w for w in workers if w["id"] == selected_wid)

        col_left, col_right = st.columns([1, 1])

        # ---- editar datos básicos
        with col_left:
            st.markdown("### ✏️ Datos del trabajador")
            with st.form("form_worker_update"):
                upd_name = st.text_input("Nombre", value=selected_worker["name"])
                upd_max_hours = st.number_input(
                    "Máx. horas/semana",
                    min_value=0,
                    max_value=80,
                    value=int(selected_worker.get("max_hours", 40)),
                    step=1,
                )
                upd_submit = st.form_submit_button("💾 Guardar cambios")

            if upd_submit:
                upd_name = upd_name.strip()
                if not upd_name:
                    st.error("El nombre no puede estar vacío.")
                else:
                    # actualizar en lista workers
                    for w in workers:
                        if w["id"] == selected_wid:
                            w["name"] = upd_name
                            w["max_hours"] = int(upd_max_hours)
                            break
                    repo.save_workers(workers)
                    st.success("Datos del trabajador actualizados.")
                    st.rerun()

        # ---- editar NO disponibilidad
        with col_right:
            st.markdown("### 🕒 NO disponibilidad del trabajador")

            availability_all = repo.load_availability() or {}
            df_no_av = worker_no_availability_to_df(availability_all, selected_wid)

            edited_no_av = st.data_editor(
                df_no_av,
                num_rows="dynamic",
                column_config={
                    "Día": st.column_config.SelectboxColumn(options=DAY_NAMES),
                    "Turno": st.column_config.SelectboxColumn(options=SHIFT_UI_NAMES),
                },
                key="no_av_editor_update",
                use_container_width=True,
            )

            if st.button("💾 Guardar NO disponibilidad", key="btn_save_no_av"):
                df_clean = edited_no_av.copy()
                df_clean["Día"] = df_clean["Día"].apply(normalize_cell)
                df_clean["Turno"] = df_clean["Turno"].apply(normalize_cell)
                df_clean = df_clean.dropna().reset_index(drop=True)

                replace_worker_no_availability(repo, selected_wid, df_clean)
                st.success("NO disponibilidad actualizada.")
                st.rerun()

        st.divider()

        # ---- eliminar trabajador
        st.markdown("### 🗑️ Eliminar trabajador")
        st.warning("Esto eliminará el trabajador y sus NO disponibilidades asociadas.")

        confirm = st.checkbox(
            "Confirmo que quiero eliminar este trabajador", key="chk_del_worker"
        )
        if st.button(
            "❌ Eliminar definitivamente", disabled=not confirm, key="btn_del_worker"
        ):
            # 1) eliminar de workers
            new_workers = [w for w in workers if w["id"] != selected_wid]
            repo.save_workers(new_workers)

            # 2) eliminar su disponibilidad
            availability_all = repo.load_availability() or {}
            if selected_wid in availability_all:
                availability_all.pop(selected_wid)
                repo.save_availability(availability_all)

            # (opcional) podrías también invalidar el schedule guardado si depende de ese worker
            st.success("Trabajador eliminado.")
            st.rerun()

# =========================================================
# PASO 2 — Demanda mínima
# =========================================================
st.header("PASO 2 🗓️ Definir mínimos por turno")

# Cargar demanda guardada (overrides explícitos)
demand_saved = repo.load_demand() or {}

# -------------------------
# Defaults por turno
# -------------------------
st.subheader("Valores por defecto (por turno)")

# si tienes 4 turnos, esto crea 4 inputs (Mañana, Tarde, Noche, etc.)
# usamos SHIFT_NAMES / SHIFT_TO_IDX (los "turnos reales" del modelo)
default_cols = st.columns(len(SHIFT_NAMES))
defaults_by_shift_idx = {}

for i, shift_name in enumerate(SHIFT_NAMES):
    with default_cols[i]:
        defaults_by_shift_idx[SHIFT_TO_IDX[shift_name]] = st.number_input(
            f"Default {shift_name}",
            min_value=0,
            step=1,
            value=0,
            key=f"default_shift_{shift_name}",
        )

st.caption(
    "Estos valores rellenan toda la semana. Después puedes modificar día a día en la tabla de abajo."
)

# -------------------------
# Construir tabla base = defaults
# -------------------------
rows = []
for day_name in DAY_NAMES:
    d_idx = DAY_TO_IDX[day_name]
    for shift_name in SHIFT_NAMES:
        t_idx = SHIFT_TO_IDX[shift_name]

        # base = default del turno
        base_val = defaults_by_shift_idx.get(t_idx, 0)

        # override si ya había algo guardado
        if d_idx in demand_saved and t_idx in demand_saved[d_idx]:
            base_val = demand_saved[d_idx][t_idx]

        rows.append({"Día": day_name, "Turno": shift_name, "Mínimo": base_val})

df_dem = pd.DataFrame(rows)

# -------------------------
# Editor: sobrescribir sobre el default
# -------------------------
st.subheader("Ajuste por día (sobrescribe el default)")

edited_dem = st.data_editor(
    df_dem,
    num_rows="fixed",
    column_config={
        "Día": st.column_config.SelectboxColumn(options=DAY_NAMES, disabled=True),
        "Turno": st.column_config.SelectboxColumn(options=SHIFT_NAMES, disabled=True),
        "Mínimo": st.column_config.NumberColumn(min_value=0, step=1),
    },
    use_container_width=True,
    key="demands_editor",
)

# -------------------------
# Guardado:
# - guardamos SOLO overrides respecto al default (más limpio)
#   (si prefieres guardar todo, te lo cambio)
# -------------------------
col_save, col_clear = st.columns([1, 1])

with col_save:
    if st.button("💾 Guardar", key="btn_save_demand"):
        dem_dict = {}
        for _, r in edited_dem.iterrows():
            day_name = r["Día"]
            shift_name = r["Turno"]
            min_val = r["Mínimo"]

            d_idx = DAY_TO_IDX[day_name]
            t_idx = SHIFT_TO_IDX[shift_name]

            # default del turno
            default_val = defaults_by_shift_idx.get(t_idx, 0)

            # guardamos solo si es override (distinto del default)
            # if int(min_val) != int(default_val):
            dem_dict.setdefault(d_idx, {})[t_idx] = int(min_val)

        repo.save_demand(dem_dict)
        st.success("Demanda guardada.")

with col_clear:
    if st.button("🧹 Vaciar demanda", key="btn_clear_demand"):
        repo.save_demand({})
        st.warning("Demanda vaciada.")


# =========================================================
# PASO 3 — Resolver y mostrar
# =========================================================
st.header("PASO 3 🧠 Generar calendario")

workers = repo.load_workers() or []
availability = repo.load_availability() or {}
demand = repo.load_demand() or {}

loaded = repo.load_schedule()
if loaded and workers and demand:
    request = RequestBuilder.from_dict(workers, availability, demand)
    df_loaded = schedule_db_to_df(loaded, request)

    pivot_loaded = schedule_pivot(df_loaded.copy())
    pivot_loaded.index = pivot_loaded.index.map(IDX_TO_DAY)
    pivot_loaded.columns = pivot_loaded.columns.map(IDX_TO_SHIFT)

    st.subheader("📅 Horario guardado en base de datos")
    st.dataframe(pivot_loaded, use_container_width=True)

    summary_loaded = hours_per_worker(df_loaded.copy(), TURN_HOURS)
    st.subheader("🕒 Horas totales por trabajador")
    st.dataframe(summary_loaded, use_container_width=True)

    matrix_loaded = day_worker_matrix(df_loaded.copy())
    matrix_loaded["Día"] = matrix_loaded["Día"].map(IDX_TO_DAY)
    matrix_loaded.rename(columns=IDX_TO_SHIFT, inplace=True)

    st.subheader("📋 Detalle Día × Trabajador")
    styled_loaded = matrix_loaded.style.applymap(
        lambda v: "background-color: #6ee757"
        if v == "Sí"
        else "background-color: #f78282"
    )
    st.dataframe(styled_loaded, use_container_width=True)

    st.divider()
else:
    st.info("No hay horario guardado todavía (o faltan datos).")

# Crear nuevo
if st.button("🚀 Crear horario"):
    if not workers:
        st.error("Faltan trabajadores.")
    elif not demand:
        st.error("Falta demanda mínima.")
    else:
        request = RequestBuilder.from_dict(workers, availability, demand)
        result = solve_schedule(request)
        st.session_state["result"] = result
        st.session_state["request"] = request

# Mostrar resultado si existe
if "result" in st.session_state and "request" in st.session_state:
    result = st.session_state["result"]
    request = st.session_state["request"]

    st.subheader(f"Estado solver: {result['status']}")
    df_raw = result_to_df(result, request)
    pivot = schedule_pivot(df_raw)

    st.subheader("📅 Horario generado")
    st.dataframe(pivot, use_container_width=True)

    summary = hours_per_worker(df_raw.copy(), TURN_HOURS)
    st.subheader("🕒 Horas totales por trabajador")
    st.dataframe(summary, use_container_width=True)

    matrix = day_worker_matrix(df_raw.copy())
    matrix["Día"] = matrix["Día"].map(IDX_TO_DAY)
    matrix.rename(columns=IDX_TO_SHIFT, inplace=True)

    st.subheader("📋 Detalle Día × Trabajador")
    WORKER_COLORS = pastel_colors(matrix["Trabajador"].unique())

    turno_cols = matrix.columns[2:]

    def color_turno(v):
        if v == "Sí":
            return "background-color:rgb(190, 247, 179)"
        elif v == "No":
            return "background-color:rgb(248, 185, 185)"
        return ""

    def color_dia(col):
        return [DAY_COLORS.get(v, "") for v in col]

    def color_trabajador(col):
        return [WORKER_COLORS.get(v, "") for v in col]

    styled = (
        matrix.style
        # Día
        .apply(color_dia, subset=["Día"])
        # Trabajador
        .apply(color_trabajador, subset=["Trabajador"])
        # Turnos
        .applymap(color_turno, subset=turno_cols)
    )

    st.dataframe(styled, use_container_width=True)
    # styled = matrix.style.applymap(color_si_no, subset=turno_cols)

    # st.dataframe(styled, use_container_width=True)
    # styled = matrix.style.applymap(
    #     lambda v: "background-color: #6ee757"
    #     if v == "Sí"
    #     else "background-color: #f78282"
    # )
    # st.dataframe(styled, use_container_width=True)

    col_save, col_dl = st.columns([1, 1])

    with col_save:
        if st.button("💾 Guardar horario en base de datos"):
            repo.save_schedule_from_result(result)
            st.success("Horario guardado en base de datos.")

    with col_dl:
        csv = pivot.to_csv().encode("utf-8")
        st.download_button(
            "⬇️ Descargar CSV",
            data=csv,
            file_name="horario.csv",
            mime="text/csv",
        )
