import os
import io
from pathlib import Path

import streamlit as st
from PyPDF2 import PdfReader
from openai import OpenAI


# =========================
# App Configuration
# =========================

st.set_page_config(
    page_title="Qatar STEM Planner",
    page_icon="🧪",
    layout="wide"
)

APP_TITLE = "Qatar STEM Lesson Planning and Evaluation Tool"
APP_SUBTITLE = "A standards-based AI-supported STEM co-planning prototype for science teachers in Qatar"


# =========================
# Helper Functions
# =========================

def get_openai_client():
    """
    Reads OpenAI API key from Streamlit Secrets.
    The key should NOT be written inside GitHub.
    """
    api_key = st.secrets.get("OPENAI_API_KEY", None)

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def extract_text_from_pdf(uploaded_file):
    """
    Extract text from uploaded PDF lesson pages.
    """
    if uploaded_file is None:
        return ""

    text = ""
    try:
        pdf_reader = PdfReader(uploaded_file)
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        st.error(f"Could not read the PDF file: {e}")
        return ""

    return text.strip()


def load_text_file(path):
    """
    Load a text file safely.
    """
    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except Exception:
        return ""


def load_pdf_file(path):
    """
    Load PDF text from knowledge_base folder.
    """
    text = ""
    try:
        with open(path, "rb") as file:
            reader = PdfReader(file)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception:
        return ""

    return text.strip()


def load_knowledge_base():
    """
    Load all .txt and .pdf files from knowledge_base folder.
    """
    kb_folder = Path("knowledge_base")
    knowledge_text = ""

    if not kb_folder.exists():
        return "", []

    loaded_files = []

    for file_path in kb_folder.iterdir():
        if file_path.suffix.lower() == ".txt":
            content = load_text_file(file_path)
            if content:
                knowledge_text += f"\n\n--- Source: {file_path.name} ---\n{content}"
                loaded_files.append(file_path.name)

        elif file_path.suffix.lower() == ".pdf":
            content = load_pdf_file(file_path)
            if content:
                knowledge_text += f"\n\n--- Source: {file_path.name} ---\n{content}"
                loaded_files.append(file_path.name)

    return knowledge_text.strip(), loaded_files


def load_rubric():
    """
    Load STEM lesson plan rubric.
    """
    rubric_path = Path("rubrics/stem_lesson_plan_rubric.txt")

    if rubric_path.exists():
        return load_text_file(rubric_path)

    return """
STEM Lesson Plan Quality Rubric - 100 Points

1. Curriculum Alignment - 10 points
2. Science Content Grounding - 10 points
3. STEM Integration - 15 points
4. Engineering Design Process - 15 points
5. Qatar Local Context - 10 points
6. SDG Connection - 5 points
7. Assessment Plan - 10 points
8. Differentiation and Inclusion - 10 points
9. Resources, Safety, and Time Management - 5 points
10. Teacher Creative Adaptation - 10 points
"""


def call_openai(prompt, model):
    """
    Call OpenAI Responses API.
    """
    client = get_openai_client()

    if client is None:
        st.error("OpenAI API key is missing. Add OPENAI_API_KEY in Streamlit Secrets.")
        return None

    try:
        response = client.responses.create(
            model=model,
            input=prompt,
            temperature=0.3
        )
        return response.output_text

    except Exception as e:
        st.error(f"OpenAI API error: {e}")
        return None


def build_lesson_plan_prompt(
    lesson_text,
    knowledge_base,
    rubric,
    teacher_inputs
):
    """
    Build a controlled prompt for generating a structured STEM lesson plan.
    """
    prompt = f"""
You are a standards-based AI-supported STEM lesson planning assistant for science teachers in Qatar.

Important:
You are NOT a general chatbot.
You must generate a curriculum-grounded STEM lesson plan using:
1. The uploaded textbook lesson pages.
2. The teacher's structured inputs.
3. The embedded STEM knowledge base.
4. The STEM lesson plan template.
5. The quality rubric.
6. Qatar local context.
7. Relevant Sustainable Development Goals.

The teacher remains the final decision-maker. Include a section called "Teacher Creative Adaptation" where the teacher can adapt the plan.

========================
TEACHER INPUTS
========================

Grade Level: {teacher_inputs["grade_level"]}
Subject: {teacher_inputs["subject"]}
Unit: {teacher_inputs["unit"]}
Lesson Title / Topic: {teacher_inputs["lesson_title"]}
Learning Outcomes: {teacher_inputs["learning_outcomes"]}
Lesson Duration: {teacher_inputs["lesson_duration"]}
Number of Students: {teacher_inputs["number_of_students"]}
Student Level: {teacher_inputs["student_level"]}
Available Resources: {teacher_inputs["available_resources"]}
Classroom Constraints: {teacher_inputs["classroom_constraints"]}
Qatar Local Context: {teacher_inputs["qatar_context"]}
Selected SDGs: {teacher_inputs["sdgs"]}
Teacher Notes: {teacher_inputs["teacher_notes"]}

========================
UPLOADED TEXTBOOK LESSON PAGES
========================

{lesson_text}

========================
EMBEDDED KNOWLEDGE BASE
========================

{knowledge_base}

========================
STEM QUALITY RUBRIC
========================

{rubric}

========================
TASK
========================

Generate a complete STEM lesson plan using the following required structure:

1. Lesson Overview
- Grade level
- Subject
- Unit
- Lesson title
- Duration
- Main science concept
- Learning outcomes

2. Curriculum Grounding
- Key textbook concepts used
- Prior knowledge
- Misconceptions students may have

3. Real-World STEM Problem
- Problem statement
- Why it matters
- Qatar local connection
- SDG connection

4. STEM Integration
- Science
- Technology
- Engineering
- Mathematics

5. Driving Question

6. Engineering Design Challenge
- What students will design, build, model, test, or improve

7. Lesson Sequence
Use a clear sequence:
- Engage
- Explore
- Explain
- Elaborate / Engineer
- Evaluate

8. Teacher Role
- Facilitation moves
- Guiding questions
- How to support without giving direct answers

9. Student Role
- Individual work
- Group work
- Communication and presentation

10. Assessment Plan
- Formative assessment
- Summative assessment
- Rubric criteria

11. Differentiation
- Support for struggling students
- Extension for high-achieving students

12. Resources and Safety
- Materials
- Technology
- Safety
- Time management

13. Teacher Creative Adaptation
- What the teacher can modify
- Alternative resources
- Local examples
- Adjustments for different student levels

14. Expected Student Product
- Model, prototype, explanation, poster, presentation, data table, graph, or written response

15. Reflection After Implementation
- What the teacher should review after the lesson

Write the lesson plan clearly and professionally.
Avoid generic content.
Use the uploaded lesson pages as the main content source.
"""
    return prompt


def build_evaluation_prompt(generated_plan, rubric, teacher_inputs):
    """
    Build a controlled prompt for evaluating the generated plan.
    """
    prompt = f"""
You are an expert STEM lesson plan evaluator.

Evaluate the following STEM lesson plan using the rubric below.

========================
TEACHER CONTEXT
========================

Grade Level: {teacher_inputs["grade_level"]}
Subject: {teacher_inputs["subject"]}
Unit: {teacher_inputs["unit"]}
Lesson Title / Topic: {teacher_inputs["lesson_title"]}

========================
STEM QUALITY RUBRIC
========================

{rubric}

========================
LESSON PLAN TO EVALUATE
========================

{generated_plan}

========================
TASK
========================

Provide a structured evaluation with:

1. Overall Quality Score out of 100

2. Sub-scores:
- Curriculum Alignment /10
- Science Content Grounding /10
- STEM Integration /15
- Engineering Design Process /15
- Qatar Local Context /10
- SDG Connection /5
- Assessment Plan /10
- Differentiation and Inclusion /10
- Resources, Safety, and Time Management /5
- Teacher Creative Adaptation /10

3. Strengths

4. Weaknesses

5. Specific Improvement Suggestions

6. Revised Priority Actions
List the top 5 changes the teacher should make to improve the plan.

Be strict, evidence-based, and clear.
Do not give full marks unless the plan truly meets the criteria.
"""
    return prompt


# =========================
# Sidebar
# =========================

st.sidebar.title("Research Prototype Controls")

model = st.sidebar.selectbox(
    "Choose AI Model",
    ["gpt-4o-mini", "gpt-4o"],
    index=0
)

st.sidebar.info(
    "Use gpt-4o-mini for testing and gpt-4o for higher-quality final outputs."
)

knowledge_base_text, loaded_kb_files = load_knowledge_base()
rubric_text = load_rubric()

st.sidebar.subheader("Knowledge Base Status")

if loaded_kb_files:
    st.sidebar.success("Knowledge-base files loaded:")
    for file_name in loaded_kb_files:
        st.sidebar.write(f"- {file_name}")
else:
    st.sidebar.warning("No knowledge-base files found yet.")

st.sidebar.subheader("Rubric Status")
if rubric_text:
    st.sidebar.success("Rubric loaded.")
else:
    st.sidebar.warning("Rubric not found.")


# =========================
# Main Interface
# =========================

st.title(APP_TITLE)
st.caption(APP_SUBTITLE)

st.markdown("""
This prototype supports science teachers in Qatar by guiding them through a structured STEM lesson-planning process. 
It uses uploaded textbook lesson pages, a knowledge base, and a quality rubric to generate and evaluate STEM lesson plans.
""")

st.divider()

# Step 1
st.header("Step 1: Upload Textbook Lesson Pages")

uploaded_pdf = st.file_uploader(
    "Upload only the relevant textbook lesson pages as PDF",
    type=["pdf"]
)

lesson_text = ""

if uploaded_pdf:
    lesson_text = extract_text_from_pdf(uploaded_pdf)

    if lesson_text:
        st.success("Lesson PDF text extracted successfully.")
        with st.expander("Preview extracted lesson text"):
            st.write(lesson_text[:4000])
    else:
        st.warning("No readable text was extracted. The PDF may be scanned or image-based.")

st.divider()

# Step 2
st.header("Step 2: Enter Curriculum Information")

col1, col2 = st.columns(2)

with col1:
    grade_level = st.selectbox(
        "Grade Level",
        ["Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
    )

    subject = st.selectbox(
        "Subject",
        ["Science", "Physics", "Chemistry", "Biology", "Integrated Science"]
    )

    unit = st.text_input("Unit", placeholder="Example: Digestive System")

with col2:
    lesson_title = st.text_input(
        "Lesson Title / Topic",
        placeholder="Example: How do living organisms obtain food?"
    )

    lesson_duration = st.text_input(
        "Lesson Duration",
        placeholder="Example: 45 minutes / 90 minutes"
    )

    learning_outcomes = st.text_area(
        "Learning Outcomes",
        placeholder="Write the expected learning outcomes for the lesson."
    )

st.divider()

# Step 3
st.header("Step 3: Enter Classroom Context")

col3, col4 = st.columns(2)

with col3:
    number_of_students = st.number_input(
        "Number of Students",
        min_value=1,
        max_value=60,
        value=24
    )

    student_level = st.selectbox(
        "General Student Level",
        [
            "Mixed ability",
            "Struggling students",
            "Average level",
            "High-achieving students",
            "Gifted students"
        ]
    )

with col4:
    available_resources = st.text_area(
        "Available Resources",
        placeholder="Example: lab equipment, tablets, internet, recycled materials, Excel, sensors"
    )

    classroom_constraints = st.text_area(
        "Classroom Constraints",
        placeholder="Example: limited time, limited lab materials, no internet, large class size"
    )

st.divider()

# Step 4
st.header("Step 4: Select Qatar Local Context")

qatar_context_options = [
    "Water conservation in Qatar",
    "Energy use and sustainability",
    "Desert environment",
    "Marine environment and pollution",
    "Food security",
    "Health and lifestyle in Qatar",
    "Transportation and sustainable cities",
    "Waste management and recycling",
    "Air quality and climate",
    "Other"
]

selected_qatar_context = st.multiselect(
    "Choose one or more Qatar local contexts",
    qatar_context_options
)

other_qatar_context = ""

if "Other" in selected_qatar_context:
    other_qatar_context = st.text_input("Write another Qatar local context")

qatar_context = ", ".join(selected_qatar_context)

if other_qatar_context:
    qatar_context += f", {other_qatar_context}"

st.divider()

# Step 5
st.header("Step 5: Select SDG Connections")

sdg_options = [
    "SDG 3: Good Health and Well-being",
    "SDG 4: Quality Education",
    "SDG 6: Clean Water and Sanitation",
    "SDG 7: Affordable and Clean Energy",
    "SDG 11: Sustainable Cities and Communities",
    "SDG 12: Responsible Consumption and Production",
    "SDG 13: Climate Action",
    "SDG 14: Life Below Water",
    "SDG 15: Life on Land"
]

selected_sdgs = st.multiselect(
    "Choose relevant SDGs",
    sdg_options
)

sdgs = ", ".join(selected_sdgs)

teacher_notes = st.text_area(
    "Additional Teacher Notes",
    placeholder="Write any special notes about students, school context, or lesson needs."
)

st.divider()

# Step 6
st.header("Step 6: Generate STEM Lesson Plan")

teacher_inputs = {
    "grade_level": grade_level,
    "subject": subject,
    "unit": unit,
    "lesson_title": lesson_title,
    "learning_outcomes": learning_outcomes,
    "lesson_duration": lesson_duration,
    "number_of_students": number_of_students,
    "student_level": student_level,
    "available_resources": available_resources,
    "classroom_constraints": classroom_constraints,
    "qatar_context": qatar_context,
    "sdgs": sdgs,
    "teacher_notes": teacher_notes
}

required_fields_missing = []

if not uploaded_pdf:
    required_fields_missing.append("Uploaded textbook lesson pages PDF")

if not lesson_title:
    required_fields_missing.append("Lesson title/topic")

if not learning_outcomes:
    required_fields_missing.append("Learning outcomes")

if not available_resources:
    required_fields_missing.append("Available resources")

if not qatar_context:
    required_fields_missing.append("Qatar local context")

if not sdgs:
    required_fields_missing.append("SDG connection")

if required_fields_missing:
    st.warning("Before generating the plan, please complete:")
    for field in required_fields_missing:
        st.write(f"- {field}")

generate_button = st.button("Generate STEM Lesson Plan", type="primary")

if generate_button:
    if required_fields_missing:
        st.error("Please complete the required fields first.")
    elif not lesson_text:
        st.error("The uploaded PDF did not provide readable text.")
    else:
        with st.spinner("Generating STEM lesson plan..."):
            lesson_prompt = build_lesson_plan_prompt(
                lesson_text=lesson_text,
                knowledge_base=knowledge_base_text,
                rubric=rubric_text,
                teacher_inputs=teacher_inputs
            )

            generated_plan = call_openai(lesson_prompt, model)

            if generated_plan:
                st.session_state["generated_plan"] = generated_plan
                st.success("STEM lesson plan generated successfully.")

if "generated_plan" in st.session_state:
    st.subheader("Generated STEM Lesson Plan")
    st.markdown(st.session_state["generated_plan"])

    st.download_button(
        label="Download Lesson Plan as TXT",
        data=st.session_state["generated_plan"],
        file_name="generated_stem_lesson_plan.txt",
        mime="text/plain"
    )

st.divider()

# Step 7
st.header("Step 7: Evaluate Lesson Plan Quality")

if "generated_plan" not in st.session_state:
    st.info("Generate a STEM lesson plan first, then evaluate it.")
else:
    evaluate_button = st.button("Evaluate Lesson Plan Quality")

    if evaluate_button:
        with st.spinner("Evaluating lesson plan quality..."):
            evaluation_prompt = build_evaluation_prompt(
                generated_plan=st.session_state["generated_plan"],
                rubric=rubric_text,
                teacher_inputs=teacher_inputs
            )

            evaluation_result = call_openai(evaluation_prompt, model)

            if evaluation_result:
                st.session_state["evaluation_result"] = evaluation_result
                st.success("Lesson plan evaluation completed.")

if "evaluation_result" in st.session_state:
    st.subheader("STEM Lesson Plan Quality Evaluation")
    st.markdown(st.session_state["evaluation_result"])

    st.download_button(
        label="Download Evaluation as TXT",
        data=st.session_state["evaluation_result"],
        file_name="stem_lesson_plan_evaluation.txt",
        mime="text/plain"
    )

st.divider()

# Step 8
st.header("Step 8: Teacher Creative Adaptation")

st.markdown("""
The AI-generated lesson plan is a draft. The teacher should review and adapt it based on:
- student needs,
- available classroom resources,
- school context,
- lesson timing,
- safety,
- and professional judgment.
""")

teacher_adaptation = st.text_area(
    "Write teacher adaptations here",
    placeholder="Example: I will replace the lab activity with a low-cost classroom model because the lab is not available."
)

if teacher_adaptation:
    st.success("Teacher adaptation recorded.")
    st.markdown("### Teacher Adaptation Notes")
    st.write(teacher_adaptation)
