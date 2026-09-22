# frontend/app.py
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from graph.build_graph import build_graph
from memory.history import append_turn

st.set_page_config(page_title="Weather-Advisory Bot", page_icon="⛅")
st.title("⛅ Weather-Advisory Support Bot")
st.caption("Every answer is traceable to a written SOP — or the bot says honestly that none applies.")

if "app" not in st.session_state:
    st.session_state.app = build_graph()
if "history" not in st.session_state:
    st.session_state.history = []
if "city" not in st.session_state:
    st.session_state.city = None
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.city is None:
    city_input = st.text_input("Which city are you in?", key="city_box")
    if st.button("Start") and city_input.strip():
        st.session_state.city = city_input.strip()
        st.rerun()
    st.stop()

st.info(f"📍 Location set to **{st.session_state.city}**")
if st.button("Change city / reset session"):
    st.session_state.city = None
    st.session_state.history = []
    st.session_state.messages = []
    st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

query = st.chat_input("Ask about outdoor activity safety, e.g. 'is it safe to cycle today?'")
if query:
    st.session_state.messages.append({"role": "user", "content": query})
    with st.chat_message("user"):
        st.markdown(query)

    state = {
        "user_query": query,
        "city_name": st.session_state.city,
        "conversation_history": st.session_state.history,
    }
    result = st.session_state.app.invoke(state)
    answer = result.get("answer", "Something went wrong — no answer produced.")

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.session_state.history = append_turn(st.session_state.history, query, answer)