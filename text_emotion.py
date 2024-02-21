from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch

# Load the tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("xlm-roberta-base")
model = AutoModelForSequenceClassification.from_pretrained("xlm-roberta-base")

# Function to predict emotion
def detect_emotion(text):
    # Preprocess the text
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    
    # Predict
    with torch.no_grad():
        logits = model(**inputs).logits
    
    # Convert logits to probabilities (optional, depending on your model)
    probabilities = torch.softmax(logits, dim=1)
    
    # Assuming you have a mapping of model outputs to emotions
    # emotion = map_prediction_to_emotion(probabilities)
    # return emotion

    return probabilities # Or your mapped emotion

# Example usage
text = "i am so happy, that i feel like flying in sky" # Example in French
emotion = detect_emotion(text)
print(emotion)
