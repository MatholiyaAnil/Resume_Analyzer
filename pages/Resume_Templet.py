import streamlit as st
from google.generativeai import GenerativeModel
import PyPDF2
import os
from dotenv import load_dotenv

load_dotenv()

# Set up Streamlit
st.set_page_config(page_title="Resume Template Generator", page_icon="📄")
st.title("Resume Template Generator")
st.write("Upload your resume and provide a job title to generate tailored resume templates.")

# Check for Google API Key
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    api_key = st.text_input("Enter your Google API Key", type="password")
    if not api_key:
        st.warning("Please provide a valid API key.")
        st.stop()
os.environ["GOOGLE_API_KEY"] = api_key  # Set API Key

# Initialize Gemini Model after setting API key
model = GenerativeModel("gemini-1.5-pro")

# Function to extract text from PDF
def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
        return text.strip() if text else None
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return None

# Function to generate resume templates
def generate_resume_templates(job_title, resume_text):
    prompts = [
        f"""
        Generate a **modern** resume template for the job title: {job_title}.
        Highlight relevant skills and experiences from the following resume:
        
        {resume_text}
        
        The format should be ATS-friendly with sections: Summary, Skills, Experience, Education, and Certifications.
        """,
        f"""
        Generate a **creative** resume template for the job title: {job_title}.
        Use the following resume content as a base:
        
        {resume_text}
        
        The template should have a unique and engaging style while maintaining professionalism.
        """,
        f"""
        Generate a **minimalist** resume template for the job title: {job_title}.
        Focus on clarity and conciseness using the content below:
        
        {resume_text}
        
        Keep the design simple, clean, and optimized for ATS.
        """
    ]
    
    templates = []
    with st.spinner("Generating resume templates..."):
        for prompt in prompts:
            response = model.generate_content(prompt).text
            templates.append(response)
    
    return templates

# Resume Template Page
st.header("Resume Template Generator")

# Upload resume
uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf", key="template")
job_title = st.text_input("Enter Job Title")

if st.button("Generate Resume Templates"):
    if uploaded_file and job_title:
        with st.spinner("Extracting text from resume..."):
            resume_text = extract_text_from_pdf(uploaded_file)

        if resume_text:
            st.success("✅ Resume Text Extracted Successfully!")
            
            # Generate resume templates
            templates = generate_resume_templates(job_title, resume_text)

            if templates:
                st.subheader("Generated Resume Templates")
                st.markdown("### 🏢 Modern Resume Template")
                st.markdown(templates[0])
                st.markdown("---")
                st.markdown("### 🎨 Creative Resume Template")
                st.markdown(templates[1])
                st.markdown("---")
                st.markdown("### 📄 Minimalist Resume Template")
                st.markdown(templates[2])
            else:
                st.error("Failed to generate resume templates.")
    else:
        st.warning("Please upload a resume and provide a job title.")
