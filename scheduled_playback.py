from fastapi import FastAPI, Request, HTTPException, Query
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import os
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import asyncio
import time
import logging
from requests.exceptions import ConnectionError
import urllib3

app = FastAPI()

scheduler = BackgroundScheduler()

sp_oauth = SpotifyOAuth(client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                        scope="user-modify-playback-state")

token_store = {}
TOKEN_FILE_PATH = "token_info.json"

def save_token_info(token_info):
    token_store['token_info'] = token_info
    with open(TOKEN_FILE_PATH, 'w') as f:
        json.dump(token_info, f)

def load_token_info():
    if 'token_info' in token_store:
        return token_store['token_info']
    if os.path.exists(TOKEN_FILE_PATH):
        with open(TOKEN_FILE_PATH, 'r') as f:
            token_info = json.load(f)
            token_store['token_info'] = token_info
            return token_info
    return None

token_info = None
sp = None

@app.get("/login")
def login():
    token_info = load_token_info()
    if token_info:
        return {"message": "Already authenticated", "token_info": token_info}
    auth_url = sp_oauth.get_authorize_url()
    return {"auth_url": auth_url}

@app.get("/callback")
def callback(request: Request):
    global sp
    code = request.query_params.get('code')
    if not code:
        raise HTTPException(status_code=400, detail="Authorization failed or denied.")
    token_info = sp_oauth.get_access_token(code)
    save_token_info(token_info)
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_info = sp.current_user()
    return {"user_info": user_info}

def refresh_token_if_needed(retry_count=3, delay=5):
    global sp
    token_info = load_token_info()
    if token_info is None:
        raise Exception("Token info is not initialized. Please authenticate first.")
    
    # Check if the token is expired
    if sp_oauth.is_token_expired(token_info):
        for attempt in range(retry_count):
            try:
                # Try to refresh the token
                token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                save_token_info(token_info)
                sp = spotipy.Spotify(auth=token_info['access_token'])
                logging.info("Token refreshed successfully.")
                break  # Exit the retry loop if successful
            except (ConnectionError, urllib3.exceptions.ProtocolError, urllib3.exceptions.MaxRetryError) as e:
                logging.error(f"Failed to refresh token: {str(e)}")
                if attempt < retry_count - 1:
                    # Wait before retrying
                    time.sleep(delay * (2 ** attempt))  # Exponential backoff
                else:
                    logging.error("Max retry attempts reached. Token refresh failed.")
                    raise

def play_playlist(playlist_uri):
    global sp
    refresh_token_if_needed()
    if not sp:
        raise Exception("Spotify client is not initialized")
    sp.start_playback(context_uri=playlist_uri)
    print(f"Started playback for {playlist_uri}")

@app.get("/schedule-playlist")
def schedule_playlist(playlist_uri: str, play_time: str = Query(..., regex="^([0-9]{2}):([0-9]{2})$")):
    now = datetime.now()
    play_time_obj = datetime.strptime(play_time, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )
    if play_time_obj < now:
        play_time_obj = play_time_obj.replace(day=now.day + 1)
    trigger = DateTrigger(run_date=play_time_obj)
    scheduler.add_job(play_playlist, trigger, args=[playlist_uri])
    return {
        "message": f"Playlist {playlist_uri} scheduled to play at {play_time_obj.strftime('%Y-%m-%d %H:%M:%S')}"
    }

def periodic_token_refresh():
    refresh_token_if_needed()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown(wait=False)
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        if not task.cancelled():
            task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

@app.on_event("startup")
def startup_event():
    scheduler.start()
    scheduler.add_job(periodic_token_refresh, 'interval', minutes=45)
