# 

import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
import spacy
import re
from difflib import get_close_matches

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_trf")
except:
    nlp = spacy.load("en_core_web_sm")

# Load skills list
@st.cache_data
def load_skills():
    skills = [
        "Python", "Machine Learning", "SQL", "Excel", "Access", "MySQL",
        "Genetec", "Axis", "Morpho", "Geosatis", "Cloud Computing",
        "Security Systems", "Data Analysis", "Artificial Intelligence",
        "Networking", "PowerPoint", "Word"
    ]
    return skills

skills_list = load_skills()

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

def extract_entities(text):
    doc = nlp(text)

    entities = {
        "Name": "",
        "Address": "",
        "Phone": "",
        "Email": "",
        "Driving License": "",
        "Profile": "",
        "Skills": "",
        "Experience": "",
        "Education": "",
        "Languages": "",
        "Certifications": ""
    }

    # Email
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if emails:
        entities["Email"] = emails[0]

    # Phone
    phones = re.findall(r'(\+?\d[\d\s\-\(\)]{7,})', text)
    if phones:
        entities["Phone"] = phones[0].replace(" ", "").replace("-", "")

    # Name
    for ent in doc.ents:
        if ent.label_ == "PERSON" and 1 <= len(ent.text.split()) <= 4:
            entities["Name"] = ent.text.strip()
            break

    # Driving License
    if "permis" in text.lower():
        permis_match = re.search(r'permis\s+([A-Za-z]{1})', text, re.IGNORECASE)
        if permis_match:
            entities["Driving License"] = f"Permis {permis_match.group(1).upper()}"

    # Address
    address_match = re.search(r'(adresse|address)[\:\- ]*(.*?)(\n|$)', text, re.IGNORECASE)
    if address_match:
        entities["Address"] = address_match.group(2).strip()

    # Profile
    profile_match = re.search(r'(profil|objectif|profile)[\:\- ]*(.*?)(experience|skills|formation|education|competences)', text, re.IGNORECASE|re.DOTALL)
    if profile_match:
        entities["Profile"] = profile_match.group(2).strip()

    # Skills
    found_skills = set()
    for word in text.split():
        close = get_close_matches(word, skills_list, n=1, cutoff=0.8)
        if close:
            found_skills.add(close[0])
    entities["Skills"] = ", ".join(sorted(found_skills))

    # Education
    education_match = re.search(r'(formation|education)[\:\- ]*(.*?)(experience|skills|competences|languages)', text, re.IGNORECASE|re.DOTALL)
    if education_match:
        entities["Education"] = education_match.group(2).strip()

    # Experience
    experience_match = re.search(r'(experience|expérience)[\:\- ]*(.*?)(formation|education|skills|competences|languages)', text, re.IGNORECASE|re.DOTALL)
    if experience_match:
        entities["Experience"] = experience_match.group(2).strip()

    # Languages
    language_keywords = ['français', 'anglais', 'espagnol', 'arabe']
    lang = []
    for k in language_keywords:
        if k in text.lower():
            lang.append(k.capitalize())
    if lang:
        entities["Languages"] = ", ".join(lang)

    return entities

# --- Streamlit UI ---

st.title("📄 Résumé Parsing Niveau Entreprise")

st.markdown("""
**Instructions** :
- Déposez un ou plusieurs CVs (PDF ou Image)
- Le système extrait automatiquement les informations
- Vous pouvez télécharger les résultats en Excel/CSV
""")

uploaded_files = st.file_uploader("📤 Déposer un ou plusieurs CVs", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    all_entities = []
    for file in uploaded_files:
        with st.spinner(f"Traitement de {file.name}..."):
            text = extract_text_from_pdf(file)
            entities = extract_entities(text)
            all_entities.append(entities)
    
    df = pd.DataFrame(all_entities)
    
    st.success("✅ Extraction terminée ! Voici le tableau des CVs :")
    st.dataframe(df, use_container_width=True)

    # Télécharger les résultats
    output_excel = BytesIO()
    with pd.ExcelWriter(output_excel, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    output_excel.seek(0)

    st.download_button("⬇️ Télécharger Résultats (Excel)", data=output_excel, file_name="resumes_parsed.xlsx")

    output_csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("⬇️ Télécharger Résultats (CSV)", data=output_csv, file_name="resumes_parsed.csv")
