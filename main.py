from fastapi import FastAPI, Request, Query, HTTPException
from contextlib import asynccontextmanager
from uvicorn import run
from ai import get_ai_playlist_recommendation, get_ai_podcast_recommendation
from auth import callback, login
from scheduled_playback import (
    refresh_token_if_needed,
    play_playlist
)
from scheduler import schedule_playlist, start_scheduler, stop_scheduler
from podcast import search_podcast
import logging

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
async def login_route():
    try:
        return await login()
    except Exception as e:
        logging.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.get("/callback")
async def callback_route(request: Request):
    try:
        return await callback(request)
    except Exception as e:
        logging.error(f"Error during callback: {e}")
        raise HTTPException(status_code=500, detail="Callback failed")

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

if __name__ == "__main__":
    run("main:app", host="0.0.0.0", port=8000, reload=True)