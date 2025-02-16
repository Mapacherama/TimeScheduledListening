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
        response = model.generate_content(f"Suggest a Spotify playlist for someone feeling {mood}. suggest a relevant Spotify playlist that best matches their mood. " 
                                          "The response should be concise, including only the playlist's name and its Spotify URI, in the format: spotify:playlist:<playlist_id>. Ensure the playlist aligns with the "
                                          "user's current feelings, whether they seek motivation, relaxation, focus, or nostalgia.")

        playlist_suggestion = response.text.strip()
        return {"mood": mood, "suggested_playlist": playlist_suggestion}
    
    except Exception as e:
        logging.error(f"AI Playlist Generation Failed: {e}")
        return {"error": "Failed to generate playlist recommendation"}
    
def get_ai_podcast_recommendation(subject: str):
    """
    Uses Gemini AI to generate a podcast recommendation based on mood.
    """
    try:
        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(f"Suggest a podcast on Spotify for someone feeling {subject}. "
                                          "Ensure the recommendation is engaging, well-reviewed,"
                                          "and directly related to the chosen subject. Provide only the podcast’s name "
                                          "and its Spotify URL. Make sure that the podcast URL is correct and valid.")


        playlist_suggestion = response.text.strip()
        return {"subject": subject, "suggested_podcast": playlist_suggestion}
    

    except Exception as e:
        logging.error(f"AI Playlist Generation Failed: {e}")
        return {"error": "Failed to generate playlist recommendation"}    
