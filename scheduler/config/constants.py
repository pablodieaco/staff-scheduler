DAY_NAMES = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

SHIFT_NAMES = ["Mañana", "Mediodía", "Tarde", "Noche"]
SHIFT_UI_NAMES = SHIFT_NAMES + ["Todo el día"]

DAY_TO_IDX = {name: i for i, name in enumerate(DAY_NAMES)}
IDX_TO_DAY = {i: name for i, name in enumerate(DAY_NAMES)}

SHIFT_TO_IDX = {name: i for i, name in enumerate(SHIFT_NAMES)}
IDX_TO_SHIFT = {i: name for i, name in enumerate(SHIFT_NAMES)}
DAY_COLORS = {
    "Lunes": "background-color: #FFF1C1",
    "Martes": "background-color: #E3F2FD",
    "Miércoles": "background-color: #E8F5E9",
    "Jueves": "background-color: #F3E5F5",
    "Viernes": "background-color: #E0F7FA",
    "Sábado": "background-color: #FFF3E0",
    "Domingo": "background-color: #FCE4EC",
}
