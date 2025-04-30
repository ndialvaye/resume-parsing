
import streamlit as st
import pandas as pd
import fitz  # PyMuPDF
import pytesseract
from pdf2image import convert_from_bytes
from io import BytesIO
import re
from difflib import get_close_matches

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
    entities = {
        "Nom": "",
        "Email": "",
        "Téléphone": "",
        "Adresse": "",
        "Profil": "",
        "Compétences": "",
        "Expérience": "",
        "Formation": "",
        "Langues": ""
    }

    # Email
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    if emails:
        entities["Email"] = emails[0]

    # Téléphone
    phones = re.findall(r'(\+?\d[\d\s\-\(\)]{7,})', text)
    if phones:
        entities["Téléphone"] = phones[0].replace(" ", "").replace("-", "")

    # Nom (première ligne généralement)
    lines = text.split("\n")
    if lines:
        potential_name = lines[0].strip()
        if len(potential_name.split()) <= 4:
            entities["Nom"] = potential_name

    # Adresse
    match = re.search(r"(adresse|address)\s*[:\-\n]?\s*(.*?)\n", text, re.IGNORECASE)
    if match:
        entities["Adresse"] = match.group(2).strip()

    # Profil
    match = re.search(r"(profil|objectif)\s*[:\-\n]?\s*(.*?)\n", text, re.IGNORECASE)
    if match:
        entities["Profil"] = match.group(2).strip()

    # Formation
    match = re.search(r"(formation|education)\s*[:\-\n]?\s*(.*?)(expérience|experience|skills|compétences)", text, re.IGNORECASE | re.DOTALL)
    if match:
        entities["Formation"] = match.group(2).strip().replace("\n", " ")

    # Expérience
    match = re.search(r"(expérience|experience)\s*[:\-\n]?\s*(.*?)(formation|education|skills|compétences)", text, re.IGNORECASE | re.DOTALL)
    if match:
        entities["Expérience"] = match.group(2).strip().replace("\n", " ")

    # Langues
    langues = []
    for lang in ["français", "anglais", "espagnol", "arabe"]:
        if lang in text.lower():
            langues.append(lang.capitalize())
    entities["Langues"] = ", ".join(langues)

    # Compétences
    found_skills = set()
    for word in text.split():
        close = get_close_matches(word, skills_list, n=1, cutoff=0.8)
        if close:
            found_skills.add(close[0])
    entities["Compétences"] = ", ".join(sorted(found_skills))

    return entities

st.title("📄 Analyse de CV (version légère sans spaCy)")
st.markdown("Déposez un ou plusieurs CVs au format PDF/Image. Le système analysera automatiquement les informations principales.")

uploaded_files = st.file_uploader("📤 Déposer vos fichiers", type=["pdf", "png", "jpg", "jpeg"], accept_multiple_files=True)

if uploaded_files:
    all_entities = []
    for file in uploaded_files:
        with st.spinner(f"Analyse de {file.name}..."):
            text = extract_text_from_pdf(file)
            data = extract_entities(text)
            all_entities.append(data)

    df = pd.DataFrame(all_entities)
    st.success("✅ Extraction terminée !")
    st.dataframe(df)

    excel_file = BytesIO()
    with pd.ExcelWriter(excel_file, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    st.download_button("⬇️ Télécharger en Excel", data=excel_file.getvalue(), file_name="cv_extraits.xlsx")
