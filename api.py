from utils import fetch_articles, analyze_sentiment, extract_keywords, extract_relevant_entities, is_english, generate_tts
from collections import Counter
import json


def get_sentiment_report(company_name, num_articles):
    """
    Fetches articles, analyzes sentiment, generates a sentiment report, and creates a Text-to-Speech (TTS) file.
    
    Args:
        company_name (str): The company name for which to fetch articles.
        num_articles (int): The number of articles to fetch and analyze.
    
    Returns:
        tuple: A tuple containing the sentiment report (str) and TTS filename (str).
    """
    articles = fetch_articles(company_name)
    counter = 0
    
    if len(articles) == 0:
        return "No articles found.", "error"

    sentiment_report = ""
    sentiment_distribution = {"Positive": 0, "Negative": 0, "Neutral": 0}
    all_keywords = []
    all_articles_sentiment = []
    all_topics = []

    # Process each article
    for article in articles:
        if counter >= num_articles:  # Limit to user-defined number of articles
            break
        title = article.get("title", "No title")
        summary = article.get("description", "No summary available")
        
        if not summary or not is_english(summary):
            continue  # Skip invalid or non-English summaries
        
        # Extract keywords and entities
        keywords = extract_keywords(summary)
        entities = extract_relevant_entities(summary)
        combined_keywords = list(set(keywords + entities))
        all_keywords.extend(combined_keywords)
        
        # Perform sentiment analysis
        sentiment_score = analyze_sentiment(summary)
        sentiment = "Positive" if sentiment_score > 0 else "Negative" if sentiment_score < 0 else "Neutral"
        sentiment_distribution[sentiment] += 1
        
        # Format the article data into a more readable format
        sentiment_report += f"**Title**: {title}\n" + "\n"
        sentiment_report += f"**Summary**: {summary}\n" + "\n"
        sentiment_report += f"**Sentiment**: {sentiment}\n" + "\n"
        sentiment_report += f"**Keywords**: {','.join(combined_keywords)}" + "\n"
        sentiment_report += "\n"
        sentiment_report += "-" * 50 + "\n"

        # Collect all topics and sentiments from the articles
        all_topics.append(combined_keywords)
        all_articles_sentiment.append(sentiment)
        counter += 1

    # Generate Topic Overlap
    all_keywords_count = Counter(all_keywords)
    common_topics = [k for k, v in all_keywords_count.items() if v > 1]
    unique_topics = [k for k, v in all_keywords_count.items() if v == 1]

    # Generate coverage differences with dynamic impact messages
    coverage_differences = generate_coverage_differences(all_topics, company_name)

    # Generate Final Sentiment Analysis sentence
    final_sentiment = determine_final_sentiment(sentiment_distribution)
    final_sentiment_sentence = f"Based on the analysis of the articles, the news coverage of {company_name} is mostly {final_sentiment.lower()}. There is a balanced sentiment coverage with mixed perspectives."

    # Combine all information for final report
    sentiment_report += "\nComparative Sentiment Score:" + "\n"
    sentiment_report += f"\nSentiment Distribution: {sentiment_distribution}" + "\n"
    sentiment_report += "\n"
    sentiment_report += "-" * 50 + "\n"
    sentiment_report += "\n"

    # Add coverage differences to the report
    sentiment_report +="\n"
    sentiment_report += "\nCoverage Differences:"+"\n"
    for diff in coverage_differences:
        sentiment_report += "\n"
        sentiment_report += "  ----------------------------\n"+ "\n"
        sentiment_report += "\n"
        sentiment_report += f"  **Comparison**: {diff['Comparison']}\n"
        sentiment_report += "\n"
        sentiment_report += f"  **Impact**: {diff['Impact']}\n"
        sentiment_report += "\n"
        sentiment_report += "  ----------------------------\n\n"

    # Formatting Topic Overlap
    sentiment_report += "-" * 10 + "\n"
    sentiment_report += "\nTopic Overlap:" + "\n"
    sentiment_report += f"\nCommon Topics: {', '.join(common_topics)}" + "\n"
    sentiment_report += f"\nUnique Topics in All Articles: {', '.join(unique_topics)}" + "\n"
    sentiment_report += "\n"
    sentiment_report += "-" * 10 + "\n"

    sentiment_report += f"**Final Sentiment Analysis**: {final_sentiment_sentence}\n"
    
    # Generate TTS from the sentiment report
    tts_filename = generate_tts(final_sentiment_sentence)

    return sentiment_report, tts_filename


def generate_coverage_differences(all_topics, company_name):
    """
    Generates the coverage differences between consecutive articles, with dynamic impact messages based on topics.
    
    Args:
        all_topics (list): List of topics extracted from the articles.
        company_name (str): The company name being analyzed.
    
    Returns:
        list: A list of coverage difference dictionaries.
    """
    coverage_differences = []
    for i in range(1, len(all_topics)):
        difference = set(all_topics[i]) - set(all_topics[i - 1])
        if difference:
            impact_message = ""

            # Check for legal/regulatory topics
            if any(keyword in difference for keyword in ["regulation", "lawsuit", "compliance"]):
                impact_message = f"This article introduces legal/regulatory topics such as {', '.join(difference)} that could affect the company's regulatory landscape."

            # Check for financial topics
            elif any(keyword in difference for keyword in ["financial", "revenue", "profits", "growth", "stocks"]):
                impact_message = f"This article discusses the financial health of the company with topics like {', '.join(difference)}, which may impact investor sentiment."

            # Check for technology/innovation topics
            elif any(keyword in difference for keyword in ["technology", "innovation", "AI", "machine learning"]):
                impact_message = f"New technological advancements, including {', '.join(difference)}, have the potential to reshape the company's future growth trajectory."

            # Check for market share/competition topics
            elif any(keyword in difference for keyword in ["market share", "competitors", "competition"]):
                impact_message = f"This article highlights shifts in the competitive landscape, with topics like {', '.join(difference)} that could change the company's market position."

            # Check for product launches or developments
            elif any(keyword in difference for keyword in ["launch", "product", "release", "update"]):
                impact_message = f"The article introduces new product developments or launches such as {', '.join(difference)}, which may reshape {company_name}'s market strategy."

            # Check for management or leadership changes
            elif any(keyword in difference for keyword in ["CEO", "leadership", "management", "board"]):
                impact_message = f"Management changes, including topics like {', '.join(difference)}, might influence the company's strategic direction."

            # Default impact message
            else:
                impact_message = f"Article introduces new perspectives on the company's coverage, adding topics such as {', '.join(difference)}."

            coverage_differences.append({
                "Comparison": f"Article {i} introduces topics {', '.join(difference)} which are not in Article {i-1}",
                "Impact": impact_message
            })

    return coverage_differences


def determine_final_sentiment(sentiment_distribution):
    """
    Determines the final sentiment (Positive, Negative, Neutral) based on sentiment distribution.
    
    Args:
        sentiment_distribution (dict): A dictionary containing sentiment counts (Positive, Negative, Neutral).
    
    Returns:
        str: The final sentiment ("Positive", "Negative", or "Neutral").
    """
    if sentiment_distribution["Positive"] > sentiment_distribution["Negative"] and sentiment_distribution["Positive"] > sentiment_distribution["Neutral"]:
        return "Positive"
    elif sentiment_distribution["Negative"] > sentiment_distribution["Positive"] and sentiment_distribution["Negative"] > sentiment_distribution["Neutral"]:
        return "Negative"
    else:
        return "Neutral"
