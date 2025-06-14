import streamlit as st
import fitz  # PyMuPDF
import re
import io

# ----------- PDF Text Extraction -----------
def extract_text_from_pdf(file_stream):
    text = ""
    with fitz.open(stream=file_stream, filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

# ----------- Extract Bold Lines from Sections -----------
def extract_bold_lines_from_section(file_stream, section_name, stop_words):
    bold_lines = []
    inside_section = False

    with fitz.open(stream=file_stream, filetype="pdf") as doc:
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span["text"].strip()
                        if not text:
                            continue
                        if section_name.upper() in text.upper():
                            inside_section = True
                            continue
                        if any(stop in text.upper() for stop in stop_words):
                            inside_section = False
                        if inside_section and ("bold" in span["font"].lower() or span.get("flags", 0) & 2):
                            bold_lines.append(text)
    return bold_lines if bold_lines else [f"No bold lines found in {section_name.upper()}"]

# ----------- Extract Section Text by Heading -----------
def extract_section(text, section, stop_sections):
    pattern = rf"{section.upper()}(.*?)(?=\n(?:{'|'.join(stop_sections).upper()}|$))"
    match = re.search(pattern, text, re.DOTALL)
    return match.group(1).strip() if match else "Not found"

# ----------- Other Utilities -----------
def extract_certificates(text):
    return [line.strip("•- ") for line in text.splitlines() if line.strip()]

def extract_languages(text):
    match = re.search(r"LANGUAGES\n([A-Za-z, ]+)", text)
    return match.group(1).strip().split(',') if match else ["Not found"]

def parse_skills(skills_text):
    lines = skills_text.splitlines()
    skills = {}
    current = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if ":" not in line and re.match(r"^[A-Za-z ]+$", line):
            current = line
            skills[current] = []
        elif current:
            skills[current] += [item.strip() for item in line.split(",") if item.strip()]
    return skills

def extract_email(text):
    match = re.search(r'[\w\.-]+@[\w\.-]+', text)
    return match.group() if match else "Not found"

def extract_phone(text):
    match = re.search(r'\b\d{10}\b', text)
    return match.group() if match else "Not found"

def extract_name(text):
    match = re.match(r"^[A-Za-z ]+", text)
    return match.group().strip() if match else "Not found"

def extract_location(text):
    match = re.search(r'\bRajahmundry.*', text)
    return match.group().strip() if match else "Not found"

# ----------- Parse Education into Sections -----------
def parse_education(edu_text):
    btech, inter, tenth = [], [], []
    current_section = None
    lines = [line.strip("•- ") for line in edu_text.splitlines() if line.strip()]

    for line in lines:
        l = line.lower()
        if "bachelor" in l or "b.tech" in l or "engineering" in l:
            current_section = btech
        elif "intermediate" in l or "junior college" in l:
            current_section = inter
        elif "secondary education" in l or "high school" in l:
            current_section = tenth

        if current_section is not None:
            current_section.append(line)

    return btech, inter, tenth

# ----------- Streamlit App -----------
def main():
    st.set_page_config("AI Resume Parser", layout="centered", page_icon="🧠")
    st.markdown("""
        <style>
            .big-title {
                font-size: 36px;
                font-weight: bold;
                text-align: center;
                color: #4A90E2;
            }
            .section-title {
                font-size: 24px;
                margin-top: 30px;
                color: #ffffff;
            }
            .basic-info-box {
                background-color: #1A1C24;
                padding: 15px 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                color: white;
            }
            .container-box {
                background-color: #1A1C24;
                color: white;
                padding: 15px 20px;
                border-radius: 10px;
                margin-bottom: 20px;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="big-title">📄 AI Resume Parser</div>', unsafe_allow_html=True)
    st.markdown("Upload your resume PDF and extract key information with clean formatting.")

    uploaded_file = st.file_uploader("📤 Upload your Resume (PDF only)", type=["pdf"])

    if uploaded_file:
        file_bytes = uploaded_file.read()
        file_stream = io.BytesIO(file_bytes)

        with st.spinner("🛠️ Parsing your resume..."):
            file_stream.seek(0)
            raw_text = extract_text_from_pdf(file_stream)

            name = extract_name(raw_text)
            email = extract_email(raw_text)
            phone = extract_phone(raw_text)
            location = extract_location(raw_text)

            profile = extract_section(raw_text, "PROFILE", ["EDUCATION"])
            education = extract_section(raw_text, "EDUCATION", ["EXPERIENCE"])
            skills_text = extract_section(raw_text, "SKILLS", ["PROJECTS"])
            cert_text = extract_section(raw_text, "CERTIFICATES", ["LANGUAGES"])
            certificates = extract_certificates(cert_text)
            languages = extract_languages(raw_text)
            skills = parse_skills(skills_text)

            file_stream.seek(0)
            bold_projects = extract_bold_lines_from_section(file_stream, "PROJECTS", ["CERTIFICATES", "SKILLS", "LANGUAGES", "DECLARATION"])

            file_stream.seek(0)
            bold_experience = extract_bold_lines_from_section(file_stream, "EXPERIENCE", ["SKILLS", "PROJECTS", "CERTIFICATES", "LANGUAGES", "DECLARATION"])

            btech, inter, tenth = parse_education(education)

        # Output
        st.markdown('<div class="section-title">👤 Basic Info</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="basic-info-box">'
            f'<strong>Name:</strong> {name}<br>'
            f'<strong>Email:</strong> {email}<br>'
            f'<strong>Phone:</strong> {phone}<br>'
            f'<strong>Location:</strong> {location}'
            f'</div>', unsafe_allow_html=True
        )

        st.markdown('<div class="section-title">🧠 Profile Summary</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="container-box"><pre>{profile}</pre></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-title">🎓 Education</div>', unsafe_allow_html=True)

        def format_edu_block(title, items):
            html = f"<h4>{title}</h4><div class='container-box'>"
            for line in items:
                html += f"<p>• {line}</p>"
            html += "</div>"
            return html

        if btech:
            st.markdown(format_edu_block("Bachelor of Technology", btech), unsafe_allow_html=True)
        if inter:
            st.markdown(format_edu_block("Intermediate", inter), unsafe_allow_html=True)
        if tenth:
            st.markdown(format_edu_block("10th Class", tenth), unsafe_allow_html=True)

        st.markdown('<div class="section-title">💼 Experience</div>', unsafe_allow_html=True)
        experience_html = '<div class="container-box">\n'
        experience_html += ''.join(f"<p>• {line}</p>\n" for line in bold_experience)
        experience_html += '</div>'
        st.markdown(experience_html, unsafe_allow_html=True)

        st.markdown('<div class="section-title">🛠 Skills</div>', unsafe_allow_html=True)
        skills_html = '<div class="container-box">\n'
        for cat, val in skills.items():
            skills_html += f"<p><strong>{cat}:</strong> {', '.join(val)}</p>\n"
        skills_html += '</div>'
        st.markdown(skills_html, unsafe_allow_html=True)

        st.markdown('<div class="section-title">📌 Projects </div>', unsafe_allow_html=True)
        projects_html = '<div class="container-box">\n'
        projects_html += ''.join(f"<p>• {line}</p>\n" for line in bold_projects)
        projects_html += '</div>'
        st.markdown(projects_html, unsafe_allow_html=True)

        st.markdown('<div class="section-title">🏅 Certificates</div>', unsafe_allow_html=True)
        cert_html = '<div class="container-box">\n'
        cert_html += ''.join(f"<p>• {cert}</p>\n" for cert in certificates)
        cert_html += '</div>'
        st.markdown(cert_html, unsafe_allow_html=True)

        st.markdown('<div class="section-title">🌐 Languages</div>', unsafe_allow_html=True)
        lang_html = '<div class="container-box">\n'
        lang_html += f"<p>{', '.join(languages)}</p>\n"
        lang_html += '</div>'
        st.markdown(lang_html, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
