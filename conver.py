import os
import re
import httpx
import json
import wave
import base64
import random
from dotenv import load_dotenv
from deepgram import DeepgramClient, SpeakOptions
from groq import Groq


class URLToAudioConverter:
    def __init__(self, groq_api_key, dg_api_key):
        self.groq_client = Groq(api_key=groq_api_key)
        self.deepgram_client = DeepgramClient(api_key=dg_api_key)
        self.template = """
        {
            "conversation": [
                {"speaker": "", "text": ""},
                {"speaker": "", "text": ""}
            ]
        }
        """
        self.conversation_out = ""

    def fetch_text(self, url):
        prefix_url = "https://r.jina.ai/"
        url = prefix_url + url
        response = httpx.get(url, timeout=60.0)
        return response.text

    def extract_conversation(self, text):
        chat_completion = self.groq_client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": f"{text} \n Convert the provided text into a informative podcast conversation between two experts. The tone should be professional and engaging. Please adhere to the following format and return the conversation in JSON: \n {self.template}",
                }
            ],
            model="llama3-8b-8192",
        )
        pattern = r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}"
        json_match = re.search(pattern, chat_completion.choices[0].message.content)

        return json_match.group()

    def text_to_speech(self, conversation_json,voice_1,voice_2):
        conversation = json.loads(conversation_json)
        self.conversation_out = conversation
        filenames = []
        random_bytes = os.urandom(8)
        folder_name = base64.urlsafe_b64encode(random_bytes).decode("utf-8")
        os.makedirs(folder_name, exist_ok=True)

        for i, turn in enumerate(conversation["conversation"]):
            filename = os.path.join(folder_name, f"output_{i}.wav")
            model = voice_1 if i % 2 else voice_2
            options = SpeakOptions(model=model, encoding="linear16", container="wav")
            self.deepgram_client.speak.v("1").save(
                filename, {"text": turn["text"]}, options
            )
            filenames.append(filename)
        return filenames, folder_name

    def combine_audio_files(self, filenames, output_file):
        with wave.open(filenames[0], "rb") as first_file:
            params = first_file.getparams()
            with wave.open(output_file, "wb") as output:
                output.setparams(params)
                for filename in filenames:
                    with wave.open(filename, "rb") as file:
                        output.writeframes(file.readframes(file.getnframes()))

    def url_to_audio(self, url,voice_1,voice_2):
        text = self.fetch_text(url)
        if len(text.split()) > 5000:
            text = " ".join(text.split()[:5000])
        conversation_json = self.extract_conversation(text)
        audio_files, folder_name = self.text_to_speech(conversation_json,voice_1,voice_2)
        final_output = os.path.join(folder_name, "combined_output.wav")
        self.combine_audio_files(audio_files, final_output)
        return final_output


# Example usage:
# load_dotenv()
# groq_api_key = os.getenv("GROQ_API_KEY")
# dg_api_key = os.getenv("DG_API_KEY")
# converter = URLToAudioConverter(groq_api_key, dg_api_key)
# audio_file = converter.url_to_audio("https://example.com/article")
