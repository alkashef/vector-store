import os
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv("config/.env")
RAW_DATA = os.getenv("RAW_DATA", "store/raw_data")

st.set_page_config(page_title="Vector Store Demo", layout="wide")

col1, col2 = st.columns(2)


with col1:
    st.header("Raw Data")
    folder = st.text_input("Folder", value=RAW_DATA, key="raw_data_folder")
    files = []
    if os.path.isdir(folder):
        files = os.listdir(folder)
        files = [f for f in files if os.path.isfile(os.path.join(folder, f))]
    else:
        st.warning(f"Folder not found: {folder}")
    # File list directly under folder input
    selected_file = None
    if files:
        for f in files:
            if st.button(f, key=f"file_{f}"):
                selected_file = f
        if selected_file:
            st.info(f"Selected: {selected_file}")
    else:
        st.write("_No files found._")

with col2:
    st.header("Chat")
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Chat history area with vertical scrolling
    chat_height = 400
    chat_container = st.container()
    with chat_container:
        st.markdown(
            f"<div style='height:{chat_height}px;overflow-y:auto;padding:0 0 8px 0;border:1px solid #eee;background:#fafafa;'>",
            unsafe_allow_html=True,
        )
        for msg in st.session_state["chat_history"]:
            role = msg["role"]
            content = msg["content"]
            align = "left" if role == "assistant" else "right"
            color = "#f1f1f1" if role == "assistant" else "#e6f7ff"
            st.markdown(
                f"<div style='text-align:{align};margin:4px 0;'><span style='display:inline-block;padding:8px 12px;border-radius:8px;background:{color};max-width:80%;'>{content}</span></div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

    # Chat input at the bottom
    prompt = st.text_input("Type your message...", key="chat_input", label_visibility="collapsed")
    if prompt:
        st.session_state["chat_history"].append({"role": "user", "content": prompt})
        st.session_state["chat_history"].append({"role": "assistant", "content": "Noted!"})
        st.rerun()
