import google.generativeai as genai

# Configure the API key (replace with your actual API key)
genai.configure(api_key="AIzaSyB-f-KRov7a3KxB7Dqon3kpoTWGwEUld9E")

# Create a GenerativeModel object with the desired model
model = genai.GenerativeModel('gemini-pro')
sour_lan = "english"
tra_lan = "tamil"

def extract_meaning(text,tra_lan):
  """
  Extracts meaning from the provided text and attempts to generate a sentence in the target language.

  Args:
      text: The text to understand and potentially translate/rephrase.

  Returns:
      A string containing the extracted meaning or an informative message if no content is generated.
  """

  prompts = [
    f"For the sentence: {text}, you want to understand the meaning of the sentence and generate a similar sentence in {tra_lan}?"
  ]

  for prompt in prompts:
      response = model.generate_content(prompt)

      # Check if the response contains any candidates
      if response._result.candidates:
          # Extract the meaning from the response (assuming first candidate)
          meaning = response._result.candidates[0].content.parts[0].text
          return meaning

  # If no prompt generates candidates, return an informative message
  return "Model did not generate any response for this sentence."

def main():
  # Example usage
  text = input("Enter the text: ")
  meaning = extract_meaning(text)
  print(meaning)

if __name__ == "__main__":
  main()
