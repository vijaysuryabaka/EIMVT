from google.cloud import texttospeech
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "tribal-booth-414608-dbc61449795a.json"

def list_voices():
    client = texttospeech.TextToSpeechClient()

    # Perform the list voices request
    response = client.list_voices()

    # Display the voices
    for voice in response.voices:
        print(f"Name: {voice.name}")
        print(f"Language codes: {voice.language_codes}")
        print(f"SSML gender: {texttospeech.SsmlVoiceGender(voice.ssml_gender).name}")
        print(f"Natural sample rate hertz: {voice.natural_sample_rate_hertz}\n")

if __name__ == "__main__":
    list_voices()
