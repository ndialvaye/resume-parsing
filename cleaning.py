import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet
from nltk.stem import WordNetLemmatizer

nltk.download('punkt')
nltk.download('wordnet')

def clean_text(text):
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-zA-Z0-9,.:;()\-\s]', '', text)
    return text.strip()

def normalize_text(text):
    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()
    normalized = [lemmatizer.lemmatize(token.lower()) for token in tokens]
    return ' '.join(normalized)