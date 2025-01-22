from fastapi import FastAPI, Request, Query, HTTPException
from contextlib import asynccontextmanager
from uvicorn import run
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