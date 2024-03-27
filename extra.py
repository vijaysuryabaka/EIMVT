import html
import os
import threading
import wave
from datetime import datetime
import boto3
import pyaudio
from botocore.exceptions import NoCredentialsError
from flask import Flask, jsonify, render_template, request
from google.cloud import speech
from google.cloud import texttospeech as tts
from google.cloud import translate_v2 as translate
from transformers import pipeline
import requests
from auth import auth
from pymongo import MongoClient

# Configure your S3 bucket name
S3_BUCKET_NAME = 'audioemo'

uri = 'mongodb+srv://Emo:9W6QkCDfFeLBBepA@cluster0.uc1at1a.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0'
client = MongoClient(uri)
db = client['EIMVT']

emotions = pipeline('sentiment-analysis', model='arpanghoshal/EmoRoBERTa')

app = Flask(__name__)
app.secret_key = 'IUY!&TORG#Y!GRR#&!U'
app.register_blueprint(auth, url_prefix='/auth')
app.config["db"] = db

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "tribal-booth-414608-dbc61449795a.json"

RATE = 44100  # Adjusted the sample rate to match the recording settings

class MicrophoneRecorder:
    emotions = pipeline('sentiment-analysis', model='arpanghoshal/EmoRoBERTa')
    def __init__(self):
        self.stream = None
        self.p = pyaudio.PyAudio()
        self.frames = []
        self.s3_client = boto3.client('s3')
        self.is_recording = False  # Flag to indicate if recording is in progress

    def start_recording(self):
        self.is_recording = True
        self.stream = self.p.open(format=pyaudio.paInt16,
                                  channels=1,
                                  rate=RATE,
                                  input=True,
                                  frames_per_buffer=1024)
        self.frames = []
        self.thread = threading.Thread(target=self._record)
        self.thread.start()

    def _record(self):
        while self.is_recording:
            data = self.stream.read(1024)
            self.frames.append(data)

    def stop_recording(self, fromlang, tolang):
        self.is_recording = False
        self.stream.stop_stream()
        self.stream.close()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"input_{timestamp}.wav"

        # Save the recording locally first
        self.save_recording(filename)

        use_local_file = False
        s3_input_path = f"{filename}"

        # Try to upload to S3
        try:
            self.s3_client.upload_file(filename, S3_BUCKET_NAME, s3_input_path)
            print(f"File {filename} uploaded to {s3_input_path} successfully.")
        except Exception as e:
            print(f"Failed to upload {filename} to S3: {e}. Using local file for further processing.")
            use_local_file = True

        if not use_local_file:
            # If upload succeeds, remove the local file
            os.remove(filename)

        # Process the recording, using S3 path if upload succeeded, or local path if failed
        file_path_for_processing = s3_input_path if not use_local_file else filename
        transcribed_text = self.transcribe_audio(file_path_for_processing, fromlang, use_local_file)
        translated_text, emotext = self.trans_text(transcribed_text, tolang)
        audio_emotion = self.audio_emo(file_path_for_processing)
        emotion = self.emotionlabel(emotext)
        audio_url = self.tts(translated_text, tolang, emotion)

        return transcribed_text, translated_text, emotion, audio_url, audio_emotion


    def save_recording(self, filename):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()


    def transcribe_audio(self, file_path, fromlang, use_local_file=False):
        if use_local_file:
            local_file_path = file_path
        else:
            # Assuming file_path is the S3 object key
            filename = file_path.split('/')[-1]
            local_file_path = f"./{filename}"
            try:
                self.s3_client.download_file(S3_BUCKET_NAME, file_path, local_file_path)
                print(f"Downloaded {file_path} from S3 for processing.")
            except Exception as e:
                print(f"Failed to download {file_path} from S3: {e}")
                return ""

        # File transcription process remains the same
        with open(local_file_path, 'rb') as audio_file:
            content = audio_file.read()

        client = speech.SpeechClient()
        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code=fromlang,
        )
        try:
            response = client.recognize(config=config, audio=audio)
            transcribed_text = ''.join([result.alternatives[0].transcript for result in response.results])
        except Exception as e:
            print(f"Error during transcription: {e}")
            transcribed_text = ""

        # Delete the local file if it was downloaded from S3
        if not use_local_file:
            os.remove(local_file_path)

        print("Transcribed Text:", transcribed_text)
        return transcribed_text

    
    def trans_text(self, text, tolang):
        translate_client = translate.Client()

    # Translates the text into the target language
        translated_text = translate_client.translate(text, target_language=tolang)
        trans_text = html.unescape(translated_text['translatedText'])

        emotion_text = translate_client.translate(text, target_language='en-US')
        emo_text = html.unescape(emotion_text['translatedText'])
        
        print("translated text:",translated_text)

        return trans_text, emo_text
    
    def emotionlabel(self, emotext):
        emotion = emotions(emotext)
        print(emotion[0]['label'])
        return emotion[0]['label']
    
    def audio_emo(self, audio_file_path):
        api_url = "http://localhost:8080/classify-emotion"
        files = {'file': open(audio_file_path, 'rb')}
        try:
            response = requests.post(api_url, files=files)
            
            if response.status_code == 200:
                emotion_label = response.json().get('emotion')
                print(f"Classified Emotion: {emotion_label}")
                return emotion_label
            else:
                print("Failed to classify emotion")
                return "error"
        except Exception as ex:
            print(f"API request failed: {ex}")
    
    def tts(self, text, tolang, emotion):
        if emotion in emotion_to_voice_params:
            voice_params.update(emotion_to_voice_params[emotion])

        # print(voice_params['pitch'],voice_params['speaking_rate'])
        
        client = tts.TextToSpeechClient()

        synthesis_input = tts.SynthesisInput(text=text)

        voice = tts.VoiceSelectionParams(
            # language_code="en-US",  # Language code (e.g., "en-US")
            language_code=tolang,
            name=voice_map.get(tolang),  # Voice name (e.g., "en-US-Wavenet-D")
            ssml_gender=tts.SsmlVoiceGender.MALE  # Gender of the voice
        )
        # print( tolang,voice.name,voice.language_code)
        audio_config = tts.AudioConfig(
            audio_encoding=tts.AudioEncoding.MP3,
            pitch = voice_params['pitch'],
            speaking_rate = voice_params['speaking_rate'] # Output audio format
        )

        response = client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        local_filename = f"op_{timestamp}.mp3"
        local_filepath = os.path.join("static", local_filename)
        # Use a temp directory for local storage
        s3_filepath = f"audio/{local_filename}"

        # Save locally
        if not os.path.exists("static"):
            os.makedirs("static")
        with open(local_filepath, "wb") as out_file:
            out_file.write(response.audio_content)
            print(f"Audio content written to {local_filepath}")

        # Attempt to upload to S3 and prepare the response URL
        try:
            self.upload_file_to_s3(local_filepath, s3_filepath)
            audio_url = self.generate_s3_url(s3_filepath)
            print(f"File {local_filename} uploaded to S3 successfully.")
        except Exception as e:
            print(f"Failed to upload {local_filename} to S3: {e}. Using local file for response.")
            # When running locally, replace the domain below with your Flask server address
            audio_url = local_filepath
        return audio_url
    
    def upload_file_to_s3(self, file_name, s3_file_path):
        try:
            self.s3_client.upload_file(file_name, S3_BUCKET_NAME, s3_file_path)
            print(f"File {file_name} uploaded to {s3_file_path}")
        except NoCredentialsError:
            print("Credentials not available")

    def generate_s3_url(self, s3_file_path):
        return f"https://{S3_BUCKET_NAME}.s3.amazonaws.com/{s3_file_path}"



recorder = MicrophoneRecorder()

language_mapping = {
            'tam': 'ta-IN',  # Tamil
            'eng': 'en-US',  # English
            'fre': 'fr-FR',  # French
            'jap': 'ja-JP',# Japanese
            'hin': 'hi-IN'  # hindi
            
        }

voice_map={
        'ta:IN' : 'ta-IN-Wavenet-D',
        'en-US' : 'en-US-Wavenet-D',
        'fr-FR' : 'fr-FR-Standard-D',
        'ja-JP' : 'ja-JP-Wavenet-D',
        'hi-IN' : 'hi-IN-Wavenet-D'
        }

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

@app.route('/')
def index():
    return render_template('indexm.html')

@app.route("/user")
def user():
    return render_template('user.html')

@app.route('/main')
def main():
    return render_template('main.html')


@app.route('/launch')
def launch():
    return render_template('main.html')


@app.route('/start', methods=['POST'])
def start():
    recorder.start_recording()
    return jsonify({'success': True})

# @app.route('/start', methods=['POST'])
# def start():
#     recorder.start_recording()
#     return jsonify({'success': True})

@app.route('/stop', methods=['POST'])
def stop():
    # Extract languages from the form data
    from_lang = request.form['from']
    to_lang = request.form['to']
    
    from_lang = language_mapping.get(from_lang)
    to_lang = language_mapping.get(to_lang)

    # Process the audio recording and respond with results
    transcribed_text, translated_text, emotion, audio_url, audio_emotion = recorder.stop_recording(from_lang, to_lang)

    print("Audio url:",audio_url)

    return jsonify({
        'success': True,
        'transcribed_text': transcribed_text,
        'translated_text': translated_text,
        'emotion': emotion,
        'audio_emotion':audio_emotion,
        'audio_url': audio_url
    })


if __name__ == "__main__":
    app.run(debug=True)
