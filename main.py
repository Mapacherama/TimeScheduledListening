from fastapi import FastAPI, Request, Query, HTTPException
from contextlib import asynccontextmanager
from uvicorn import run
from ai import get_ai_playlist_recommendation, get_ai_podcast_recommendation
from auth import callback
from scheduled_playback import (
    get_spotify_playlists,
    get_time_based_mood,
    initialize_spotify_client,
    refresh_token_if_needed,
    play_playlist,
    sp_oauth
)
from scheduler import schedule_playlist, start_scheduler, stop_scheduler
from podcast import search_podcast
import logging

from spotify_client import save_token_info

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    start_scheduler()
    yield
    # Shutdown
    stop_scheduler()

app = FastAPI(lifespan=lifespan)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sp = None 

@app.get("/login")
async def login():
    logging.info("Login endpoint accessed.")

    # Check if a valid token already exists
    token_info = refresh_token_if_needed()
    if token_info:
        logging.info("Token information found. User is already authenticated.")
        return {"message": "Already authenticated", "token_info": token_info}

    # If no valid token, request a new one
    auth_url = sp_oauth.get_authorize_url()
    logging.info(f"Auth URL generated: {auth_url}")

    return {"auth_url": auth_url}

@app.get("/callback")
async def callback(request: Request):
    logging.info("🚀 Callback endpoint accessed.")

    code = request.query_params.get("code")
    if not code:
        logging.error("❌ Authorization failed: No code received.")
        raise HTTPException(status_code=400, detail="Authorization failed or denied.")

    try:
        logging.info("🔄 Attempting to exchange authorization code for token...")

        # Exchange authorization code for access token
        token_info = sp_oauth.get_access_token(code)
        logging.info(f"✅ Token received: {token_info}")

        # Save the token
        save_token_info(token_info)

        # Initialize Spotify client with the new token
        initialize_spotify_client()
        logging.info("✅ Spotify authentication successful. Client initialized.")

        return {"message": "Authentication successful!", "token_info": token_info}

    except Exception as e:
        logging.error(f"❌ Error during callback: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")


@app.get("/schedule-playlist")
def schedule_playlist_route(playlist_uri: str, play_time: str = Query(..., pattern="^([0-9]{2}):([0-9]{2})$")):
    try:
        return schedule_playlist(play_playlist, playlist_uri, play_time)
    except Exception as e:
        logging.error(f"Error scheduling playlist: {e}")
        raise HTTPException(status_code=500, detail="Scheduling failed")

@app.get("/ai-playlist")
def ai_playlist_route(mood: str):
    """
    Fetches an AI-generated playlist recommendation based on mood.
    Falls back to Spotify's curated playlists if AI fails.
    """
    try:
        ai_playlist = get_ai_playlist_recommendation(mood)
        if not ai_playlist:
            logging.warning(f"AI failed for mood '{mood}', falling back to Spotify.")
            return get_spotify_playlists(mood)

        return ai_playlist
    except Exception as e:
        logging.error(f"AI Playlist Request Failed: {e}, using Spotify instead.")
        return get_spotify_playlists(mood)
    
@app.get("/ai-podcast")
def ai_podcast_route(subject: str):
    """
    Fetches an AI-generated podcast recommendation based on subject.
    """
    try:
        return get_ai_podcast_recommendation(subject)
    except Exception as e:
        logging.error(f"AI Podcast Request Failed: {e}")
        raise HTTPException(status_code=500, detail="AI Podcast Request Failed")

@app.get("/search-podcast")
def search_podcast_route(query: str):

    global sp
    try:
        return search_podcast(sp, refresh_token_if_needed, query)
    except Exception as e:
        logging.error(f"Error searching podcast: {e}")
        raise HTTPException(status_code=500, detail="Podcast search failed")   
    
@app.get("/mood-playlist")
def mood_playlist_route():
    """
    Automatically selects a playlist based on the time of day.
    Falls back to Spotify if AI fails.
    """
    mood = get_time_based_mood()
    logging.info(f"Selected mood: {mood}")

    try:
        # Try AI-based recommendation first
        ai_playlist = get_ai_playlist_recommendation(mood)
        if ai_playlist:
            return ai_playlist

        # If AI fails, fallback to Spotify's curated playlists
        logging.warning(f"AI failed for mood '{mood}', falling back to Spotify.")
        return get_spotify_playlists(mood)

    except Exception as e:
        logging.error(f"Error fetching mood-based playlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch mood-based playlist")

if __name__ == "__main__":
    run("main:app", host="0.0.0.0", port=8000, reload=True)