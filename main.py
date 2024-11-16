from fastapi import FastAPI, Request, HTTPException, Query
from uvicorn import run
from auth import callback, login
from scheduled_playback import (
    initialize_spotify_client,
    refresh_token_if_needed,
    play_playlist,
    sp_oauth
)
from scheduler import schedule_playlist, start_scheduler, stop_scheduler
from podcast import search_podcast
import logging

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.on_event("startup")
def startup_event():
    start_scheduler()

@app.get("/login")
async def login_route():
    return await login() 

@app.get("/callback")
async def callback_route(request: Request):
    return await callback(request)

@app.get("/schedule-playlist")
def schedule_playlist_route(playlist_uri: str, play_time: str = Query(..., regex="^([0-9]{2}):([0-9]{2})$")):
    return schedule_playlist(play_playlist, playlist_uri, play_time)

@app.get("/search-podcast")
def search_podcast_route(query: str):
    global sp
    return search_podcast(sp, refresh_token_if_needed, query)

@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000, reload=True)