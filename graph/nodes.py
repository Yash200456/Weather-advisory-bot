# graph/nodes.py
from services.geocoding import resolve_city, LocationNotFoundError
from services.weather import get_current_weather, WeatherFetchError
from services.llm import call_llm
from sop_matching.matcher import load_sops, match_sops, pick_primary_sop, get_fuzzy_sop_for_activity

SOPS = load_sops()

ACTIVITY_TAGS = [
    "cycling", "commute", "elderly_outdoor_activity", "children_outdoor_activity",
    "pet_outdoor_activity", "general_outdoor_plans", "picnic", "unknown",
]


def resolve_location_node(state):
    try:
        lat, lon = resolve_city(state["city_name"])
        return {**state, "latitude": lat, "longitude": lon, "error": None}
    except LocationNotFoundError as e:
        return {**state, "error": str(e)}


def fetch_weather_node(state):
    try:
        weather = get_current_weather(state["latitude"], state["longitude"])
        return {**state, "weather": weather, "error": None}
    except WeatherFetchError as e:
        return {**state, "error": str(e)}


def classify_intent_node(state):
    history = state.get("conversation_history") or []
    history_text = "\n".join(f"User: {h['user']}\nBot: {h['bot']}" for h in history) or "No earlier conversation."
    prompt = (
        f"Conversation so far:\n{history_text}\n\n"
        f"Classify the CURRENT question into exactly one of: {ACTIVITY_TAGS}. "
        f"If it references something earlier (e.g. 'what about this evening'), "
        f"use the conversation to infer the activity.\n"
        f"Current question: {state['user_query']}\nReply with only the tag, nothing else."
    )
    try:
        tag = call_llm(prompt).strip()
    except Exception:
        tag = "unknown"
    return {**state, "activity": tag if tag in ACTIVITY_TAGS else "unknown"}


def match_sop_node(state):
    matched = match_sops(state["weather"], SOPS, state.get("activity"))
    primary = pick_primary_sop(matched)
    return {**state, "matched_sops": matched, "primary_sop": primary}


def fuzzy_judge_node(state):
    sop = get_fuzzy_sop_for_activity(SOPS, state.get("activity"))
    if sop is None:
        return {**state, "primary_sop": None}

    prompt = (
        f"SOP description: {sop['condition_description']}\n"
        f"Actual current weather (use only these numbers, do not estimate): {state['weather']}\n"
        "Does this weather satisfy the SOP's description? Reply with only YES or NO."
    )
    try:
        verdict = call_llm(prompt).strip().upper()
    except Exception:
        verdict = "NO"

    chosen = dict(sop)
    chosen["_use_fallback"] = not verdict.startswith("YES")
    return {**state, "primary_sop": chosen}


def compose_answer_node(state):
    sop = state["primary_sop"]
    template = sop["fallback_advice"] if sop.get("_use_fallback") else sop["advice_template"]
    answer = template.format(**state["weather"])
    return {**state, "answer": f"[{sop['id']}] {answer}"}


def no_sop_fallback_node(state):
    return {**state, "answer": "I don't have specific guidance covering this situation, so I won't guess — you may want to check official weather advisories directly."}


def error_fallback_node(state):
    return {**state, "answer": f"I couldn't get the information needed to answer that safely: {state['error']}"}