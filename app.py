
import streamlit as st

st.set_page_config(page_title="Vector Store Demo", layout="wide")
st.markdown(
    """
    <style>
    body, .stApp, .stMarkdown, .stText, .stTitle, .stHeader, .stDataFrame, .stJson {
        color: #222222 !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)
st.title("Vector Store Demo")

# Divide the page into 3 vertical columns
import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), 'config'))
import config.settings  # loads envs

col1, col2, col3 = st.columns(3)

import pandas as pd
from streamlit import column_config
import json
with col1:
    cv_dir = os.environ.get("CV_DATA", "store/raw_data/CV")
    cv_files = []
    if os.path.isdir(cv_dir):
        cv_files = sorted([f for f in os.listdir(cv_dir) if os.path.isfile(os.path.join(cv_dir, f))])
    selected_cv = None
    
    if cv_files:
        selected_cv = st.selectbox(
            label="Select a CV File:",
            options=cv_files,
            key="cv_selectbox",
            index=0 if cv_files else None
        )
        # Show JSON for selected CV
        cv_json_data = None
        try:
            cv_path = os.path.join(cv_dir, selected_cv)
            with open(cv_path, "r", encoding="utf-8") as f:
                cv_json_data = json.load(f)
        except Exception as e:
            st.error(f"Failed to load CV: {e}")
        cv_container = st.container(height=600)
        if cv_json_data is not None:
            cv_container.json(cv_json_data, expanded=True, width='stretch')
        st.button("Ingest CV", key="ingest_cv_btn")
    else:
        st.write("_No CV files found._")

with col2:
    jd_dir = os.environ.get("JD_DATA", "store/raw_data/JD")
    jd_files = []
    if os.path.isdir(jd_dir):
        jd_files = sorted([f for f in os.listdir(jd_dir) if os.path.isfile(os.path.join(jd_dir, f))])
    selected_jd = None
    if jd_files:
        selected_jd = st.selectbox(
            label="Select a JD File:",
            options=jd_files,
            key="jd_selectbox",
            index=0 if jd_files else None
        )
        # Show JSON for selected JD
        jd_json_data = None
        try:
            jd_path = os.path.join(jd_dir, selected_jd)
            with open(jd_path, "r", encoding="utf-8") as f:
                jd_json_data = json.load(f)
        except Exception as e:
            st.error(f"Failed to load JD: {e}")
        jd_container = st.container(height=600)
        if jd_json_data is not None:
            jd_container.json(jd_json_data, expanded=True, width='stretch')
        st.button("Ingest JD", key="ingest_jd_btn")
    else:
        st.write("_No JD files found._")
with col3:
    st.header("Search")

