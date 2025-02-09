import google.generativeai as genai
import os
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure Gemini API Key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

def get_ai_playlist_recommendation(mood: str):
    """
    Uses Gemini AI to generate a playlist recommendation based on mood.
    """
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(f"Suggest a Spotify playlist for someone feeling {mood}. Make it concise, and return the URI of the playlist.")

        playlist_suggestion = response.text.strip()
        return {"mood": mood, "suggested_playlist": playlist_suggestion}
    
    except Exception as e:
        logging.error(f"AI Playlist Generation Failed: {e}")
        return {"error": "Failed to generate playlist recommendation"}
