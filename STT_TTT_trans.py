import queue
import re
import sys
import pygame
import pyaudio
from google.cloud import speech, texttospeech
from google.cloud import translate_v2 as translate
import os
from transformers import pipeline
emotion = pipeline('sentiment-analysis', model='arpanghoshal/EmoRoBERTa')

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "tribal-booth-414608-dbc61449795a.json"

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms


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


def listen_print_loop(responses: object , target_languagee) -> str:
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
            trans_text,emotext = translator(transcript,target_languagee)
            print(trans_text)
            #print("emotext:",emotext)
            detected_emotions=emotions(emotext)
            text_to_speech(trans_text, "output.mp3",target_languagee,detected_emotions)
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
    #"""

    user_lang=input("Enter user Language:")
    target_languagee=input("Enter output Language:")

    #"""
    #user_lang ="ta-IN"

    client = speech.SpeechClient()
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code=user_lang,  # Default language code
        # alternative_language_codes=['es-ES', 'fr-FR', 'de-DE', 'ja-JP', 'ru-RU', 'ta-IN','hi-IN'],  # Example list of languages
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

        listen_print_loop(responses,target_languagee)


def translator(source_text,target_languagee):
    translate_client = translate.Client()

    # Translates the text into the target language
    translation = translate_client.translate(source_text, target_language=target_languagee)

    #for emotions handling
    emotext = translate_client.translate(source_text, target_language='en-US')

    return translation['translatedText'], emotext['translatedText']
    


def emotions(text):
    emotion_labels = emotion(text)
    detected_emotions=emotion_labels[0]['label']
    print(emotion_labels[0]['label'])
    return detected_emotions

def modulate(detected_emotion):
    # Default values for neutral emotion
    pitch = 0
    speaking_rate = 1.0

    emotion_modulations = {
        "admiration": {"pitch": 5, "rate": 1.1},
        "amusement": {"pitch": 8, "rate": 1.2},
        "anger": {"pitch": -2, "rate": 1.3},
        "annoyance": {"pitch": -4, "rate": 1.1},
        "approval": {"pitch": 5, "rate": 1.1},
        "caring": {"pitch": 6, "rate": 1.0},
        "confusion": {"pitch": 0, "rate": 0.9},
        "curiosity": {"pitch": 4, "rate": 1.1},
        "desire": {"pitch": 5, "rate": 1.0},
        "disappointment": {"pitch": -4, "rate": 0.8},
        "disapproval": {"pitch": -5, "rate": 0.9},
        "disgust": {"pitch": -6, "rate": 0.8},
        "embarrassment": {"pitch": -2, "rate": 0.9},
        "excitement": {"pitch": 9, "rate": 1.4},
        "fear": {"pitch": -3, "rate": 1.2},
        "gratitude": {"pitch": 6, "rate": 1.0},
        "grief": {"pitch": -10, "rate": 0.7},
        "joy": {"pitch": 10, "rate": 1.3},
        "love": {"pitch": 6, "rate": 1.0},  
        "nervousness": {"pitch": -1, "rate": 1.2},
        "optimism": {"pitch": 7, "rate": 1.2},
        "pride": {"pitch": 6, "rate": 1.1},
        "realization": {"pitch": 3, "rate": 1.0},
        "relief": {"pitch": 5, "rate": 1.0},
        "remorse": {"pitch": -8, "rate": 0.9},
        "sadness": {"pitch": -5, "rate": 0.8},
        "surprise": {"pitch": 4, "rate": 1.2},
        "neutral": {"pitch": 0, "rate": 1.0}
    }

    # Apply modulation if the emotion is recognized
    if detected_emotion in emotion_modulations:
        pitch = emotion_modulations[detected_emotion]["pitch"]
        speaking_rate = emotion_modulations[detected_emotion]["rate"]

    return pitch, speaking_rate


def text_to_speech(text, output_file,target_languagee,detected_emotions):
    client = texttospeech.TextToSpeechClient()
    voice_map = {
    'ta-IN': 'ta-IN-Wavenet-D',
    'en-US': 'en-US-Wavenet-D',
    'fr-FR': 'fr-FR-Standard-D',
    'ja-JP': 'ja-JP-Wavenet-D',
    'hi-IN': 'hi-IN-Wavenet-D'
}
    
    synthesis_input = texttospeech.SynthesisInput(text=text)
    pitch, speaking_rate = modulate(detected_emotions)
    voice_name = voice_map.get(target_languagee, None)
    if not voice_name:
        print(f"Voice not found for language {target_languagee}, using default.")
        voice_name = "en-US-Wavenet-D"

    voice = texttospeech.VoiceSelectionParams(
        #language_code="en-US",  # Language code (e.g., "en-US")
        language_code=target_languagee,
        name=voice_name,  # Voice name (e.g., "en-US-Wavenet-D")
        ssml_gender=texttospeech.SsmlVoiceGender.MALE  # Gender of the voice
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=pitch,
        speaking_rate=speaking_rate  # Output audio format
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    print(voice_name)
    print(pitch,)
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to "{output_file}"')


if __name__ == "__main__":main()
