from flask import Flask, render_template, request, jsonify
import pyaudio
import wave
import threading
from datetime import datetime
from google.cloud import speech, translate_v2 as translate, texttospeech as tts
import os
import html
from transformers import pipeline

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

    def stop_recording(self, output_file, fromlang, tolang):
        if self.is_recording:
            self.is_recording = False
            self.stream.stop_stream()
            self.stream.close()
            transcribed_text, translated_text, emotion, aud_out = self.save_recording(output_file, fromlang, tolang)
        # print('hi')
        # print(transcribed_text, translated_text, emotion)
        return transcribed_text, translated_text, emotion, aud_out

    def save_recording(self, filename, fromlang, tolang):
        wf = wave.open(filename, 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(self.p.get_sample_size(pyaudio.paInt16))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(self.frames))
        wf.close()

        # Perform language detection and transcription
        transcribed_text = self.transcribe_audio(filename, fromlang)
        print("Transcribed Text:", transcribed_text)
        translated_text, emotext = self.trans_text(transcribed_text,tolang)
        print("Translated Text: ", translated_text)
        # print('hi')
        emotion = self.emotionlabel(emotext)
        aud_out = self.tts(translated_text, tolang, "static/extra_op", emotion)
        
        return transcribed_text, translated_text, emotion, aud_out


    def transcribe_audio(self, filename, fromlang):
        client = speech.SpeechClient()

        with open(filename, 'rb') as audio_file:
            content = audio_file.read()

        audio = speech.RecognitionAudio(content=content)
        config = speech.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=RATE,
            # language_code='en-US',
            language_code=fromlang,  # Change to appropriate language code
        )

        response = client.recognize(config=config, audio=audio)
        transcribed_text = ''
        for result in response.results:
            transcribed_text += result.alternatives[0].transcript
        
        return transcribed_text
    
    def trans_text(self, text, tolang):
        translate_client = translate.Client()

    # Translates the text into the target language
        translated_text = translate_client.translate(text, target_language=tolang)
        trans_text = html.unescape(translated_text['translatedText'])

        emotion_text = translate_client.translate(text, target_language='en-US')
        emo_text = html.unescape(emotion_text['translatedText'])

        return trans_text, emo_text
    
    def emotionlabel(self, emotext):
        emotion = emotions(emotext)
        print(emotion[0]['label'])
        return emotion[0]['label']
    
    def tts(self, text, tolang, out_dir, emotion):
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
    return render_template('extra.html')

@app.route('/start', methods=['POST'])
def start():
    recorder.start_recording()
    return jsonify({'success': True})

@app.route('/stop', methods=['POST'])
def stop():
    from_lang = request.form['from']
    to_lang = request.form['to']

    fromlang = language_mapping.get(from_lang)
    tolang = language_mapping.get(to_lang)
    print(fromlang,tolang)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    input_aud = f"ip_{timestamp}.wav"
    input_dir = os.path.join("static/extra_ip", input_aud)

    tscribe_text, tslate_text, emotion, out_aud = recorder.stop_recording(input_dir, fromlang, tolang)
    # print( tscribe_text, tslate_text, emotion)
    return jsonify({
        'success': True,
        'tscribed_text': tscribe_text,
        'tslated_text': tslate_text,
        'emotion': emotion,
        'audio': out_aud  # Assuming this is the filename of the audio file
    })
if __name__ == "__main__":
    app.run(debug=True)
