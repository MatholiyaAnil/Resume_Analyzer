import streamlit as st
import PyPDF2
from google.generativeai import GenerativeModel
from langchain.prompts import PromptTemplate

st.set_page_config(page_title="ATS Score Checker")

st.header("📊 ATS Score Checker")

# Initialize Gemini Model
model = GenerativeModel("gemini-1.5-pro")

# Function to extract text from PDF
def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
        return text.strip() if text else None
    except Exception as e:
        st.error(f"Error extracting text: {e}")
        return None

# Prompt Templates
ats_score_prompt = PromptTemplate(
    input_variables=["resume_text"],
    template="Evaluate this resume for ATS compatibility and provide a score (0-100%).\n\n{resume_text}"
)

improvement_prompt = PromptTemplate(
    input_variables=["resume_text"],
    template="Analyze this resume and suggest 3-5 key improvements to increase its ATS compatibility.\n\n{resume_text}"
)

# Functions to generate ATS score and suggestions
def calculate_ats_score(resume_text):
    return model.generate_content(ats_score_prompt.format(resume_text=resume_text)).text.strip()

def generate_improvement_suggestions(resume_text):
    return model.generate_content(improvement_prompt.format(resume_text=resume_text)).text.strip()

# Upload resume
uploaded_file = st.file_uploader("Upload your resume (PDF) for ATS analysis", type="pdf")

if uploaded_file and st.button("Check ATS Score"):
    resume_text = extract_text_from_pdf(uploaded_file)
    
    if resume_text:
        with st.spinner("Analyzing your resume..."):
            ats_score = calculate_ats_score(resume_text)
            suggestions = generate_improvement_suggestions(resume_text)

        st.write(f"**Your ATS Score:** {ats_score}%")
        st.subheader("📌 Suggested Improvements:")
        st.markdown(suggestions)
