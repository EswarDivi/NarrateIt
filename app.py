import streamlit as st
from conver import URLToAudioConverter
import os
from dotenv import load_dotenv

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")
dg_api_key = os.getenv("DG_API_KEY")

converter = URLToAudioConverter(groq_api_key, dg_api_key)

st.set_page_config(page_title="NarrateLink", layout="wide")
st.title("NarrateLink: Turn Any Article into Audio")
st.subheader("Easily convert articles from URLs into listenable audio formats.")


st.write("## Enter Article URL")
url = st.text_input("URL Input", placeholder="Paste the URL here...")

convert_button = st.button(
    "Narrate it", help="Click to convert the URL into an audio file"
)

if convert_button and url:
    with st.spinner("Converting article to audio... Please wait."):
        try:
            audio_file = converter.url_to_audio(url)
            audio_file_path = f"./{audio_file}"

            st.audio(audio_file_path, format="audio/wav")

            st.json(converter.conversation_out)


            st.download_button(
                label="Download Audio File",
                data=open(audio_file_path, "rb"),
                file_name=audio_file,
                mime="audio/wav",
                help="Download the converted audio file",
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")
else:
    if convert_button:
        st.error("Please enter a valid URL.")

st.info(
    "Powered by Groq and Deepgram APIs. URLs are parsed by https://r.jina.ai/. Ensure your URLs are accessible and point to text-rich content for best results."
)
