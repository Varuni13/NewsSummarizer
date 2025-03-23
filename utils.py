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
    Analyzes the sentiment of the input text using VADER sentiment analysis.
    
    Args:
        text (str): The text for sentiment analysis.
    
    Returns:
        float: The sentiment score of the text. Positive for positive sentiment, negative for negative, and neutral.
    """
    sentiment_score = sid.polarity_scores(text)
    return sentiment_score['compound']


def fetch_articles(company_name):
    """
    Fetches articles related to the company from NewsAPI using an API key.
    
    Args:
        company_name (str): The name of the company to search articles for.
    
    Returns:
        list: A list of articles related to the company.
    """
    API_KEY = os.getenv("API_KEY")
    url = f"https://newsapi.org/v2/everything?q={company_name}&apiKey={API_KEY}"

    response = requests.get(url)
    articles = response.json().get("articles", [])
    return articles


def generate_tts(text, filename="summary_hindi.mp3"):
    """
    Converts the input text to speech in Hindi and saves it to a file.
    
    Args:
        text (str): The text to be converted to speech.
        filename (str): The name of the file to save the TTS audio. Default is "summary_hindi.mp3".
    
    Returns:
        str: The filename of the saved TTS audio.
    """
    # Translate the summary into Hindi using Google Translate
    translator = Translator()
    translated_text = translator.translate(text, src='en', dest='hi').text

    # Convert the translated Hindi text to speech
    tts = gTTS(text=translated_text, lang='hi', slow=False)
    tts.save(filename)

    # Return the filename for later use
    return filename
