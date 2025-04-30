
import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
import spacy
import re
from difflib import get_close_matches

# Utilise un modèle vide de spaCy compatible avec Streamlit Cloud
nlp = spacy.blank("en")

skills_list = [
    "Python", "Machine Learning", "SQL", "Excel", "Access", "MySQL",
    "Genetec", "Axis", "Morpho", "Geosatis", "Cloud Computing",
    "Security Systems", "Data Analysis", "Artificial Intelligence",
    "Networking", "PowerPoint", "Word"
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

    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if emails:
        entities["Email"] = emails[0]

    phones = re.findall(r'(\+?\d[\d\s\-\(\)]{7,})', text)
    if phones:
        entities["Phone"] = phones[0].replace(" ", "").replace("-", "")

    for ent in doc.ents:
        if ent.label_ == "PERSON" and 1 <= len(ent.text.split()) <= 4:
            entities["Name"] = ent.text.strip()
            break

    if "permis" in text.lower():
        permis_match = re.search(r'permis\s+([A-Za-z]{1})', text, re.IGNORECASE)
        if permis_match:
            entities["Driving License"] = f"Permis {permis_match.group(1).upper()}"

    address_match = re.search(r'(adresse|address)[\:\- ]*(.*?)(\n|$)', text, re.IGNORECASE)
    if address_match:
        entities["Address"] = address_match.group(2).strip()

    profile_match = re.search(r'(profil|objectif|profile)[\:\- ]*(.*?)(experience|skills|formation|education|competences)', text, re.IGNORECASE|re.DOTALL)
    if profile_match:
        entities["Profile"] = profile_match.group(2).strip()

    found_skills = set()
    for word in text.split():
        close = get_close_matches(word, skills_list, n=1, cutoff=0.8)
        if close:
            found_skills.add(close[0])
    entities["Skills"] = ", ".join(sorted(found_skills))

    education_match = re.search(r'(formation|education)[\:\- ]*(.*?)(experience|skills|competences|languages)', text, re.IGNORECASE|re.DOTALL)
    if education_match:
        entities["Education"] = education_match.group(2).strip()

    experience_match = re.search(r'(experience|expérience)[\:\- ]*(.*?)(formation|education|skills|competences|languages)', text, re.IGNORECASE|re.DOTALL)
    if experience_match:
        entities["Experience"] = experience_match.group(2).strip()

    language_keywords = ['français', 'anglais', 'espagnol', 'arabe']
    lang = []
    for k in language_keywords:
        if k in text.lower():
            lang.append(k.capitalize())
    if lang:
        entities["Languages"] = ", ".join(lang)

    return entities

st.title("📄 Analyse automatique de CVs avec Python")

st.markdown("Déposez un ou plusieurs CVs pour analyser leur contenu automatiquement.")

uploaded_files = st.file_uploader("📤 Déposer vos fichiers CV", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    all_entities = []
    for file in uploaded_files:
        with st.spinner(f"Traitement de {file.name}..."):
            text = extract_text_from_pdf(file)
            entities = extract_entities(text)
            all_entities.append(entities)

    df = pd.DataFrame(all_entities)
    st.success("✅ Extraction terminée !")
    st.dataframe(df)

    excel_buffer = BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    st.download_button("⬇️ Télécharger Excel", data=excel_buffer.getvalue(), file_name="resultats_cv.xlsx")
