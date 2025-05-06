import os
import pandas as pd
from cleaning import clean_text, normalize_text

input_folder = "uploads"
output_path = "resultats_cv_nettoyes.xlsx"

data = []

for filename in os.listdir(input_folder):
    if filename.endswith(".txt") or filename.endswith(".pdf"):
        with open(os.path.join(input_folder, filename), 'r', encoding='utf-8') as f:
            raw_text = f.read()
            cleaned = clean_text(raw_text)
            normalized = normalize_text(cleaned)
            data.append({
                "Nom du fichier": filename,
                "Texte brut": raw_text,
                "Texte nettoyé": cleaned,
                "Texte normalisé": normalized
            })

df = pd.DataFrame(data)
df.to_excel(output_path, index=False)
print(f"✔️ Fichier Excel généré : {output_path}")