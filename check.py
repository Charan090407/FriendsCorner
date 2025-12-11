import google.generativeai as genai

API_KEY = "AIzaSyBqsfzRQ5YqXSeiNvwCnE2cGzgretLfZWE"

def test_gemini_key(api_key):
    try:
        genai.configure(api_key=api_key)

        # Try a simple model call
        model = genai.GenerativeModel("gemini-2.5-flash")
        response = model.generate_content("Hello! Just testing the API key.")

        print("API key is valid!")
        print("Response:", response.text)

    except Exception as e:
        print("API key is INVALID or an error occurred.")
        print("Error:", str(e))

if __name__ == "__main__":
    test_gemini_key(API_KEY)
