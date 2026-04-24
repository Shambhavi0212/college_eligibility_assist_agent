import streamlit as st
from agent import run_agent

st.set_page_config(page_title="AI Admission Concierge", layout="centered")

st.title("🎓 AI Admission Concierge")

# --- Initialize Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display Chat History (Top) ---
# This loop renders every previous message in chronological order
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# st.chat_input automatically stays at the bottom of the screen
if prompt := st.chat_input("Ask about colleges..."):
    
    # 1. Display user message immediately
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate and display assistant response
    with st.chat_message("assistant"):
        # We use st.spinner to give that "thinking" feel
        with st.spinner("Consulting admission data..."):
            try:
                reply = run_agent(prompt)
                st.markdown(reply)
                # Save to history
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                st.error(f"Error fetching response: {e}")