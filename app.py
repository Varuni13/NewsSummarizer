import streamlit as st
from api import get_sentiment_report


# Add custom CSS styling for the app to enhance its UI
# This section allows us to modify the appearance of Streamlit's default UI components
st.markdown("""
    <style>
        .stApp {
            background-color: #2E3B4E;
        }

        .stButton>button {
            background-color: #FF5E57;
            color: white;
            border-radius: 12px;
        }

        .stTextInput>div>input, .stNumberInput>div>input {
            background-color: #31333F;
            color: white;
            border: 1px solid #FF5E57;
        }

        .stText {
            color: white;
            font-size: 18px;
        }

        .stSubheader {
            color: white;
        }
    </style>
""", unsafe_allow_html=True)


def main():
    """
    Main function that runs the Streamlit app. 
    This function is responsible for displaying the user interface, 
    calling the necessary functions to fetch news articles, analyze sentiment,
    and generate TTS (Text-to-Speech).
    """
    
    # Streamlit components for the user interface
    st.title("News Summarization and Text-to-Speech Application")
    st.write("Enter the company name to fetch news articles and analyze the sentiment.")

    # Dropdown for selecting the company
    company_name = st.selectbox(
        "Select Company", 
        ["Apple", "Amazon", "Tesla", "Microsoft", "Google", 
         "Facebook (Meta)", "Netflix", "Samsung", "IBM"]
    )

    # Input for the number of articles to fetch
    num_articles = st.number_input(
        "Enter the number of articles to fetch:", 
        min_value=1, max_value=20, value=5
    )

    # Ensure the user has selected a company and entered the number of articles
    if company_name and num_articles:
        # Call the function to get the sentiment report and TTS filename
        sentiment_report, tts_filename = get_sentiment_report(company_name, num_articles)

        # Display the sentiment analysis report
        st.subheader("Sentiment Analysis Report")
        st.write(sentiment_report)

        # Check if TTS filename is None or error flag and display message accordingly
        if tts_filename == "error":
            # If TTS generation fails, display an error message and retry option
            st.write("TTS Generation Failed. Please try again later.")
            if st.button("Retry TTS Generation"):
                st.experimental_rerun()  # This will trigger the process again (re-fetch articles, analyze sentiment, generate TTS)
        else:
            # If TTS is successful, display audio player for TTS output
            st.subheader("Text-to-Speech Output")
            st.audio(tts_filename, format="audio/mp3")
            print(f"Audio file path: {tts_filename}")


# Run the Streamlit app when this script is executed directly
if __name__ == "__main__":
    main()
