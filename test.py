import streamlit as st
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.messages import HumanMessage, AIMessage
from prompt import SYSTEM_PROMPT
from tools import sql_executor
import os

# Load environment variables
load_dotenv()

# --- Streamlit Page Config ---
st.set_page_config(page_title="AI Admission Concierge", page_icon="🎓")
st.title("🎓 AI Admission Concierge")

# --- Initialize Agent (Cached) ---
@st.cache_resource
def init_agent():
    llm = ChatGroq(
        model_name="openai/gpt-oss-120b",
        temperature=0.7,
        groq_api_key=os.getenv('GROQ_API_KEY')
    )
    tools = [sql_executor]
    return create_agent(llm, tools=tools, system_prompt=SYSTEM_PROMPT)

agent = init_agent()

# --- Session State for Chat History ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Display Chat History (ChatGPT Style) ---
for message in st.session_state.messages:
    role = "user" if isinstance(message, HumanMessage) else "assistant"
    with st.chat_message(role):
        st.markdown(message.content)

# --- Chat Input Area ---
if prompt := st.chat_input("Ask about colleges..."):
    
    # 1. Add user message to state and display
    user_msg = HumanMessage(content=prompt)
    st.session_state.messages.append(user_msg)
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate Agent Response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # We pass the full history to the agent so it has context
                response = agent.invoke({
                    "messages": st.session_state.messages
                })
                
                # Extract response text
                answer_text = response["messages"][-1].content
                st.markdown(answer_text)
                
                # 3. Add assistant response to state
                st.session_state.messages.append(AIMessage(content=answer_text))
                
            except Exception as e:
                st.error(f"An error occurred: {e}")