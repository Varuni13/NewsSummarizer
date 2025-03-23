# News Summarization and Sentiment Analysis with Text-to-Speech

This is a **News Summarization and Sentiment Analysis** web application developed using **Streamlit**, **Hugging Face**, and **Google Text-to-Speech (gTTS)** API. The app allows users to input news articles, analyze their sentiment, and get a summarized version. The summary can also be converted into speech.

### Created by: [Varuni Singh](https://github.com/Varuni13)

## Key Sections

1. [Introduction](#introduction)
2. [Technologies Used](#technologies-used)
3. [Installation Instructions](#installation-instructions)
4. [Usage](#usage)
5. [Deployment](#deployment)
6. [How It Works](#how-it-works)
7. [Troubleshooting](#troubleshooting)
8. [Contributing](#contributing)
9. [License](#license)

## Introduction

This web app allows you to **summarize news articles**, perform **sentiment analysis**, and convert the summarized text into **speech** using **Streamlit** and other NLP models.

## Features

- **Text Summarization**: Extracts the key points and provides a concise version of the news article.
- **Sentiment Analysis**: Analyzes the sentiment of the article (Positive, Negative, Neutral).
- **Text-to-Speech**: Converts the summarized news into speech.

## Technologies Used

- **Streamlit**: For creating interactive web applications.
- **Hugging Face Transformers**: For natural language processing tasks like summarization and sentiment analysis.
- **gTTS (Google Text-to-Speech)**: For converting text to speech.
- **Python**: Backend programming.
- **Docker**: For containerizing the application.
- **GitHub**: For version control and collaboration.
- **Hugging Face Spaces**: For deploying the app in a cloud environment.

## Installation Instructions

### 1. Clone the Repository

Clone the project to your local machine using Git:

```bash
git clone https://github.com/Varuni13/text-to-speech-news-summarizer.git
cd text-to-speech-news-summarizer
```
2. Create a Virtual Environment
It's recommended to create a virtual environment to keep your dependencies isolated:

Windows
```bash
Copy
python -m venv venv
.\venv\Scripts\activate
```
Linux/macOS
```bash
Copy
python3 -m venv venv
source venv/bin/activate
```
3. Install Dependencies
Install all required dependencies from the requirements.txt file:

``` bash
Copy
pip install -r requirements.txt
```
4. Run the Application Locally
To run the application on your local machine:

```bash
Copy
streamlit run app.py
```
This will start a local web server, and the app will be accessible at http://localhost:8501 in your browser.

## Usage
1. Input News Article: In the text box provided, enter the news article you want to summarize.

2. Get Summary: The application will automatically generate a summary of the article.

3. Analyze Sentiment: The sentiment of the article will be displayed (Positive, Negative, or Neutral).

4. Text-to-Speech: You can listen to the summary by clicking the "Convert to Speech" button.

## Deployment
The app has been deployed on both GitHub and Hugging Face Spaces. You can access the live web application at the following URL:

- Hugging Face Space: News Summarizer - Live

## How It Works
1. Summarization:

- The app uses Hugging Face's pre-trained summarization models to extract the most important points from the input news article.

2. Sentiment Analysis:

- It uses Hugging Face's pre-trained sentiment analysis model to determine the tone of the article (positive, negative, or neutral).

3. Text-to-Speech (TTS):

- The summarized text is passed through the Google Text-to-Speech (gTTS) API to convert the summary into speech, which is then played back to the user.

## Troubleshooting
- Error: "ModuleNotFoundError": If you encounter a ModuleNotFoundError, make sure all required libraries are installed using pip install -r requirements.txt.

- Port Conflict: If streamlit run gives an error saying that port 8501 is in use, you can specify a different port like so:

``` bash
Copy
streamlit run app.py --server.port 8502
```
- Google Translate API Issues: If you're seeing errors related to the googletrans package, try installing the correct version:

```bash
Copy
pip install googletrans==4.0.0-rc1
```
## Contributing
If you would like to contribute to this project, feel free to fork the repository and create a pull request with your changes.

## License
This project is licensed under the MIT License - see the LICENSE file for details.


