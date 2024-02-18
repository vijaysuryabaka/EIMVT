import openai
#key is edited
openai.api_key = 'sk-....KQbeBQzwylvL'

def translator(source_text, source_language,  target_language):

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo", 
        messages=[
            {"role": "system", "content": "You are a highly intelligent translator that maintains the emotional tone, nuances, and sarcasm of the source text."},
            {"role": "user", "content": f"Translate this from {source_language} to {target_language}: '{source_text}'"}
        ]
    )

    
    return response.choices[0].message['content']

# Example 
source_text = "I'm not sure if I should be amazed or worried by how smart these AI models are becoming."
translated_text = translator(source_text, "English", "tamil")
print(translated_text)
