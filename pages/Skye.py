import streamlit as st

from backend.utils.utils import invoke_gemini_tooled_model
from config.gemini import tooled_model, TOOLS_LIST
from config.base import CHATBOT_NAME

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

st.set_page_config(page_title=f"{CHATBOT_NAME} - Event Planner Chatbot", layout="wide")
st.title("Smart Event Planner Chatbot")
st.markdown(
    f"""
        Hi, I'm {CHATBOT_NAME}, your interactive event planning assistant powered by AI! 
        Ask anything like:
        - *"Can I plan an outdoor birthday party this Saturday in San Diego?"*
        - *"What day next week is best for a wedding in Atlanta?"*
        - *"Suggest an activity for a rainy Thursday in Seattle."*  
    """
)

for message in st.session_state.chat_history:
    with st.chat_message(message["message_content"]["role"], avatar=message.get("avatar", None)):
        st.markdown(message["message_content"]["parts"][0])

prompt = st.chat_input("Ask the AI event planner...")
if prompt:
    st.session_state.chat_history.append({"message_content": {"role": "user", "parts": [prompt]}, "avatar": "👤"})

    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    chat = [message["message_content"] for message in st.session_state.chat_history]

    with st.chat_message("model", avatar="🤖"):
        with st.spinner("Thinking..."):
            response = invoke_gemini_tooled_model(tooled_model, prompt, chat, TOOLS_LIST)
            st.markdown(response)

    st.session_state.chat_history.append({"message_content": {"role": "model", "parts": [response]}, "avatar": "🤖"})