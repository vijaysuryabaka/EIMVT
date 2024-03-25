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

# Configure your S3 bucket name
S3_BUCKET_NAME = 'audioemo'


emotions = pipeline('sentiment-analysis', model='arpanghoshal/EmoRoBERTa')

app = Flask(__name__)
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

        # Only pass the filename to save_recording as fromlang and tolang are not used there
        self.save_recording(filename)

        # Upload to S3 and delete the local file
        s3_input_path = f"{filename}"
        
        try:
            self.s3_client.upload_file(filename, S3_BUCKET_NAME, s3_input_path)
            print(f"File {filename} uploaded to {s3_input_path} successfully.")
            os.remove(filename)
        except Exception as e:
            print(f"Failed to upload {filename} to S3: {e}")


        # Process the recording using the file directly from S3
        transcribed_text = self.transcribe_audio(s3_input_path, fromlang)
        translated_text, emotext = self.trans_text(transcribed_text, tolang)
        emotion = self.emotionlabel(emotext)
        s3_output_path = self.tts(translated_text, tolang, emotion, "templates")

        # Generate and return the S3 URL of the output audio
        output_url = self.generate_s3_url(s3_output_path)
        return transcribed_text, translated_text, emotion, output_url

    def save_recording(self, filename):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()


    def transcribe_audio(self, s3_input_path, fromlang):
        # Assuming s3_input_path is the full S3 object key
        filename = s3_input_path.split('/')[-1]  # Extract filename from path
        local_file_path = f"./{filename}"

        # Check if file exists locally, if not, download
        if not os.path.exists(local_file_path):
            try:
                self.s3_client.download_file(S3_BUCKET_NAME, s3_input_path, local_file_path)
                print(f"Downloaded {s3_input_path} from S3 for processing.")
            except Exception as e:
                print(f"Failed to download {s3_input_path} from S3: {e}")
                return ""

        # Now the file should be locally available; read its content
        with open(local_file_path, 'rb') as audio_file:
            content = audio_file.read()

        # Initialize the Google Cloud Speech client
        client = speech.SpeechClient()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            language_code=fromlang,  # Change to appropriate language code
        )

        # Attempt to recognize the speech in the audio file
        try:
            response = client.recognize(config=config, audio=audio)
            transcribed_text = ''
            for result in response.results:
                transcribed_text += result.alternatives[0].transcript
        except Exception as e:
            print(f"Error during transcription: {e}")
            transcribed_text = ""

        # Optionally delete the local file if no longer needed
        os.remove(local_file_path)
        print("Transcribed Text:",transcribed_text)
        
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
    
    def tts(self, text, tolang, emotion, out_dir="/templates",):
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

        #  Generate a unique filename using UUID
        # output_file = str(uuid.uuid4()) + ".mp3"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"op_{timestamp}.mp3"
        
        output_path = os.path.join(out_dir, output_file)

        with open(output_path, "wb") as out:
            out.write(response.audio_content)
            print(f'Audio content written to "{output_path}"')

        return output_path
    
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

@app.route('/main')
def main():
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
    transcribed_text, translated_text, emotion, audio_url = recorder.stop_recording(from_lang, to_lang)

    print("Audio url:",audio_url)

    return jsonify({
        'success': True,
        'transcribed_text': transcribed_text,
        'translated_text': translated_text,
        'emotion': emotion,
        'audio_url': audio_url
    })


if __name__ == "__main__":
    app.run(debug=True)
