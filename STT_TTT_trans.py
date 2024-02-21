import queue
import re
import sys
import pygame
import pyaudio
from google.cloud import speech, texttospeech
from google.cloud import translate_v2 as translate
import pyaudio
import openai
import os

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "tribal-booth-414608-dbc61449795a.json"

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

# Set OpenAI API key
openai.api_key = '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'

class MicrophoneStream:
    """Opens a recording stream as a generator yielding the audio chunks."""

    def __init__(self: object, rate: int = RATE, chunk: int = CHUNK) -> None:
        """The audio -- and generator -- is guaranteed to be on the main thread."""
        self._rate = rate
        self._chunk = chunk

        # Create a thread-safe buffer of audio data
        self._buff = queue.Queue()
        self.closed = True

    def __enter__(self: object) -> object:
        self._audio_interface = pyaudio.PyAudio()
        self._audio_stream = self._audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self._rate,
            input=True,
            frames_per_buffer=self._chunk,
            stream_callback=self._fill_buffer,
        )

        self.closed = False

        return self

    def __exit__(
        self: object,
        type: object,
        value: object,
        traceback: object,
    ) -> None:
        """Closes the stream, regardless of whether the connection was lost or not."""
        self._audio_stream.stop_stream()
        self._audio_stream.close()
        self.closed = True
        self._buff.put(None)
        self._audio_interface.terminate()

    def _fill_buffer(
        self: object,
        in_data: object,
        frame_count: int,
        time_info: object,
        status_flags: object,
    ) -> object:
        """Continuously collect data from the audio stream, into the buffer."""
        self._buff.put(in_data)
        return None, pyaudio.paContinue

    def generator(self: object) -> object:
        """Generates audio chunks from the stream of audio data in chunks."""
        while not self.closed:
            chunk = self._buff.get()
            if chunk is None:
                return
            data = [chunk]

            while True:
                try:
                    chunk = self._buff.get(block=False)
                    if chunk is None:
                        return
                    data.append(chunk)
                except queue.Empty:
                    break

            yield b"".join(data)


def listen_print_loop(responses: object) -> str:
    """Iterates through server responses and prints them."""
    num_chars_printed = 0
    for response in responses:
        if not response.results:
            continue

        result = response.results[0]
        if not result.alternatives:
            continue

        transcript = result.alternatives[0].transcript

        if not result.is_final:
            sys.stdout.write(transcript + '\r')
            sys.stdout.flush()
            num_chars_printed = len(transcript)
        else:
            detected_language = result.language_code if hasattr(result, 'language_code') else "Unknown"
            print(f"Detected language: {detected_language}")
            print(transcript + '\n')
            trans_text = translator(transcript)
            print(trans_text)
            text_to_speech(trans_text, "output.mp3")
            pygame.mixer.init()
        
            # Play the audio using pygame
            pygame.mixer.music.load("output.mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            
            # Stop and quit pygame mixer
            pygame.mixer.music.stop()
            pygame.mixer.quit()
            
            os.remove("output.mp3")
            

            if re.search(r'\b(exit|quit)\b', transcript, re.I):
                print('Exiting...')
                break

            num_chars_printed = 0

    return transcript

def main() -> None:
    """Transcribe speech from audio file."""
    user_lang ="ta-IN"
    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=user_lang,  # Default language code
        alternative_language_codes=['es-ES', 'fr-FR', 'de-DE', 'ja-JP', 'ru-RU', 'ta-IN','hi-IN'],  # Example list of languages
        enable_automatic_punctuation=True,
    )

    streaming_config = speech.StreamingRecognitionConfig(
        config=config, interim_results=True
    )

    with MicrophoneStream(RATE, CHUNK) as stream:
        audio_generator = stream.generator()
        requests = (
            speech.StreamingRecognizeRequest(audio_content=content)
            for content in audio_generator
        )

        responses = client.streaming_recognize(streaming_config, requests)

        listen_print_loop(responses)


def translator(source_text):
    translate_client = translate.Client()

    # Translates the text into the target language
    translation = translate_client.translate(source_text, target_language='en-US')

    return translation['translatedText']

    return


def text_to_speech(text, output_file):
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",  # Language code (e.g., "en-US")
        name="en-US-Wavenet-D",  # Voice name (e.g., "en-US-Wavenet-D")
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE  # Gender of the voice
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3  # Output audio format
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to "{output_file}"')


if __name__ == "__main__":main()
