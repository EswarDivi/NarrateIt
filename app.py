import streamlit as st
import conver
from conver import URLToAudioConverter
from dataclasses import dataclass

st.set_page_config(
    page_title="NarrateLink",
    page_icon="🔊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@dataclass
class ConversationConfig:
    max_words: int = 15000
    prefix_url: str = "https://r.jina.ai/"
    model_name: str = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"


if "audio_file" not in st.session_state:
    st.session_state.audio_file = None

with st.sidebar:
    st.image("https://img.icons8.com/clouds/100/000000/podcast.png", width=100)
    st.title("Settings")

    st.subheader("🎤 Voice Settings")
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

    voice_1 = st.selectbox("Speaker 1", voices, index=7)
    voice_2 = st.selectbox("Speaker 2", voices, index=0)


st.title("🎧 NarrateLink")
st.caption("Transform articles into engaging podcasts instantly")

url_container = st.container()
with url_container:
    url = st.text_input(
        "Enter Article URL",
        placeholder="https://example.com/article",
        help="Paste the URL of the article you want to convert",
    )

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        convert_button = st.button(
            "🎵 Generate Podcast", use_container_width=True, type="primary"
        )


if convert_button:
    if not url:
        st.error("⚠️ Please enter a URL to continue")
    else:
        try:
            with st.status("🎙️ Creating your podcast...", expanded=True) as status:
                llm_api_key = st.secrets["TOGETHER_API_KEY"]
                dg_api_key = st.secrets["DG_API_KEY"]
                config = ConversationConfig(
                    max_words=15000,
                    prefix_url="https://r.jina.ai/",
                    model_name="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo",
                )
                converter = URLToAudioConverter(config, llm_api_key, dg_api_key)

                status.update(label="Converting to audio...", state="running")
                audio_file = converter.url_to_audio(
                    url, voices_dict[voice_2], voices_dict[voice_1]
                )

                status.update(label="✅ Conversion complete!", state="complete")

            st.success("🎉 Your podcast is ready!")

            st.subheader("🎧 Listen Now")
            st.audio(f"./{audio_file}", format="audio/wav")

            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.download_button(
                    label="⬇️ Download Podcast",
                    data=open(f"./{audio_file}", "rb"),
                    file_name=audio_file,
                    mime="audio/wav",
                    use_container_width=True,
                )

            with st.expander("📝 View Transcript"):
                for entry in converter.llm_out["conversation"]:
                    st.markdown(f"**{entry['speaker']}**  \n{entry['text']}")

        except Exception as e:
            st.error(f"😕 Oops! Something went wrong: {str(e)}")
            st.info("🔄 Try refreshing the page or using a different URL")

st.divider()
st.markdown(
    """
    <div style='text-align: center'>
        <p>Want a secure, private text-to-speech solution? Check out 
        <a href='https://huggingface.co/spaces/eswardivi/Podcastify'>Podcastify</a> 
        </p>
        the open-source alternative that runs entirely on your device.
    </div>
    """,
    unsafe_allow_html=True,
)
