from datetime import datetime
import time
# import uuid
from flask import Flask, render_template, request, send_from_directory, url_for
import queue
import re
import sys
import pygame
import pyaudio
from google.cloud import speech, texttospeech
from google.cloud import translate_v2 as translate
import os
from transformers import pipeline
import html

emotion = pipeline('sentiment-analysis', model='arpanghoshal/EmoRoBERTa')

app = Flask(__name__)

# Set Google Cloud credentials
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "tribal-booth-414608-dbc61449795a.json"

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

# AUDIO_DIR = "static/audio"

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


def listen_print_loop(responses: object, target_languagee) -> str:
    """Iterates through server responses and prints them."""
    trans_text = ""  # Initialize trans_text
    emotext = ""     # Initialize emotion
    transcript = ""  # Initialize transcript
    num_chars_printed = 0

    # print("Entering listen_print_loop")  # Add this print statement
    voice_ip=[]

    for response in responses:
        # print("Processing response...")  # Add this print statement

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
            trans_text, emotext = translator(transcript, target_languagee)
            print(trans_text)
            print("emotext:", emotext)
            emotion = emotions(emotext)
            audio_name = text_to_speech(trans_text, target_languagee,"static/audio_op",emotion)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            input_v = f"input_{timestamp}.mp3"
            voice_ip.append({'transcript': transcript, 'audio_file': input_v})

            input_path = os.path.join("static/audio_ip", input_v)

            with open(input_path, "wb") as out:
                out.write(transcript)
                print(f'Audio content written to "{input_path}"')
            # pygame.mixer.init()

            # # Play the audio using pygame
            # pygame.mixer.music.load("output.mp3")
            # pygame.mixer.music.play()
            # while pygame.mixer.music.get_busy():
            #     pygame.time.Clock().tick(10)

            # # Stop and quit pygame mixer
            # pygame.mixer.music.stop()
            # pygame.mixer.quit()

            # os.remove("output.mp3")
            # print(transcript)

            if emotext=="exit":
                print('Exiting...')
                break

            num_chars_printed = 0

        # print("Exiting listen_print_loop")
        if emotext:
            return transcript, trans_text, emotion, audio_name

    return 0



def translator(source_text, target_languagee):
    translate_client = translate.Client()

    # Translates the text into the target language
    translation = translate_client.translate(source_text, target_language=target_languagee)

    # for emotions handling
    emotext = translate_client.translate(source_text, target_language='en-US')

    # Decode HTML entities in translated text
    translated_text = html.unescape(translation['translatedText'])
    emotext_text = html.unescape(emotext['translatedText'])

    return translated_text, emotext_text



def emotions(text):
    emotion_labels = emotion(text)
    print(emotion_labels[0]['label'])
    return emotion_labels[0]['label']


def text_to_speech(text, target_languagee, output_dir,emotion):
    voice_map={
        'ta:IN' : 'ta-IN-Wavenet-D',
        'en-US' : 'en-US-Wavenet-D',
        'fr-FR' : 'fr-FR-Standard-D',
        'ja-JP' : 'ja-JP-Wavenet-D',
        'hi-IN' : 'hi-IN-Wavenet-D'    }
    
        # Define voice parameters for each emotion
    emotion_to_voice_params = {
        'admiration': {'pitch': 10, 'speaking_rate': 1.1},
        'amusement': {'pitch': 10, 'speaking_rate': 1.1},
        'anger': {'pitch': -10, 'speaking_rate': 0.9},
        'annoyance': {'pitch': -10, 'speaking_rate': 0.9},
        'approval': {'pitch': 10, 'speaking_rate': 1.1},
        'caring': {'pitch': 0, 'speaking_rate': 1.0},
        'confusion': {'pitch': -10, 'speaking_rate': 0.9},
        'curiosity': {'pitch': 0, 'speaking_rate': 1.0},
        'desire': {'pitch': 0, 'speaking_rate': 1.1},
        'disappointment': {'pitch': -10, 'speaking_rate': 0.9},
        'disapproval': {'pitch': -10, 'speaking_rate': 0.9},
        'disgust': {'pitch': -10, 'speaking_rate': 0.9},
        'embarrassment': {'pitch': -10, 'speaking_rate': 0.9},
        'excitement': {'pitch': 10, 'speaking_rate': 1.1},
        'fear': {'pitch': -10, 'speaking_rate': 0.9},
        'gratitude': {'pitch': 10, 'speaking_rate': 1.1},
        'grief': {'pitch': -10, 'speaking_rate': 0.9},
        'joy': {'pitch': 10, 'speaking_rate': 1.1},
        'love': {'pitch': 10, 'speaking_rate': 1.1},
        'nervousness': {'pitch': -10, 'speaking_rate': 0.9},
        'optimism': {'pitch': 10, 'speaking_rate': 1.1},
        'pride': {'pitch': 10, 'speaking_rate': 1.1},
        'realization': {'pitch': 0, 'speaking_rate': 1.0},
        'relief': {'pitch': 10, 'speaking_rate': 1.1},
        'remorse': {'pitch': -10, 'speaking_rate': 0.9},
        'sadness': {'pitch': -10, 'speaking_rate': 0.9},
        'surprise': {'pitch': 0, 'speaking_rate': 1.1},
        'neutral': {'pitch': 0, 'speaking_rate': 1.0}  # Neutral emotion
    }

    # Set default voice parameters
    voice_params = {'pitch': 0, 'speaking_rate': 1.0}

    # Update voice parameters based on the detected emotion
    if emotion in emotion_to_voice_params:
        voice_params.update(emotion_to_voice_params[emotion])


    print(voice_params['pitch'],voice_params['speaking_rate'])
    
    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        # language_code="en-US",  # Language code (e.g., "en-US")
        language_code=target_languagee,
        name=voice_map.get(target_languagee),  # Voice name (e.g., "en-US-Wavenet-D")
        ssml_gender=texttospeech.SsmlVoiceGender.MALE  # Gender of the voice
    )
    print( target_languagee,voice.name,voice.language_code)
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch = voice_params['pitch'],
        speaking_rate = voice_params['speaking_rate'] # Output audio format
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    #  Generate a unique filename using UUID
    # output_file = str(uuid.uuid4()) + ".mp3"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{emotion}_{timestamp}.mp3"
    
    output_path = os.path.join(output_dir, output_file)

    with open(output_path, "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to "{output_path}"')

    return output_file


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        from_lang = request.form['from']
        language_mapping = {
            'tam': 'ta-IN',  # Tamil
            'eng': 'en-US',  # English
            'fre': 'fr-FR',  # French
            'jap': 'ja-JP',# Japanese
            'hin': 'hi-IN'  # hindi
            # Add more mappings as needed
        }
        target_lang = request.form['to']
        target_languagee = language_mapping.get(target_lang)
        user_lang = language_mapping.get(from_lang)
        print(user_lang,target_languagee)
        if user_lang:
            with MicrophoneStream(RATE, CHUNK) as stream:
                audio_generator = stream.generator()
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=RATE,
                    language_code=user_lang,
                    # alternative_language_codes=['es-ES', 'fr-FR', 'de-DE', 'ja-JP', 'ru-RU', 'ta-IN', 'hi-IN'],
                    enable_automatic_punctuation=True,
                )

                streaming_config = speech.StreamingRecognitionConfig(
                    config=config, interim_results=True
                )

                client = speech.SpeechClient()
                requests = (
                    speech.StreamingRecognizeRequest(audio_content=content)
                    for content in audio_generator
                )
                responses = client.streaming_recognize(streaming_config, requests)

                transcribed_text,translated_text,emotion, audio_file= listen_print_loop(responses, target_languagee)
                # translated_text = translate_text(transcribed_text)
                # print(translated_text)
                # text_to_speech(translated_text, "output.mp3", target_languagee)

                # Return the transcribed and translated text to the HTML page
                # print(transcribed_text)
                # audio_file = url_for('static', filename='audio/output.mp3')
                return render_template('app_ip.html', transcribed_text=transcribed_text,
                                       translated_text= translated_text, emotion = emotion,audio=audio_file)
        else:
            return render_template('app_ip.html', error="Please select a language.")

    return render_template('app_ip.html')




# @app.route('/remove_audio', methods=['GET'])
# def remove_audio():
#     try:
#         os.remove(os.path.join(AUDIO_DIR, "output.mp3"))
#         print("Audio file removed successfully")
#         return "Audio file removed successfully"
#     except Exception as e:
#         print(f"Error removing audio file: {e}")
#         return "Error removing audio file"

# @app.route('/remove_audio', methods=['GET'])
# def remove_audio():
#     # Remove the audio file
#     audio_path = os.path.join(app.static_folder, 'audio', 'output.mp3')
#     if os.path.exists(audio_path):
#         os.remove(audio_path)
#         print("Audio file removed successfully.")
#     else:
#         print("Audio file does not exist.")

#     # Return a response
#     return "Audio file removed successfully."

# @app.route('/audio/<path:filename>')
# def serve_audio(filename):
#     return send_from_directory(AUDIO_DIR, filename)

# def main() -> None:
#     """Transcribe speech from audio file."""
#     # """

#     user_lang = input("Enter user Language:")
#     target_languagee = input("Enter output Language:")

#     # """
#     # user_lang ="ta-IN"

#     client = speech.SpeechClient()
#     config = speech.RecognitionConfig(
#         encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
#         sample_rate_hertz=RATE,
#         language_code=user_lang,  # Default language code
#         alternative_language_codes=['es-ES', 'fr-FR', 'de-DE', 'ja-JP', 'ru-RU', 'ta-IN', 'hi-IN'],  # Example list of languages
#         enable_automatic_punctuation=True,
#     )

#     streaming_config = speech.StreamingRecognitionConfig(
#         config=config, interim_results=True
#     )

#     with MicrophoneStream(RATE, CHUNK) as stream:
#         audio_generator = stream.generator()
#         requests = (
#             speech.StreamingRecognizeRequest(audio_content=content)
#             for content in audio_generator
#         )

#         responses = client.streaming_recognize(streaming_config, requests)

#         listen_print_loop(responses, target_languagee)


if __name__ == "__main__":
    # main()
    app.run(debug=True)
