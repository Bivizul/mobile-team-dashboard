import json
import os

STATE_FILE = "state.json"

def load_state():
    if not os.path.exists(STATE_FILE):
        return {
            "filters": {},
            "vacations": {},
            "vacationColumnsCount": 1
        }
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {
            "filters": {},
            "vacations": {},
            "vacationColumnsCount": 1
        }

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4, ensure_ascii=False)

def get_scope_key(epic_link, fix_version):
    return f"epic:{epic_link or 'all'}|fix:{fix_version or 'all'}"

def update_filters(epic_link, fix_version, feature_start_date=None, working_hours_per_day=None):
    state = load_state()

    # Update global filters
    if "filters" not in state:
        state["filters"] = {}

    state["filters"]["epic_link"] = epic_link
    state["filters"]["fix_version"] = fix_version

    if feature_start_date is not None:
        state["filters"]["feature_start_date"] = feature_start_date
    if working_hours_per_day is not None:
        state["filters"]["working_hours_per_day"] = working_hours_per_day

    # Update scoped data
    if "scoped_data" not in state:
        state["scoped_data"] = {}

    scope_key = get_scope_key(epic_link, fix_version)
    if scope_key not in state["scoped_data"]:
        state["scoped_data"][scope_key] = {}

    if feature_start_date is not None:
        state["scoped_data"][scope_key]["feature_start_date"] = feature_start_date
    if working_hours_per_day is not None:
        state["scoped_data"][scope_key]["working_hours_per_day"] = working_hours_per_day

    save_state(state)

def update_vacation(name, index, start, end):
    state = load_state()
    key = f"v_{name}_{index}"
    state["vacations"][key] = {"start": start, "end": end}
    save_state(state)

def update_vacation_columns(count):
    state = load_state()
    state["vacationColumnsCount"] = count
    save_state(state)

def clear_vacations():
    state = load_state()
    state["vacations"] = {}
    state["vacationColumnsCount"] = 1
    save_state(state)
