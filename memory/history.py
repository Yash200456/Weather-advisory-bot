
MAX_TURNS = 5  

def append_turn(history, user_query, answer):
    history = (history or []) + [{"user": user_query, "bot": answer}]
    return history[-MAX_TURNS:]

def format_history(history):
    if not history:
        return "No earlier conversation."
    lines = [f"User: {h['user']}\nBot: {h['bot']}" for h in history]
    return "\n".join(lines)