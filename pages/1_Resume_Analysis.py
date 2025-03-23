import streamlit as st
import pandas as pd
from google.generativeai import GenerativeModel
import PyPDF2
import re
import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate

load_dotenv()

# Set up Streamlit
st.set_page_config(page_title="Resume Analyzer", page_icon="📄")
st.title("Resume Analysis")
st.write("Upload your resume (PDF) and provide job details to analyze your fit for the role.")

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

# Load skills from CSV
@st.cache_data
def load_skills():
    try:
        skills_df = pd.read_csv("skill.csv")
        skills = skills_df.groupby('Subcategory')['Skill'].apply(list).to_dict()
        if '' in skills:
            skills['General'] = skills.pop('')  # Move unclassified skills under 'General'
        return skills
    except FileNotFoundError:
        st.error("skill.csv not found.")
        st.stop()
    except Exception as e:
        st.error(f"Error loading skill.csv: {e}")
        st.stop()

skills = load_skills()

# Function to extract text from PDF
def extract_text_from_pdf(file):
    try:
        pdf_reader = PyPDF2.PdfReader(file)
        text = "\n".join(page.extract_text() or "" for page in pdf_reader.pages)
        return text.strip() if text else None
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return None

# Function to extract skills dynamically
def extract_skills_from_text(text, skill_dict):
    text_lower = text.lower()
    extracted_skills = {category: set() for category in skill_dict.keys()}

    for category, skills_list in skill_dict.items():
        for skill in skills_list:
            if re.search(rf"\b{re.escape(skill.lower())}\b", text_lower):
                extracted_skills[category].add(skill)

    return {category: list(skills) for category, skills in extracted_skills.items() if skills}

# Function to recommend Udemy courses for missing skills
@st.cache_data
def load_udemy_courses():
    try:
        return pd.read_csv("udemy_courses.csv")
    except Exception as e:
        st.error(f"Error loading Udemy courses: {e}")
        return None

def recommend_courses(missing_skills):
    df = load_udemy_courses()
    if df is None:
        return {}

    recommendations = {}
    for category, skills_list in missing_skills.items():
        for skill in skills_list:
            skill_courses = df[df["Title"].str.contains(skill, case=False, na=False) |
                               df["Subtype"].str.contains(skill, case=False, na=False)]
            if not skill_courses.empty:
                recommendations[skill] = skill_courses[["Title", "URL"]].head(3).to_dict(orient="records")

    return recommendations

# Langchain Prompts
summary_prompt = PromptTemplate(
    input_variables=["resume_text"], template="Provide a **general summary** of the following resume:\n\n{resume_text}"
)
swot_prompt = PromptTemplate(
    input_variables=["job_title", "job_description", "resume_text"],
    template="""Analyze the following resume based on the job role and provide a SWOT analysis (Strengths, Weaknesses, Opportunities, and Threats):\n**Job Title:** {job_title}\n**Job Description:** {job_description}\n**Resume:**\n{resume_text}""",
)
score_prompt = PromptTemplate(
    input_variables=["job_title", "job_description", "resume_text"],
    template=""" 
    Provide a **match score (0-100%)** evaluating:
    - **Skill Match**
    - **Experience Match**
    - **Education Match**

    **Job Title:** {job_title} 
    **Job Description:** {job_description} 
    **Resume:**  
    {resume_text}
    """,
)

# Function to extract match scores
def extract_match_scores(score_response):
    matches = re.findall(r"(\w+)\s*:\s*(\d+)%", score_response)
    score_dict = {k.lower(): int(v) for k, v in matches}

    if len(score_dict) == 3:
        skill_match = score_dict.get("skill match", 0)
        experience_match = score_dict.get("experience match", 0)
        education_match = score_dict.get("education match", 0)
        overall_match = (skill_match + experience_match + education_match) / 3

        return f"""
        **Skill Match:** {skill_match}%  
        **Experience Match:** {experience_match}%  
        **Education Match:** {education_match}%  
        **Overall Match:** {overall_match:.2f}%
        """
    return f"Your resume matches **{score_response}** with the job description."

# Resume Analysis Page
st.header("Resume Analysis")

# Upload resume
uploaded_file = st.file_uploader("Upload your resume (PDF)", type="pdf")
job_title = st.text_input("Enter Job Title")
job_description = st.text_area("Enter Job Description")

if st.button("Analyze Resume"):
    if uploaded_file:
        with st.spinner("Extracting text from resume..."):
            resume_text = extract_text_from_pdf(uploaded_file)

        if resume_text:
            st.success("✅ Resume Text Extracted Successfully!")

            with st.expander("📝 General Resume Summary"):
                with st.spinner("Generating General Summary..."):
                    summary_response = model.generate_content(resume_text).text
                st.write(summary_response)

            with st.spinner("Analyzing Resume..."):
                swot_response = model.generate_content(
                    swot_prompt.format(job_title=job_title, job_description=job_description, resume_text=resume_text)
                ).text

                score_response = model.generate_content(
                    score_prompt.format(job_title=job_title, job_description=job_description, resume_text=resume_text)
                ).text.strip()

            if swot_response and score_response:
                with st.expander("🔍 View SWOT Analysis"):
                    st.write(swot_response)

                # Format Match Score Output
                formatted_score = extract_match_scores(score_response)
                with st.expander("📊 View Match Score Breakdown"):
                    st.subheader("📊 Match Score")
                    st.write(formatted_score)

                # Extract and compare skills
                required_skills = extract_skills_from_text(job_description, skills)
                available_skills = extract_skills_from_text(resume_text, skills)

                missing_skills = {}
                for category, subcats_or_skills in required_skills.items():
                    missing_skills[category] = {} if isinstance(subcats_or_skills, dict) else []
                    if isinstance(subcats_or_skills, dict):
                        for subcategory, required_skills_list in subcats_or_skills.items():
                            available_skills_list = available_skills.get(category, {}).get(subcategory, [])
                            missing_skills[category][subcategory] = list(set(required_skills_list) - set(available_skills_list))
                    else:
                        available_skills_list = available_skills.get(category, [])
                        missing_skills[category] = list(set(subcats_or_skills) - set(available_skills_list))
                
                missing_skills = {cat: subs for cat, subs in missing_skills.items() if subs}

                # Display Missing Skills and Udemy Recommendations
                if any(missing_skills.values()):
                    with st.expander("🛠️ Missing Skills & Recommended Courses"):
                        st.subheader("🛠️ Missing Skills & Recommended Courses")

                        for category, skills_list in missing_skills.items():
                            if skills_list:
                                st.markdown(f"**{category}:** {', '.join(skills_list)}")

                        course_recommendations = recommend_courses(missing_skills)

                        if course_recommendations:
                            st.subheader("📚 Suggested Udemy Courses")
                            for skill, courses in course_recommendations.items():
                                st.markdown(f"**{skill}:**")
                                for course in courses:
                                    st.markdown(f"- [{course['Title']}]({course['URL']})")
                        else:
                            st.info("No relevant Udemy courses found for missing skills.")
                else:
                    st.success("🎉 No missing skills! You are a great fit!")