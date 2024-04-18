# 2024-Emotion-Intelligent-Multilingual-Voice-Translator
Emotion-Intelligent Multilingual Voice Translator - https://idea.unisys.com/UIP7272
## EIMVT - Emotional Intelligence Multi-lingual Voice Translation

EIMVT is a powerful tool that enables one-on-one voice translation interactions with emotional intelligence. It facilitates seamless communication between individuals speaking different languages, preserving emotional nuances in their voices.

### Description
EIMVT integrates cutting-edge voice translation, emotion analysis, and voice cloning technologies. It analyzes emotional aspects in users' input voices, translates them into the desired language, and ensures the translated output reflects the authentic emotional expression of the user.

### Installation
To install EIMVT, follow these steps:

1. Clone the GitHub repository:
   ```
   git clone https://github.com/vijaysuryabaka/EIMVT
   ```
   
2. Install the required packages:
   ```
   pip install boto3 pyaudio flask google-cloud-speech google-cloud-texttospeech google-cloud-translate transformers requests pymongo
   ```

3. Connect to the required APIs:
- Gemini API
- Google Cloud API

4. Run the code:
   ```
   python main.py
   ```
   
### Important Packages
- `flask`: Web framework for the backend server.
- `google-cloud-speech`, `google-cloud-texttospeech`, `google-cloud-translate`: Google Cloud APIs for speech recognition, text-to-speech conversion, and translation.
- `transformers`: Library for natural language processing tasks.
- `requests`: HTTP library for making API requests.
- `pymongo`: MongoDB driver for Python.

Ensure that the necessary credentials and configurations are set up for the APIs to function properly.

### Note
Before running the code, make sure to set up authentication for accessing the required APIs and ensure that the Gemini API is accessible.

Now, you're ready to experience the seamless voice translation capabilities of EIMVT!



