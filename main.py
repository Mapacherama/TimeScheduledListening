from sched import scheduler
from fastapi import FastAPI, Request, Query
from uvicorn import run
from auth import callback, login
from podcast import search_podcast
from scheduled_playback import (
    initialize_spotify_client,
    refresh_token_if_needed,
    play_playlist
)
import logging
from scheduler import schedule_playlist

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.get("/login")
async def login_route():
    return await login() 

@app.get("/callback")
async def callback_route(request: Request):
    return await callback(request)

@app.get("/schedule-playlist")
def schedule_playlist_route(playlist_uri: str, play_time: str = Query(..., regex="^([0-9]{2}):([0-9]{2})$")):
    return schedule_playlist(scheduler, play_playlist, playlist_uri, play_time)

@app.get("/search-podcast")
def search_podcast_route(query: str):
    global sp
    return search_podcast(sp, refresh_token_if_needed, query) 

@app.on_event("startup")
def startup_event():
    initialize_spotify_client()

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Shutdown event triggered.")
    scheduler.shutdown(wait=False)

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000, reload=True)