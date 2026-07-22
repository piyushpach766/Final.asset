VALID_STATUSES = {
    "storage": "In Storage",
    "in_use": "In Use",
    "in_repair": "In Repair",
    "retired": "Retired",
}

ALLOWED_TRANSITIONS = {
    "storage": {"storage", "in_use", "in_repair", "retired"},
    "in_use": {"in_use", "storage", "in_repair", "retired"},
    "in_repair": {"in_repair", "storage", "retired"},
    "retired": {"retired"},
}


def normalize_status(status):
    return status if status in VALID_STATUSES else "storage"


def assert_transition_allowed(current_status, next_status):
    current_status = normalize_status(current_status)
    next_status = normalize_status(next_status)
    if next_status not in ALLOWED_TRANSITIONS[current_status]:
        raise ValueError(f"Cannot change asset from {current_status} to {next_status}.")


def assert_assignable(status):
    if status == "in_repair":
        raise ValueError("Assets in repair cannot be assigned until returned.")
    if status == "retired":
        raise ValueError("Retired assets cannot be assigned or reassigned.")
