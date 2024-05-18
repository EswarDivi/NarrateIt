import streamlit as st
from conver import URLToAudioConverter
import os

groq_api_key = st.secrets["GROQ_API_KEY"]
dg_api_key = st.secrets["DG_API_KEY"]

converter = URLToAudioConverter(groq_api_key, dg_api_key)

st.set_page_config(page_title="NarrateLink", page_icon="🔊", layout="centered")
st.title("NarrateLink: Turn Any Article into a Podcast")
st.subheader("Easily convert articles from URLs into listenable audio Podcasts.")

st.write("## Enter Article URL")
url = st.text_input("URL Input", placeholder="Paste the URL here...")

voices_dict = {
    "Asteria (English - US, Female)": "aura-asteria-en",
    "Luna (English - US, Female)": "aura-luna-en",
    "Stella (English - US, Female)": "aura-stella-en",
    "Athena (English - UK, Female)": "aura-athena-en",
    "Hera (English - US, Female)": "aura-hera-en",
    "Orion (English - US, Male)": "aura-orion-en",
    "Arcas (English - US, Male)": "aura-arcas-en",
    "Perseus (English - US, Male)": "aura-perseus-en",
    "Angus (English - Ireland, Male)": "aura-angus-en",
    "Orpheus (English - US, Male)": "aura-orpheus-en",
    "Helios (English - UK, Male)": "aura-helios-en",
    "Zeus (English - US, Male)": "aura-zeus-en",
}

voices = list(voices_dict.keys())

with st.expander("Voice Options"):
    col1, col2 = st.columns(2)
    with col1:
        voice_1 = st.selectbox("Speaker 1", voices, index=6)
    with col2:
        voice_2 = st.selectbox("Speaker 2", voices, index=2)

convert_button = st.button(
    "Narrate it", help="Click to convert the URL into an audio file"
)

if convert_button and url:
    with st.spinner("Converting article to audio... Please wait."):
        try:
            audio_file = converter.url_to_audio(
                url, voices_dict[voice_2], voices_dict[voice_1]
            )
            audio_file_path = f"./{audio_file}"
            st.success("Conversion completed successfully!")

            st.audio(audio_file_path, format="audio/wav")
            with st.expander("Tap to See Conversation"):
                for entry in converter.conversation_out["conversation"]:
                    st.write(f"**{entry['speaker']}**: {entry['text']}")
                st.json(converter.conversation_out,expanded=False)
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
st.info(
    "Note: If the article exceeds 8000 words, it will be truncated to ensure optimal performance and manageability."
)
