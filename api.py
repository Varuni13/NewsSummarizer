from utils import (
    fetch_articles, get_full_sentiment_scores,
    extract_keywords, extract_relevant_entities, is_english, generate_tts
)
from collections import Counter

# Risk signal keyword sets
_NEGATIVE_RISK_KEYWORDS = {
    "lawsuit", "regulation", "fine", "loss", "decline", "investigation",
    "fraud", "scandal", "crisis", "ban", "penalty", "compliance", "breach",
    "recall", "shortage", "layoff", "bankruptcy", "hack", "data leak"
}
_LEGAL_FINANCIAL_KEYWORDS = {
    "lawsuit", "regulation", "compliance", "fine", "penalty", "investigation",
    "revenue", "profits", "loss", "growth", "stocks", "earnings", "decline", "debt"
}


def compute_risk_score(sentiment_distribution, all_keywords):
    """
    Computes a 0–100 risk score and returns both the score and a breakdown dict.

    Weights:
      50% → % negative articles
      30% → presence of negative/risk keywords (capped at 10)
      20% → legal/financial keyword density (capped at 10)

    Returns:
        tuple: (score: int, breakdown: dict)
    """
    total = sum(sentiment_distribution.values()) or 1
    neg_pct = (sentiment_distribution["Negative"] / total) * 100

    neg_kw_matches = [k for k in all_keywords if any(b in k.lower() for b in _NEGATIVE_RISK_KEYWORDS)]
    neg_kw_count = len(neg_kw_matches)
    neg_kw_ratio = min(neg_kw_count / 10, 1) * 100

    lf_matches = [k for k in all_keywords if any(lf in k.lower() for lf in _LEGAL_FINANCIAL_KEYWORDS)]
    lf_count = len(lf_matches)
    lf_ratio = min(lf_count / 10, 1) * 100

    score = min(int(neg_pct * 0.5 + neg_kw_ratio * 0.3 + lf_ratio * 0.2), 100)

    breakdown = {
        "neg_article_pct": round(neg_pct, 1),
        "neg_keyword_count": neg_kw_count,
        "neg_keyword_matches": list(set(neg_kw_matches))[:8],
        "legal_financial_count": lf_count,
        "legal_financial_matches": list(set(lf_matches))[:8],
    }
    return score, breakdown


def compute_trend(articles):
    """
    Compares average sentiment of the first half vs second half of articles.

    Returns:
        tuple: (direction: str, delta: float)
            direction is one of "Improving", "Worsening", "Stable"
    """
    scores = [a["sentiment_score"] for a in articles]
    if len(scores) < 2:
        return "Stable", 0.0

    mid = max(len(scores) // 2, 1)
    first_avg = sum(scores[:mid]) / mid
    second_avg = sum(scores[mid:]) / (len(scores) - mid)
    delta = round(second_avg - first_avg, 3)

    if delta > 0.08:
        return "Improving", delta
    if delta < -0.08:
        return "Worsening", delta
    return "Stable", delta


def generate_coverage_differences(all_topics, company_name):
    coverage_differences = []
    for i in range(1, len(all_topics)):
        difference = set(all_topics[i]) - set(all_topics[i - 1])
        if not difference:
            continue

        if any(k in difference for k in ["regulation", "lawsuit", "compliance"]):
            impact = f"Legal/regulatory topics — {', '.join(difference)} — could affect the regulatory landscape."
        elif any(k in difference for k in ["financial", "revenue", "profits", "growth", "stocks"]):
            impact = f"Financial topics — {', '.join(difference)} — may impact investor sentiment."
        elif any(k in difference for k in ["technology", "innovation", "AI", "machine learning"]):
            impact = f"Tech advancements — {', '.join(difference)} — potential to reshape growth trajectory."
        elif any(k in difference for k in ["market share", "competitors", "competition"]):
            impact = f"Competitive shifts — {', '.join(difference)} — may change {company_name}'s market position."
        elif any(k in difference for k in ["launch", "product", "release", "update"]):
            impact = f"Product developments — {', '.join(difference)} — may reshape market strategy."
        elif any(k in difference for k in ["CEO", "leadership", "management", "board"]):
            impact = f"Leadership changes — {', '.join(difference)} — may influence strategic direction."
        else:
            impact = f"New perspectives — {', '.join(difference)} — adds to coverage diversity."

        coverage_differences.append({
            "Comparison": f"Article {i + 1} introduces: {', '.join(difference)} (not in Article {i})",
            "Impact": impact
        })
    return coverage_differences


def get_sentiment_data(company_name, num_articles, from_date=None):
    """
    Fetches news articles, runs NLP analysis, and returns a structured data dict.

    Returns:
        dict with keys:
            articles, sentiment_distribution, keyword_freq, common_topics,
            unique_topics, coverage_differences, final_sentiment,
            final_sentiment_sentence, risk_score, risk_score_breakdown,
            source_breakdown, trend_direction, trend_delta,
            total_articles_found, tts_filename, error
    """
    articles_raw, total_found = fetch_articles(company_name, from_date)

    if not articles_raw:
        return {"error": "No articles found. Check your API key or try a different date range."}

    articles = []
    sentiment_distribution = {"Positive": 0, "Negative": 0, "Neutral": 0}
    all_keywords = []
    all_topics = []
    source_breakdown = {}
    counter = 0

    for article in articles_raw:
        if counter >= num_articles:
            break

        title = article.get("title") or "No title"
        summary = article.get("description") or ""
        source = article.get("source", {}).get("name") or "Unknown"
        published_at = article.get("publishedAt") or ""

        if not summary or not is_english(summary):
            continue

        keywords = extract_keywords(summary)
        entities = extract_relevant_entities(summary)
        combined_keywords = list(set(keywords + entities))
        all_keywords.extend(combined_keywords)

        vader = get_full_sentiment_scores(summary)
        compound = vader["compound"]

        if compound > 0:
            sentiment = "Positive"
        elif compound < 0:
            sentiment = "Negative"
        else:
            sentiment = "Neutral"

        sentiment_distribution[sentiment] += 1

        if source not in source_breakdown:
            source_breakdown[source] = {"Positive": 0, "Negative": 0, "Neutral": 0}
        source_breakdown[source][sentiment] += 1

        # Confidence band: width driven by neutral score (more neutral = more uncertain)
        band_half = round(vader["neu"] * 0.4, 4)

        articles.append({
            "title": title,
            "summary": summary,
            "sentiment": sentiment,
            "sentiment_score": compound,
            "sentiment_upper": round(min(compound + band_half, 1.0), 4),
            "sentiment_lower": round(max(compound - band_half, -1.0), 4),
            "keywords": combined_keywords,
            "source": source,
            "published_at": published_at
        })
        all_topics.append(combined_keywords)
        counter += 1

    if not articles:
        return {"error": "No valid English articles found for this query and date range."}

    kw_counter = Counter(all_keywords)
    common_topics = [k for k, v in kw_counter.items() if v > 1]
    unique_topics = [k for k, v in kw_counter.items() if v == 1]

    coverage_differences = generate_coverage_differences(all_topics, company_name)

    pos = sentiment_distribution["Positive"]
    neg = sentiment_distribution["Negative"]
    neu = sentiment_distribution["Neutral"]
    if pos > neg and pos > neu:
        final_sentiment = "Positive"
    elif neg > pos and neg > neu:
        final_sentiment = "Negative"
    else:
        final_sentiment = "Neutral"

    total = len(articles)
    final_sentence = (
        f"Based on {total} article{'s' if total != 1 else ''}, news coverage of {company_name} "
        f"is mostly {final_sentiment.lower()}. "
        f"{'A balanced mix of perspectives was observed.' if final_sentiment == 'Neutral' else f'The coverage leans predominantly {final_sentiment.lower()}.'}"
    )

    risk_score, risk_breakdown = compute_risk_score(sentiment_distribution, all_keywords)
    trend_direction, trend_delta = compute_trend(articles)
    tts_filename = generate_tts(final_sentence)

    return {
        "articles": articles,
        "sentiment_distribution": sentiment_distribution,
        "keyword_freq": dict(kw_counter),
        "common_topics": common_topics,
        "unique_topics": unique_topics,
        "coverage_differences": coverage_differences,
        "final_sentiment": final_sentiment,
        "final_sentiment_sentence": final_sentence,
        "risk_score": risk_score,
        "risk_score_breakdown": risk_breakdown,
        "source_breakdown": source_breakdown,
        "trend_direction": trend_direction,
        "trend_delta": trend_delta,
        "total_articles_found": total_found,
        "tts_filename": tts_filename,
        "error": None
    }
