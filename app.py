import streamlit as st
import altair as alt
import pandas as pd
from datetime import datetime, timedelta
from api import get_sentiment_data

st.set_page_config(
    page_title="News Intelligence Dashboard",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp { background-color: #1a1f2e; }
    .stButton>button {
        background-color: #FF5E57;
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    .stButton>button:hover { background-color: #e04e47; }
    .stTabs [data-baseweb="tab"] { color: #aaa; }
    .stTabs [aria-selected="true"] { color: white; }
    div[data-testid="metric-container"] {
        background: #2E3B4E;
        border-radius: 10px;
        padding: 12px;
    }
    .alert-box {
        background: #4a2020;
        border-left: 4px solid #ff4444;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 12px;
    }
    .verdict-box {
        background: #1e2d3d;
        border-left: 4px solid #4A9EFF;
        border-radius: 6px;
        padding: 12px 16px;
        margin-bottom: 12px;
    }
    .signal-box {
        padding: 12px 16px;
        border-radius: 8px;
        color: white;
        font-weight: bold;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

COMPANIES = [
    "Apple", "Amazon", "Tesla", "Microsoft", "Google",
    "Facebook (Meta)", "Netflix", "Samsung", "IBM"
]

SENTIMENT_COLORS = {
    "Positive": "#00C851",
    "Negative": "#ff4444",
    "Neutral":  "#ffbb33"
}


# ──────────────────────────────────────────────
# Helper renderers
# ──────────────────────────────────────────────

def sentiment_badge(sentiment):
    c = SENTIMENT_COLORS.get(sentiment, "#999")
    return (
        f'<span style="background:{c};color:white;padding:3px 10px;'
        f'border-radius:12px;font-size:12px;font-weight:bold">{sentiment}</span>'
    )


def risk_meta(score):
    if score < 33:
        return "#00C851", "Low Risk"
    if score < 66:
        return "#ffbb33", "Medium Risk"
    return "#ff4444", "High Risk"


def coverage_signal(common, unique):
    total = len(common) + len(unique) + 1
    pct = len(common) / total * 100
    if pct > 60:
        return "#c0392b", "Focused Coverage — articles converge on a single event or topic"
    if pct > 30:
        return "#d68910", "Mixed Coverage — some consensus with diverse angles"
    return "#1e8449", "Scattered Coverage — diverse topics, no dominant narrative"


# ──────────────────────────────────────────────
# Section renderers
# ──────────────────────────────────────────────

def render_overview(data, company_name):
    dist = data["sentiment_distribution"]
    total = sum(dist.values()) or 1
    score = data["risk_score"]
    risk_color, risk_label = risk_meta(score)

    # Trend arrow
    trend = data.get("trend_direction", "Stable")
    trend_arrow = {"Improving": "↑ Improving", "Worsening": "↓ Worsening", "Stable": "→ Stable"}[trend]
    trend_color = {"Improving": "#00C851", "Worsening": "#ff4444", "Stable": "#ffbb33"}[trend]

    # Volume
    total_found = data.get("total_articles_found", 0)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Risk Score", f"{score} / 100", delta=risk_label,
              delta_color="inverse" if score >= 33 else "normal")
    c2.metric("Analyzed", f"{total} of {total_found}")
    c3.metric("Positive",  f"{dist['Positive'] * 100 // total}%")
    c4.metric("Negative",  f"{dist['Negative'] * 100 // total}%")
    c5.metric("Neutral",   f"{dist['Neutral']  * 100 // total}%")
    c6.metric("Trend", trend_arrow)

    # Verdict
    st.markdown(
        f'<div class="verdict-box">📌 <strong>Verdict</strong>: {data["final_sentiment_sentence"]} '
        f'<span style="color:{trend_color};font-weight:bold">{trend_arrow}</span></div>',
        unsafe_allow_html=True
    )

    # Risk score breakdown
    bd = data.get("risk_score_breakdown", {})
    with st.expander("Risk Score Breakdown", expanded=False):
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Negative Articles", f"{bd.get('neg_article_pct', 0)}%",
                     help="Contributes 50% of the risk score")
        col_b.metric("Risk Keywords Found", bd.get('neg_keyword_count', 0),
                     help="Contributes 30% of the risk score")
        col_c.metric("Legal/Financial Keywords", bd.get('legal_financial_count', 0),
                     help="Contributes 20% of the risk score")

        if bd.get("neg_keyword_matches"):
            st.markdown(
                "**Risk keywords detected**: " +
                " ".join([f'`{k}`' for k in bd["neg_keyword_matches"]])
            )
        if bd.get("legal_financial_matches"):
            st.markdown(
                "**Legal/financial keywords**: " +
                " ".join([f'`{k}`' for k in bd["legal_financial_matches"]])
            )


def render_charts(data):
    dist = data["sentiment_distribution"]
    articles = data["articles"]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Sentiment Distribution")
        df_dist = pd.DataFrame({
            "Sentiment": list(dist.keys()),
            "Count": list(dist.values())
        })
        donut = (
            alt.Chart(df_dist)
            .mark_arc(innerRadius=60, outerRadius=120)
            .encode(
                theta=alt.Theta("Count:Q"),
                color=alt.Color(
                    "Sentiment:N",
                    scale=alt.Scale(
                        domain=["Positive", "Negative", "Neutral"],
                        range=["#00C851", "#ff4444", "#ffbb33"]
                    )
                ),
                tooltip=["Sentiment:N", "Count:Q"]
            )
            .properties(height=300)
        )
        st.altair_chart(donut, use_container_width=True)

    with col2:
        st.subheader("Sentiment Timeline")

        def _date_label(a, i):
            raw = a.get("published_at", "")
            return raw[:10] if raw else f"#{i + 1}"

        df_tl = pd.DataFrame([{
            "Label": _date_label(a, i),
            "Score": a["sentiment_score"],
            "Upper": a.get("sentiment_upper", a["sentiment_score"]),
            "Lower": a.get("sentiment_lower", a["sentiment_score"]),
            "Sentiment": a["sentiment"],
            "Title": (a["title"][:55] + "…") if len(a["title"]) > 55 else a["title"]
        } for i, a in enumerate(articles)])

        x_enc = alt.X("Label:N", title="Date / Article",
                      sort=None, axis=alt.Axis(labelAngle=-35))
        y_enc = alt.Y("Score:Q", scale=alt.Scale(domain=[-1, 1]), title="VADER Score")

        zero = (
            alt.Chart(pd.DataFrame({"y": [0]}))
            .mark_rule(strokeDash=[5, 5], color="#555", strokeWidth=1)
            .encode(y="y:Q")
        )
        band = (
            alt.Chart(df_tl)
            .mark_area(opacity=0.15, color="#4A9EFF")
            .encode(x=x_enc, y="Upper:Q", y2="Lower:Q")
        )
        line = (
            alt.Chart(df_tl)
            .mark_line(strokeWidth=2, color="#4A9EFF")
            .encode(x=x_enc, y=y_enc)
        )
        points = (
            alt.Chart(df_tl)
            .mark_point(size=90, filled=True)
            .encode(
                x=x_enc,
                y=y_enc,
                color=alt.Color(
                    "Sentiment:N",
                    scale=alt.Scale(
                        domain=["Positive", "Negative", "Neutral"],
                        range=["#00C851", "#ff4444", "#ffbb33"]
                    )
                ),
                tooltip=["Label:N", "Title:N", "Score:Q", "Sentiment:N"]
            )
        )
        st.altair_chart(
            (zero + band + line + points).properties(height=300),
            use_container_width=True
        )


def render_articles(data):
    st.subheader("Article-Level Analysis")
    for i, article in enumerate(data["articles"]):
        with st.expander(f"#{i + 1} — {article['title']}", expanded=False):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.write(article["summary"])
                pills = " ".join([f"`{k}`" for k in article["keywords"][:10]])
                st.markdown(f"**Keywords**: {pills or '_none extracted_'}")
            with col_b:
                st.markdown(sentiment_badge(article["sentiment"]), unsafe_allow_html=True)
                st.write(f"Score: `{article['sentiment_score']}`")
                st.write(f"Source: *{article['source']}*")
                if article.get("published_at"):
                    st.caption(article["published_at"][:10])


_ALL_RISK_KEYWORDS = {
    "lawsuit", "regulation", "fine", "loss", "decline", "investigation",
    "fraud", "scandal", "crisis", "ban", "penalty", "compliance", "breach",
    "recall", "shortage", "layoff", "bankruptcy", "hack", "data leak",
    "revenue", "profits", "earnings", "debt", "stocks"
}


def render_keywords(data):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top Keywords")
        st.caption("Red bars = risk/financial signal keywords")
        kf = data["keyword_freq"]
        if kf:
            top = sorted(kf.items(), key=lambda x: x[1], reverse=True)[:15]
            df_kw = pd.DataFrame(top, columns=["Keyword", "Frequency"])
            df_kw["Type"] = df_kw["Keyword"].apply(
                lambda k: "Risk" if any(r in k.lower() for r in _ALL_RISK_KEYWORDS) else "Normal"
            )
            bar = (
                alt.Chart(df_kw)
                .mark_bar()
                .encode(
                    x=alt.X("Frequency:Q"),
                    y=alt.Y("Keyword:N", sort="-x"),
                    color=alt.Color(
                        "Type:N",
                        scale=alt.Scale(
                            domain=["Risk", "Normal"],
                            range=["#ff4444", "#4A9EFF"]
                        ),
                        legend=alt.Legend(title="Keyword Type")
                    ),
                    tooltip=["Keyword:N", "Frequency:Q", "Type:N"]
                )
                .properties(height=420)
            )
            st.altair_chart(bar, use_container_width=True)
        else:
            st.info("No keywords extracted.")

    with col2:
        st.subheader("Coverage Signal")
        sig_color, sig_text = coverage_signal(data["common_topics"], data["unique_topics"])
        st.markdown(
            f'<div class="signal-box" style="background:{sig_color}">{sig_text}</div>',
            unsafe_allow_html=True
        )

        col_c, col_u = st.columns(2)
        with col_c:
            st.write("**Common Topics**")
            for t in data["common_topics"][:10]:
                st.write(f"• {t}")
            if not data["common_topics"]:
                st.caption("_None_")
        with col_u:
            st.write("**Unique Topics**")
            for t in data["unique_topics"][:10]:
                st.write(f"• {t}")
            if not data["unique_topics"]:
                st.caption("_None_")

        if data["coverage_differences"]:
            st.write("")
            st.subheader("Coverage Differences")
            for diff in data["coverage_differences"]:
                with st.expander(diff["Comparison"][:80] + ("…" if len(diff["Comparison"]) > 80 else "")):
                    st.write(diff["Impact"])


def render_sources(data):
    st.subheader("Publisher Sentiment Breakdown")
    rows = []
    for src, counts in data["source_breakdown"].items():
        for sentiment, count in counts.items():
            for _ in range(count):
                rows.append({"Source": src, "Sentiment": sentiment})

    if rows:
        df_src = pd.DataFrame(rows)
        chart = (
            alt.Chart(df_src)
            .mark_bar()
            .encode(
                x=alt.X("count():Q", title="Article Count"),
                y=alt.Y("Source:N", sort="-x"),
                color=alt.Color(
                    "Sentiment:N",
                    scale=alt.Scale(
                        domain=["Positive", "Negative", "Neutral"],
                        range=["#00C851", "#ff4444", "#ffbb33"]
                    )
                ),
                tooltip=["Source:N", "Sentiment:N", "count():Q"]
            )
            .properties(height=max(200, len(data["source_breakdown"]) * 45))
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No source data available.")


def render_tts(data):
    st.subheader("Audio Summary (Hindi)")
    if data["tts_filename"] and data["tts_filename"] != "error":
        st.audio(data["tts_filename"], format="audio/mp3")
        st.caption(f"*{data['final_sentiment_sentence']}*")
    else:
        st.warning("TTS generation failed — check your Google Translate connection.")


def render_export(data, company_name):
    st.subheader("Export Report")
    df = pd.DataFrame(data["articles"])
    df.insert(0, "company", company_name)
    cols = ["company", "title", "source", "published_at", "sentiment", "sentiment_score", "summary"]
    csv = df[cols].to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"{company_name.lower().replace(' ', '_')}_news_report.csv",
        mime="text/csv",
        use_container_width=True
    )


def render_full_dashboard(data, company_name):
    render_overview(data, company_name)
    st.divider()

    tab1, tab2, tab3, tab4 = st.tabs(["Charts", "Articles", "Keywords & Topics", "Sources"])
    with tab1:
        render_charts(data)
    with tab2:
        render_articles(data)
    with tab3:
        render_keywords(data)
    with tab4:
        render_sources(data)

    st.divider()
    col_tts, col_exp = st.columns(2)
    with col_tts:
        render_tts(data)
    with col_exp:
        render_export(data, company_name)


# ──────────────────────────────────────────────
# Comparison view (no nested tabs — works inside columns)
# ──────────────────────────────────────────────

def _mini_donut(dist, height=220):
    df = pd.DataFrame({"Sentiment": list(dist.keys()), "Count": list(dist.values())})
    return (
        alt.Chart(df)
        .mark_arc(innerRadius=40, outerRadius=90)
        .encode(
            theta=alt.Theta("Count:Q"),
            color=alt.Color(
                "Sentiment:N",
                scale=alt.Scale(
                    domain=["Positive", "Negative", "Neutral"],
                    range=["#00C851", "#ff4444", "#ffbb33"]
                )
            ),
            tooltip=["Sentiment:N", "Count:Q"]
        )
        .properties(height=height)
    )


def _mini_keyword_bar(kf, color, height=280):
    top = sorted(kf.items(), key=lambda x: x[1], reverse=True)[:10]
    df = pd.DataFrame(top, columns=["Keyword", "Frequency"])
    return (
        alt.Chart(df)
        .mark_bar(color=color)
        .encode(
            x=alt.X("Frequency:Q"),
            y=alt.Y("Keyword:N", sort="-x"),
            tooltip=["Keyword:N", "Frequency:Q"]
        )
        .properties(height=height)
    )


def render_comparison(data_a, company_a, data_b, company_b):
    # ── Top metrics ──
    st.subheader("Head-to-Head: Key Metrics")
    col_a, col_mid, col_b_col = st.columns([5, 1, 5])

    with col_a:
        st.markdown(f"### {company_a}")
        render_overview(data_a, company_a)
    with col_mid:
        st.markdown("<br><br><br><br><center>vs</center>", unsafe_allow_html=True)
    with col_b_col:
        st.markdown(f"### {company_b}")
        render_overview(data_b, company_b)

    st.divider()

    # ── Sentiment distributions ──
    st.subheader("Sentiment Distribution")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(company_a)
        st.altair_chart(_mini_donut(data_a["sentiment_distribution"]), use_container_width=True)
    with col2:
        st.caption(company_b)
        st.altair_chart(_mini_donut(data_b["sentiment_distribution"]), use_container_width=True)

    st.divider()

    # ── Risk score comparison ──
    st.subheader("Risk Score Comparison")
    def _risk_color(score):
        if score > 66:
            return "#ff4444"
        if score > 33:
            return "#ffbb33"
        return "#00C851"

    df_risk = pd.DataFrame({
        "Company": [company_a, company_b],
        "Risk Score": [data_a["risk_score"], data_b["risk_score"]],
        "Color": [_risk_color(data_a["risk_score"]), _risk_color(data_b["risk_score"])]
    })
    risk_chart = (
        alt.Chart(df_risk)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
        .encode(
            x=alt.X("Company:N", axis=alt.Axis(labelFontSize=13)),
            y=alt.Y("Risk Score:Q", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color("Color:N", scale=None, legend=None),
            tooltip=["Company:N", "Risk Score:Q"]
        )
        .properties(height=220)
    )
    st.altair_chart(risk_chart, use_container_width=True)

    st.divider()

    # ── Top keywords side by side ──
    st.subheader("Top Keywords")
    col1, col2 = st.columns(2)
    with col1:
        st.caption(company_a)
        if data_a["keyword_freq"]:
            st.altair_chart(_mini_keyword_bar(data_a["keyword_freq"], "#FF5E57"), use_container_width=True)
        else:
            st.info("No keywords.")
    with col2:
        st.caption(company_b)
        if data_b["keyword_freq"]:
            st.altair_chart(_mini_keyword_bar(data_b["keyword_freq"], "#4A9EFF"), use_container_width=True)
        else:
            st.info("No keywords.")

    st.divider()

    # ── Sentiment timelines side by side ──
    st.subheader("Sentiment Timelines")
    col1, col2 = st.columns(2)

    def _mini_timeline(articles, color_label):
        df = pd.DataFrame([{
            "Article": f"#{i + 1}",
            "Score": a["sentiment_score"],
            "Sentiment": a["sentiment"],
            "Title": (a["title"][:45] + "…") if len(a["title"]) > 45 else a["title"]
        } for i, a in enumerate(articles)])
        zero = (
            alt.Chart(pd.DataFrame({"y": [0]}))
            .mark_rule(strokeDash=[5, 5], color="#555", strokeWidth=1)
            .encode(y="y:Q")
        )
        line = (
            alt.Chart(df)
            .mark_line(strokeWidth=2, color=color_label)
            .encode(x="Article:N", y=alt.Y("Score:Q", scale=alt.Scale(domain=[-1, 1])))
        )
        pts = (
            alt.Chart(df)
            .mark_point(size=70, filled=True)
            .encode(
                x="Article:N",
                y="Score:Q",
                color=alt.Color(
                    "Sentiment:N",
                    scale=alt.Scale(
                        domain=["Positive", "Negative", "Neutral"],
                        range=["#00C851", "#ff4444", "#ffbb33"]
                    )
                ),
                tooltip=["Title:N", "Score:Q", "Sentiment:N"]
            )
        )
        return (zero + line + pts).properties(height=240)

    with col1:
        st.caption(company_a)
        st.altair_chart(_mini_timeline(data_a["articles"], "#FF5E57"), use_container_width=True)
    with col2:
        st.caption(company_b)
        st.altair_chart(_mini_timeline(data_b["articles"], "#4A9EFF"), use_container_width=True)

    st.divider()

    # ── Export both ──
    st.subheader("Export Reports")
    col1, col2 = st.columns(2)
    with col1:
        render_export(data_a, company_a)
    with col2:
        render_export(data_b, company_b)


# ──────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────

def main():
    st.title("News Intelligence Dashboard")
    st.caption("Real-time news sentiment, keyword analysis, and media coverage intelligence.")

    # ── Sidebar ──
    with st.sidebar:
        st.header("Settings")

        mode = st.radio("Analysis Mode", ["Single Company", "Compare Companies"])

        st.divider()
        num_articles = st.slider("Articles to Analyze", min_value=1, max_value=20, value=5)

        st.subheader("Date Range")
        period = st.selectbox(
            "Coverage Period",
            ["Last 7 days", "Last 30 days", "Last 90 days", "All time"]
        )
        today = datetime.today()
        days_map = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90, "All time": None}
        days = days_map[period]
        from_date = (today - timedelta(days=days)).strftime("%Y-%m-%d") if days else None

        st.divider()
        st.subheader("Alert Settings")
        alert_threshold = st.slider("Alert if Positive% below", 0, 100, 30)
        st.caption("A warning appears if positive coverage falls below this level.")

    # ── Single company mode ──
    if mode == "Single Company":
        company = st.selectbox("Select Company", COMPANIES)

        if st.button("Analyze News", type="primary", use_container_width=True):
            with st.spinner(f"Fetching and analyzing articles for {company}…"):
                data = get_sentiment_data(company, num_articles, from_date)

            if data.get("error"):
                st.error(data["error"])
                st.stop()

            dist = data["sentiment_distribution"]
            total = sum(dist.values()) or 1
            pos_pct = dist["Positive"] * 100 // total

            if pos_pct < alert_threshold:
                st.markdown(
                    f'<div class="alert-box">⚠️ <strong>Alert</strong>: Only {pos_pct}% positive coverage '
                    f'for {company} — below your {alert_threshold}% threshold.</div>',
                    unsafe_allow_html=True
                )

            render_full_dashboard(data, company)

    # ── Comparison mode ──
    else:
        col1, col2 = st.columns(2)
        with col1:
            company_a = st.selectbox("Company A", COMPANIES, index=0)
        with col2:
            company_b = st.selectbox("Company B", COMPANIES, index=1)

        if company_a == company_b:
            st.warning("Please select two different companies to compare.")
        elif st.button("Compare", type="primary", use_container_width=True):
            with st.spinner(f"Analyzing {company_a} and {company_b}…"):
                data_a = get_sentiment_data(company_a, num_articles, from_date)
                data_b = get_sentiment_data(company_b, num_articles, from_date)

            if data_a.get("error"):
                st.error(f"{company_a}: {data_a['error']}")
                st.stop()
            if data_b.get("error"):
                st.error(f"{company_b}: {data_b['error']}")
                st.stop()

            render_comparison(data_a, company_a, data_b, company_b)


if __name__ == "__main__":
    main()
