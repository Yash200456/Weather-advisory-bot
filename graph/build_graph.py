# graph/build_graph.py
from langgraph.graph import StateGraph, END
from graph.state import GraphState
from graph.nodes import (
    resolve_location_node,
    fetch_weather_node,
    classify_intent_node,
    match_sop_node,
    fuzzy_judge_node,
    compose_answer_node,
    no_sop_fallback_node,
    error_fallback_node,
)


def route_after_location(state):
    return "error" if state.get("error") else "fetch_weather"


def route_after_weather(state):
    return "error" if state.get("error") else "classify_intent"


def route_after_match(state):
    if state.get("primary_sop"):
        return "compose"
    return "fuzzy_check"


def route_after_fuzzy(state):
    return "compose" if state.get("primary_sop") else "no_sop"


def build_graph():
    g = StateGraph(GraphState)

    g.add_node("resolve_location", resolve_location_node)
    g.add_node("fetch_weather", fetch_weather_node)
    g.add_node("classify_intent", classify_intent_node)
    g.add_node("match_sop", match_sop_node)
    g.add_node("fuzzy_check", fuzzy_judge_node)
    g.add_node("compose", compose_answer_node)
    g.add_node("no_sop", no_sop_fallback_node)
    g.add_node("error_fallback", error_fallback_node)

    g.set_entry_point("resolve_location")

    g.add_conditional_edges(
        "resolve_location",
        route_after_location,
        {"error": "error_fallback", "fetch_weather": "fetch_weather"},
    )
    g.add_conditional_edges(
        "fetch_weather",
        route_after_weather,
        {"error": "error_fallback", "classify_intent": "classify_intent"},
    )
    g.add_edge("classify_intent", "match_sop")
    g.add_conditional_edges(
        "match_sop",
        route_after_match,
        {"compose": "compose", "fuzzy_check": "fuzzy_check"},
    )
    g.add_conditional_edges(
        "fuzzy_check",
        route_after_fuzzy,
        {"compose": "compose", "no_sop": "no_sop"},
    )

    g.add_edge("compose", END)
    g.add_edge("no_sop", END)
    g.add_edge("error_fallback", END)

    return g.compile()