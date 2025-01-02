from dataclasses import dataclass
from typing import List, Tuple, Dict
import os
import re
import httpx
import json
from openai import OpenAI
import logfire
from deepgram import DeepgramClient, SpeakOptions
import wave
import base64
from pathlib import Path


@dataclass
class ConversationConfig:
    max_words: int = 3000
    prefix_url: str = "https://r.jina.ai/"
    model_name: str = "meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"


class URLToAudioConverter:
    def __init__(self, config: ConversationConfig, llm_api_key: str, dg_api_key: str):
        self.config = config
        self.llm_client = OpenAI(api_key=llm_api_key, base_url="https://api.together.xyz/v1")
        self.deepgram_client = DeepgramClient(api_key=dg_api_key)
        self.llm_out= None
        self._setup_logging()

    def _setup_logging(self) -> None:
        logfire.configure()
        logfire.instrument_requests()
        logfire.instrument_system_metrics()
        logfire.instrument_openai(self.llm_client)

    def fetch_text(self, url: str) -> str:
        if not url:
            raise ValueError("URL cannot be empty")

        full_url = f"{self.config.prefix_url}{url}"
        try:
            response = httpx.get(full_url, timeout=60.0)
            response.raise_for_status()
            return response.text
        except httpx.HTTPError as e:
            raise RuntimeError(f"Failed to fetch URL: {e}")

    def extract_conversation(self, text: str) -> Dict:
        if not text:
            raise ValueError("Input text cannot be empty")

        try:
            chat_completion = self.llm_client.chat.completions.create(
                messages=[{"role": "user", "content": self._build_prompt(text)}],
                model=self.config.model_name,
            )

            pattern = r"\{(?:[^{}]|(?:\{[^{}]*\}))*\}"
            json_match = re.search(pattern, chat_completion.choices[0].message.content)

            if not json_match:
                raise ValueError("No valid JSON found in response")

            return json.loads(json_match.group())
        except Exception as e:
            raise RuntimeError(f"Failed to extract conversation: {e}")

    def _build_prompt(self, text: str) -> str:
        template = """
        {
            "conversation": [
                {"speaker": "", "text": ""},
                {"speaker": "", "text": ""}
            ]
        }
        """
        return (
            f"{text}\nConvert the provided text into a short informative and crisp "
            f"podcast conversation between two experts. The tone should be "
            f"professional and engaging. Please adhere to the following "
            f"format and return the conversation in JSON:\n{template}"
        )

    def text_to_speech(
        self, conversation_json: Dict, voice_1: str, voice_2: str
    ) -> Tuple[List[str], str]:
        output_dir = Path(self._create_output_directory())
        filenames = []

        try:
            for i, turn in enumerate(conversation_json["conversation"]):
                filename = output_dir / f"output_{i}.wav"
                voice_model = voice_1 if i % 2 else voice_2

                options = SpeakOptions(
                    model=voice_model, encoding="linear16", container="wav"
                )

                self.deepgram_client.speak.v("1").save(
                    str(filename), {"text": turn["text"]}, options
                )
                filenames.append(str(filename))

            return filenames, str(output_dir)
        except Exception as e:
            self._cleanup_files(filenames)
            raise RuntimeError(f"Failed to convert text to speech: {e}")

    def _create_output_directory(self) -> str:
        random_bytes = os.urandom(8)
        folder_name = base64.urlsafe_b64encode(random_bytes).decode("utf-8")
        os.makedirs(folder_name, exist_ok=True)
        return folder_name

    def _cleanup_files(self, files: List[str]) -> None:
        for file in files:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except OSError:
                pass

    def combine_audio_files(self, filenames: List[str], output_file: str) -> None:
        if not filenames:
            raise ValueError("No input files provided")

        try:
            with wave.open(filenames[0], "rb") as first_file:
                params = first_file.getparams()
                with wave.open(output_file, "wb") as output:
                    output.setparams(params)
                    for filename in filenames:
                        with wave.open(filename, "rb") as file:
                            output.writeframes(file.readframes(file.getnframes()))
        except Exception as e:
            raise RuntimeError(f"Failed to combine audio files: {e}")

    def url_to_audio(self, url: str, voice_1: str, voice_2: str) -> str:
        text = self.fetch_text(url)

        words = text.split()
        if len(words) > self.config.max_words:
            text = " ".join(words[: self.config.max_words])

        conversation_json = self.extract_conversation(text)
        self.llm_out = conversation_json
        audio_files, folder_name = self.text_to_speech(
            conversation_json, voice_1, voice_2
        )

        final_output = os.path.join(folder_name, "combined_output.wav")
        self.combine_audio_files(audio_files, final_output)

        self._cleanup_files(audio_files)

        return final_output
