import requests
import spacy
import re
from rake_nltk import Rake
from nltk.corpus import stopwords
from langdetect import detect  # For language detection
from gtts import gTTS  # For Text-to-Speech (TTS) functionality
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from collections import Counter
from googletrans import Translator
import os
import nltk
from dotenv import load_dotenv

load_dotenv()  # loads API_KEY from .env into os.environ

# Also support Streamlit Cloud secrets (st.secrets["API_KEY"])
try:
    import streamlit as st
    if "API_KEY" in st.secrets:
        os.environ["API_KEY"] = st.secrets["API_KEY"]
except Exception:
    pass

# Auto-download required NLTK data on first run
for _pkg in ("stopwords", "vader_lexicon", "punkt", "punkt_tab"):
    nltk.download(_pkg, quiet=True)

# Initialize RAKE, SpaCy, and SentimentIntensityAnalyzer (VADER)
rake = Rake()
nlp = spacy.load("en_core_web_sm")
sid = SentimentIntensityAnalyzer()


def filter_keywords(keywords, doc):
    """
    Filters out keywords based on length, stop words, and part of speech (POS).
    Only non-stop words that are not verbs and have a length greater than 2 are retained.
    
    Args:
        keywords (list): List of keywords extracted from text.
        doc (spaCy Doc): A spaCy Doc object representing the text.
    
    Returns:
        list: Filtered keywords.
    """
    filtered_keywords = set()
    stop_words = set(stopwords.words("english"))
    number_pattern = r'\d+|[a-zA-Z]+\d+[a-zA-Z]*'

    for word in keywords:
        if len(word) <= 2 or re.search(number_pattern, word):
            continue
        
        token = next((t for t in doc if t.text == word), None)
        if token is None:
            continue
        
        if token.pos_ == 'VERB':
            continue
        
        if word.lower() not in stop_words:
            filtered_keywords.add(word.lower())
    
    return list(filtered_keywords)


def extract_keywords(text):
    """
    Extracts keywords from the input text using RAKE and filters them using spaCy.
    
    Args:
        text (str): The text from which to extract keywords.
    
    Returns:
        list: A list of filtered keywords.
    """
    rake.extract_keywords_from_text(text)
    keywords = rake.get_ranked_phrases()
    doc = nlp(text)
    return filter_keywords(keywords, doc)


def extract_relevant_entities(text):
    """
    Extracts relevant entities (such as organizations, products, and events) from the input text.
    
    Args:
        text (str): The text from which to extract entities.
    
    Returns:
        list: A list of relevant entities extracted from the text.
    """
    doc = nlp(text)
    relevant_entities = []
    
    for entity in doc.ents:
        if entity.label_ in ['ORG', 'PRODUCT', 'EVENT']:
            relevant_entities.append(entity.text)
    
    return relevant_entities


def is_english(text):
    """
    Detects if the input text is in English using the langdetect library.
    
    Args:
        text (str): The text to be checked for language.
    
    Returns:
        bool: True if the text is in English, otherwise False.
    """
    try:
        return detect(text) == 'en'
    except:
        return False


def analyze_sentiment(text):
    """
    Returns the VADER compound score for the text (-1 to +1).
    """
    return sid.polarity_scores(text)['compound']


def get_full_sentiment_scores(text):
    """
    Returns all four VADER scores for the text.

    Returns:
        dict: {compound, pos, neg, neu}
    """
    scores = sid.polarity_scores(text)
    return {
        "compound": round(scores["compound"], 4),
        "pos":      round(scores["pos"], 4),
        "neg":      round(scores["neg"], 4),
        "neu":      round(scores["neu"], 4),
    }


def fetch_articles(company_name, from_date=None):
    """
    Fetches articles related to the company from NewsAPI.

    Args:
        company_name (str): Company name to search for.
        from_date (str, optional): ISO date string (YYYY-MM-DD) lower bound.

    Returns:
        tuple: (articles: list, total_results: int)
    """
    API_KEY = os.getenv("API_KEY")
    url = f"https://newsapi.org/v2/everything?q={company_name}&apiKey={API_KEY}"
    if from_date:
        url += f"&from={from_date}"

    try:
        response = requests.get(url, timeout=10)
        data = response.json()
        return data.get("articles", []), data.get("totalResults", 0)
    except Exception:
        return [], 0


def generate_tts(text, filename="summary_hindi.mp3"):
    """
    Converts the input text to speech in Hindi and saves it to a file.
    Returns "error" string if translation or TTS generation fails.

    Args:
        text (str): The text to be converted to speech.
        filename (str): The name of the file to save the TTS audio. Default is "summary_hindi.mp3".

    Returns:
        str: The filename of the saved TTS audio, or "error" on failure.
    """
    try:
        translator = Translator()
        translated_text = translator.translate(text, src='en', dest='hi').text
        tts = gTTS(text=translated_text, lang='hi', slow=False)
        tts.save(filename)
        return filename
    except Exception:
        return "error"
