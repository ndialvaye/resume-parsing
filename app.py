import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_bytes
import re
from difflib import get_close_matches
from io import BytesIO

skills_list = [
    "Python", "Java", "JavaScript", "SQL", "HTML", "CSS", "C++", "C#", "PHP", "React",
    "Angular", "Node.js", "Excel", "Word", "PowerPoint", "MySQL", "MongoDB", "Django", "Flask",
    "Git", "Linux", "Docker", "Kubernetes", "Photoshop", "Illustrator", "Machine Learning",
    "Deep Learning", "Data Analysis", "TensorFlow", "Pandas", "NumPy", "OpenCV", "NLP",
    "REST API", "CI/CD", "Genetec", "Axis", "Morpho", "Geosatis", "VMS", "Access Control", "Cybersecurity"
]

def extract_text_from_pdf(file):
    text = ""
    try:
        doc = fitz.open(stream=file.read(), filetype="pdf")
        for page in doc:
            text += page.get_text()
    except:
        images = convert_from_bytes(file.read())
        for img in images:
            text += pytesseract.image_to_string(img)
    return text.strip()

def extract_data(text):
    data = {
        "Name": "", "Email": "", "Phone": "", "Address": "", "Profile": "",
        "Skills": "", "Experience": "", "Education": "", "Languages": "", "Driving License": ""
    }
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if emails: data["Email"] = emails[0].lower()
    phones = re.findall(r'(\+?\d[\d\s\-\(\)]{7,})', text)
    if phones: data["Phone"] = re.sub(r"[^\d+]", "", phones[0])
    lines = text.split("\n")
    if lines:
        first_line = lines[0].strip()
        if len(first_line.split()) <= 4:
            data["Name"] = first_line.title()
    address_match = re.search(r"(adresse|address)\s*[:\-]*\s*(.+)", text, re.IGNORECASE)
    if address_match:
        data["Address"] = address_match.group(2).split("\n")[0].strip().title()
    profile_match = re.search(r"(profil|objectif)\s*[:\-]*\s*(.+?)(\n|experience|formation|education|skills)", text, re.IGNORECASE | re.DOTALL)
    if profile_match: data["Profile"] = profile_match.group(2).strip()
    edu_match = re.search(r"(formation|education)\s*[:\-]*\s*(.+?)(experience|skills|competences|languages)", text, re.IGNORECASE | re.DOTALL)
    if edu_match: data["Education"] = edu_match.group(2).strip()
    exp_match = re.search(r"(expérience|experience)\s*[:\-]*\s*(.+?)(formation|education|skills|competences|languages)", text, re.IGNORECASE | re.DOTALL)
    if exp_match: data["Experience"] = exp_match.group(2).strip()
    license_match = re.search(r"permis\s+([A-Za-z])", text, re.IGNORECASE)
    if license_match: data["Driving License"] = f"Permis {license_match.group(1).upper()}"
    skill_words = re.findall(r'\b\w[\w\-\+#/.]*\b', text)
    matched_skills = set()
    for word in skill_words:
        match = get_close_matches(word, skills_list, n=1, cutoff=0.85)
        if match: matched_skills.add(match[0])
    data["Skills"] = ", ".join(sorted(matched_skills))
    langs = []
    if "français" in text.lower(): langs.append("Français")
    if "anglais" in text.lower(): langs.append("Anglais")
    if "espagnol" in text.lower(): langs.append("Espagnol")
    if "arabe" in text.lower(): langs.append("Arabe")
    data["Languages"] = ", ".join(langs)
    return data

st.title("📄 Analyse Automatique de CVs")
uploaded_files = st.file_uploader("Déposez vos CVs ici", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    all_results = []
    for file in uploaded_files:
        with st.spinner(f"Traitement de {file.name}..."):
            text = extract_text_from_pdf(file)
            data = extract_data(text)
            all_results.append(data)
    df = pd.DataFrame(all_results)
    st.success("✅ Analyse terminée !")
    st.dataframe(df)
    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    st.download_button("⬇️ Télécharger le fichier Excel", data=excel_buffer.getvalue(), file_name="résultats_cv.xlsx")
