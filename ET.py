from transformers import pipeline
emotion = pipeline('sentiment-analysis', model='arpanghoshal/EmoRoBERTa')
emotion_labels = emotion("iam so glad that i met you")
print(emotion_labels)