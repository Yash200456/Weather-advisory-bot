# main.py
import sys
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

from graph.build_graph import build_graph
from memory.history import append_turn


def run():
    app = build_graph()
    conversation_history = []
    city_name = input("Which city are you in? ").strip()

    print("Weather-advisory bot ready. Type 'quit' to exit.\n")
    while True:
        query = input("You: ").strip()
        if query.lower() in ("quit", "exit"):
            break

        state = {
            "user_query": query,
            "city_name": city_name,
            "conversation_history": conversation_history,
        }
        result = app.invoke(state)
        answer = result.get("answer", "Something went wrong — no answer produced.")
        print(f"Bot: {answer}\n")

        conversation_history = append_turn(conversation_history, query, answer)


if __name__ == "__main__":
    run()