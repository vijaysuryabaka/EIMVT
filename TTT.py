import os
import pyaudio
from google.cloud import speech

# Path to your Google Cloud credentials JSON file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "tribal-booth-414608-dbc61449795a.json"


RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

def listen_and_transcribe():
    client = speech.SpeechClient()
    
    # Configure the request with language detection
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",  # Default fallback language
        alternative_language_codes=['es-ES', 'fr-FR', 'de-DE', 'hi-IN', 'ar-SA', 'zh-CN', 'ru-RU', 'ja-JP', 'pt-PT', 'it-IT','ta-IN'],
    )
    streaming_config = speech.StreamingRecognitionConfig(
        config=config,
        interim_results=True
    )

    # Initialize PyAudio
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    def stream_generator():
        while True:
            data = stream.read(CHUNK)
            yield speech.StreamingRecognizeRequest(audio_content=data)
    
    requests = stream_generator()

    print("Listening...")
    responses = client.streaming_recognize(streaming_config, requests)

    # Process responses
    for response in responses:
        for result in response.results:
            if result.is_final:
                transcript = result.alternatives[0].transcript
                detected_language = result.language_code
                print(f"Detected language: {detected_language}")
                print(f"Transcript: {transcript}")

    stream.stop_stream()
    stream.close()
    p.terminate()

listen_and_transcribe()
