from datetime import datetime
from fastapi import FastAPI, Request, Query, HTTPException
from contextlib import asynccontextmanager
from uvicorn import run
from ai import get_ai_playlist_recommendation, get_ai_podcast_recommendation
from auth import callback as auth_callback
from scheduled_playback import (
    get_spotify_playlists,
    get_time_based_mood,
    initialize_spotify_client,
    play_playlist,
    sp_oauth
)
from scheduler import schedule_playlist, start_scheduler, stop_scheduler
from podcast import search_podcast
import logging

# Import from spotify_client instead of scheduled_playback
from spotify_client import clear_token_info, save_token_info, refresh_token_if_needed

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

    # Use the same refresh_token_if_needed function
    token_info = refresh_token_if_needed()
    if token_info:
        logging.info("Token information found. User is already authenticated.")
        return {"message": "Already authenticated", "token_info": token_info}

    # If no valid token, request a new one
    auth_url = sp_oauth.get_authorize_url()
    logging.info(f"Auth URL generated: {auth_url}")

    return {"auth_url": auth_url}

@app.get("/logout")
def logout():
    """
    Clears stored Spotify authentication tokens and forces user to log in again.
    """
    clear_token_info()
    logging.info("✅ User logged out successfully.")
    return {"message": "Logged out successfully"}

@app.get("/callback")
async def callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(status_code=400, detail="Authorization code not provided")

    token_info = sp_oauth.get_access_token(code)
    token_info["expires_at"] = datetime.now().timestamp() + token_info["expires_in"]

    save_token_info(token_info) 

    return await auth_callback(request)

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

@app.get("/force-login")
def force_login():
    """
    Forces a new login by clearing all stored tokens.
    Use this when you get 'Refresh token revoked' errors.
    """
    clear_token_info()
    logging.info("✅ All tokens cleared. User must re-authenticate.")
    
    # Generate new auth URL
    auth_url = sp_oauth.get_authorize_url()
    return {"message": "Please re-authenticate", "auth_url": auth_url}

@app.get("/auth-status")
def auth_status():
    """
    Check the current authentication status and return appropriate action.
    """
    # Use the refresh_token_if_needed from spotify_client
    token_info = refresh_token_if_needed()
    if token_info:
        return {
            "status": "authenticated",
            "message": "User is authenticated",
            "expires_at": token_info.get("expires_at")
        }
    else:
        auth_url = sp_oauth.get_authorize_url()
        return {
            "status": "unauthenticated", 
            "message": "User needs to authenticate",
            "auth_url": auth_url
        }

@app.get("/debug-token")
def debug_token():
    """
    Debug endpoint to check token file and status.
    """
    import os
    from spotify_client import load_token_info
    
    token_file_exists = os.path.exists("token_info.json")
    token_info = load_token_info()
    
    if token_file_exists:
        file_size = os.path.getsize("token_info.json")
        try:
            with open("token_info.json", 'r') as f:
                file_content = f.read()
        except Exception as e:
            file_content = f"Error reading file: {e}"
    else:
        file_size = 0
        file_content = "File does not exist"
    
    return {
        "token_file_exists": token_file_exists,
        "file_size": file_size,
        "token_info_loaded": token_info is not None,
        "token_info_keys": list(token_info.keys()) if token_info else None,
        "file_content_preview": file_content[:200] + "..." if len(file_content) > 200 else file_content,
        "current_time": time.time()
    }

if __name__ == "__main__":
    run("main:app", host="0.0.0.0", port=8000, reload=True)