import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

st.set_page_config(page_title="Resume Analyzer", page_icon="📝")
st.title("Resume Analyzer")
st.write("Navigate using the sidebar to analyze resumes, check ATS scores, and get improvement suggestions.")

# Sidebar navigation
st.sidebar.success("Select a page from the sidebar.")