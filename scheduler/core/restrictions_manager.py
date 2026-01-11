# core/restrictions_manager.py

from scheduler.core.restrictions import (
    availability,
    coverage,
    full_day,
    hours,
    rest,
    rest2days,
    split_shifts,
)

ACTIVE_RESTRICTIONS = [
    coverage.add_coverage_constraints,
    coverage.add_empty_turn_penalty,
    availability.add_availability_constraints,
    hours.add_hour_constraints,
    full_day.add_full_day_constraints,
    split_shifts.add_split_shift_constraints,
    rest.add_rest_constraints,
    rest2days.add_rest2days_constraints,
]


def apply_restrictions(model, variables, schedule_request, restrictions=None):
    if not restrictions:
        restrictions = ACTIVE_RESTRICTIONS
    for add in restrictions:
        add(model, variables, schedule_request)
