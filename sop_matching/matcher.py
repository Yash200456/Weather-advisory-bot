import yaml

SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "severe": 3}


def load_sops(path="SOPS/sops.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)


def check_single(check, weather):
    value = weather.get(check["field"])
    if value is None:
        return False
    if check["operator"] == "greater_than":
        return value > check["value"]
    if check["operator"] == "less_than":
        return value < check["value"]
    return False


def check_condition(check, weather):
    if check is None:
        return None
    if check.get("combined"):
        return all(check_single(c, weather) for c in check["conditions"])
    return check_single(check, weather)


def _is_relevant(sop, activity):
    sop_activity = sop.get("activity")
    return sop_activity == "any" or sop_activity == activity


def match_sops(weather, sops, activity):
    return [
        sop
        for sop in sops
        if sop.get("condition_check") is not None
        and _is_relevant(sop, activity)
        and check_condition(sop["condition_check"], weather)
    ]


def pick_primary_sop(matched_sops):
    if not matched_sops:
        return None
    return max(matched_sops, key=lambda s: SEVERITY_RANK.get(s["severity"], -1))


def get_fuzzy_sops(sops):
    return [s for s in sops if s.get("condition_check") is None]


def get_fuzzy_sop_for_activity(sops, activity):
    for s in sops:
        if s.get("condition_check") is None and s.get("activity") == activity:
            return s
    return None