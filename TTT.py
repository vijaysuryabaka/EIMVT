<<<<<<< HEAD
from translate import Translator
from langdetect import detect

language_mapping = {
    'afrikaans': 'af',
    'albanian': 'sq',
    'amharic': 'am',
    'arabic': 'ar',
    'armenian': 'hy',
    'azerbaijani': 'az',
    'basque': 'eu',
    'belarusian': 'be',
    'bengali': 'bn',
    'bosnian': 'bs',
    'bulgarian': 'bg',
    'catalan': 'ca',
    'cebuano': 'ceb',
    'chichewa': 'ny',
    'chinese (simplified)': 'zh-cn',
    'chinese (traditional)': 'zh-tw',
    'corsican': 'co',
    'croatian': 'hr',
    'czech': 'cs',
    'danish': 'da',
    'dutch': 'nl',
    'english': 'en',
    'esperanto': 'eo',
    'estonian': 'et',
    'filipino': 'tl',
    'finnish': 'fi',
    'french': 'fr',
    'frisian': 'fy',
    'galician': 'gl',
    'georgian': 'ka',
    'german': 'de',
    'greek': 'el',
    'gujarati': 'gu',
    'haitian creole': 'ht',
    'hausa': 'ha',
    'hawaiian': 'haw',
    'hebrew': 'iw',
    'hindi': 'hi',
    'hmong': 'hmn',
    'hungarian': 'hu',
    'icelandic': 'is',
    'igbo': 'ig',
    'indonesian': 'id',
    'irish': 'ga',
    'italian': 'it',
    'japanese': 'ja',
    'javanese': 'jw',
    'kannada': 'kn',
    'kazakh': 'kk',
    'khmer': 'km',
    'korean': 'ko',
    'kurdish (kurmanji)': 'ku',
    'kyrgyz': 'ky',
    'lao': 'lo',
    'latin': 'la',
    'latvian': 'lv',
    'lithuanian': 'lt',
    'luxembourgish': 'lb',
    'macedonian': 'mk',
    'malagasy': 'mg',
    'malay': 'ms',
    'malayalam': 'ml',
    'maltese': 'mt',
    'maori': 'mi',
    'marathi': 'mr',
    'mongolian': 'mn',
    'myanmar (burmese)': 'my',
    'nepali': 'ne',
    'norwegian': 'no',
    'odia': 'or',
    'pashto': 'ps',
    'persian': 'fa',
    'polish': 'pl',
    'portuguese': 'pt',
    'punjabi': 'pa',
    'romanian': 'ro',
    'russian': 'ru',
    'samoan': 'sm',
    'scots gaelic': 'gd',
    'serbian': 'sr',
    'sesotho': 'st',
    'shona': 'sn',
    'sindhi': 'sd',
    'sinhala': 'si',
    'slovak': 'sk',
    'slovenian': 'sl',
    'somali': 'so',
    'spanish': 'es',
    'sundanese': 'su',
    'swahili': 'sw',
    'swedish': 'sv',
    'tajik': 'tg',
    'tamil': 'ta',
    'telugu': 'te',
    'thai': 'th',
    'turkish': 'tr',
    'ukrainian': 'uk',
    'urdu': 'ur',
    'uyghur': 'ug',
    'uzbek': 'uz',
    'vietnamese': 'vi',
    'welsh': 'cy',
    'xhosa': 'xh',
    'yiddish': 'yi',
    'yoruba': 'yo',
    'zulu': 'zu',
}

def detect_language(text):
    try:
        language_code = detect(text)
        return language_code
    except Exception as e:
        print(f"Error during language detection: {e}")
        return None

if __name__ == "__main__":
    in_text = input("Enter the text you want to translate: ")
    source_language = detect_language(in_text)
    if source_language:
        tar_txt = input("Enter the translating language: ")
        target_code = language_mapping.get(tar_txt.lower())
        if target_code:
            translator = Translator(from_lang=source_language, to_lang=target_code)
            translation = translator.translate(in_text)
            print("Original Text:", in_text)
            print("Translated Text:", translation)
        else:
            print("Invalid target language.")
    else:
        print("Language detection failed.")
=======
import os
import pyaudio
from google.cloud import speech

# Path to your Google Cloud credentials JSON file
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "tribal-booth-414608-dbc61449795a.json"

# Audio recording parameters
RATE = 16000
CHUNK = int(RATE / 10)  # 100ms

def listen_and_transcribe():
    client = speech.SpeechClient()
    
    # Configure the request with language detection
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=RATE,
        language_code="en-US",  # Default fallback language
        # Assuming the API or future updates might allow broader automatic detection
        # This setup specifies a wide range of languages as alternatives
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
    
>>>>>>> 4bde838 (Speech to Text (Google api))
