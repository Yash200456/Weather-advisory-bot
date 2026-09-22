from typing import TypedDict, Optional, List, Dict, Any


class GraphState(TypedDict):
    user_query: str
    city_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    weather: Optional[Dict[str, Any]]
    activity: Optional[str]
    matched_sops: Optional[List[Dict[str, Any]]]
    primary_sop: Optional[Dict[str, Any]]
    answer: Optional[str]
    error: Optional[str]
    conversation_history: Optional[List[Dict[str, str]]]