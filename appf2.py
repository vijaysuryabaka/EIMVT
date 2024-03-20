from datetime import datetime
import time
from flask import Flask, render_template, request, jsonify
import queue
import sys
import pyaudio
from google.cloud import speech, texttospeech
from google.cloud import translate_v2 as translate
import os
import html
from transformers import pipeline

emotion = pipeline('sentiment-analysis', model='arpanghoshal/EmoRoBERTa')

app = Flask(__name__)

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
        self._stream_closed = True  # Flag to indicate whether the stream is closed
        self._stop_stream = False  # Flag to control when to stop the stream

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
        self._stream_closed = False  # Stream is opened
        self._stop_stream = False  # Reset stop stream flag

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
        self._stream_closed = True  # Stream is closed
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
        while not self.closed and not self._stop_stream:  # Check the flag to stop streaming
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
            trans_text, emotext = translator(transcript, target_languagee)
            print(trans_text)
            print("emotext:", emotext)
            emotion = emotions(emotext)
            audio_name = text_to_speech(trans_text, "output.mp3", target_languagee,"static/audio",emotion)

            if emotext == "exit":
                print('Exiting...')
                return transcript, trans_text, emotion, audio_name  # Return the values and exit the loop

            num_chars_printed = 0

        if emotext:
            return transcript, trans_text, emotion, audio_name  # Return the values

    return transcript, trans_text, emotion


def translator(source_text, target_languagee):
    translate_client = translate.Client()

    translation = translate_client.translate(source_text, target_language=target_languagee)

    emotext = translate_client.translate(source_text, target_language='en-US')

    translated_text = html.unescape(translation['translatedText'])
    emotext_text = html.unescape(emotext['translatedText'])

    return translated_text, emotext_text


def emotions(text):
    emotion_labels = emotion(text)
    print(emotion_labels[0]['label'])
    return emotion_labels[0]['label']


def text_to_speech(text, output_file, target_languagee, output_dir, emotion):
    voice_map={
        'ta:IN' : 'ta-IN-Wavenet-D',
        'en-US' : 'en-US-Wavenet-D',
        'fr-FR' : 'fr-FR-Standard-D',
        'ja-JP' : 'ja-JP-Wavenet-D',
        'hi-IN' : 'hi-IN-Wavenet-D'    }

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

    voice_params = {'pitch': 0, 'speaking_rate': 1.0}

    if emotion in emotion_to_voice_params:
        voice_params.update(emotion_to_voice_params[emotion])

    print(voice_params['pitch'], voice_params['speaking_rate'])

    client = texttospeech.TextToSpeechClient()

    synthesis_input = texttospeech.SynthesisInput(text=text)

    voice = texttospeech.VoiceSelectionParams(
        language_code=target_languagee,
        name=voice_map.get(target_languagee),
        ssml_gender=texttospeech.SsmlVoiceGender.MALE
    )

    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3,
        pitch=voice_params['pitch'],
        speaking_rate=voice_params['speaking_rate']
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{emotion}_{timestamp}.mp3"
    
    output_path = os.path.join(output_dir, output_file)

    with open(output_path, "wb") as out:
        out.write(response.audio_content)
        print(f'Audio content written to "{output_path}"')

    return output_file


responses = None # Initialize responses variable

language_mapping = {
            'tam': 'ta-IN',
            'eng': 'en-US',
            'fre': 'fr-FR',
            'jap': 'ja-JP',
            'hin': 'hi-IN'
        }

@app.route('/')
def index():
    return render_template('page.html')


@app.route('/toggle-recording', methods=['POST'])
def toggle_recording():
    action = request.form.get('action')
    print(action)
    if action == 'start':
        print("hi")
        # global responses   # Use global keyword to modify global variable
        source_lang = request.form['source']  # Corrected line
        print(source_lang)
        user_lang = language_mapping.get(source_lang)
        print(user_lang)
        if user_lang:
            with MicrophoneStream(RATE, CHUNK) as stream:
                print("Hello")
                audio_generator = stream.generator()
                config = speech.RecognitionConfig(
                    encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                    sample_rate_hertz=RATE,
                    language_code=user_lang,
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
        
    elif action == 'stop':
        print("hii")
        target_lang = request.form.get('to')
        target_languagee = language_mapping.get(target_lang)
        print(target_languagee)
        transcribed_text, translated_text, emotion, audio_file = listen_print_loop(responses, target_languagee)

    return jsonify({'success': True})



# @app.route('/stop', methods=['POST'])
# def stop():
#     global responses  # Use global keyword to access global variable
#     target_lang = request.form['to']
#     target_languagee = language_mapping.get(target_lang)
#     print(target_languagee)
#     transcribed_text, translated_text, emotion, audio_file = listen_print_loop(responses, target_languagee)
#     return jsonify({'success': True})


if __name__ == "__main__":
    app.run(debug=True)
