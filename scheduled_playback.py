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

def initialize_spotify_client():
    global sp
    token_info = load_token_info()
    if token_info and not sp_oauth.is_token_expired(token_info):
        sp = spotipy.Spotify(auth=token_info['access_token'])
    else:
        sp = None

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

def refresh_token_if_needed(retry_count=5, delay=5):
    global sp
    token_info = load_token_info()
    if token_info is None:
        raise Exception("Token info is not initialized. Please authenticate first.")
    if sp_oauth.is_token_expired(token_info):
        for attempt in range(retry_count):
            try:
                token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
                save_token_info(token_info)
                sp = spotipy.Spotify(auth=token_info['access_token'])
                logging.info("Token refreshed successfully.")
                break
            except (ConnectionError, urllib3.exceptions.ProtocolError, urllib3.exceptions.MaxRetryError, urllib3.exceptions.NewConnectionError, urllib3.exceptions.HTTPError) as e:
                logging.error(f"Failed to refresh token: {str(e)}")
                if attempt < retry_count - 1:
                    time.sleep(delay * (2 ** attempt))
                else:
                    logging.error("Max retry attempts reached. Token refresh failed.")
                    raise
    else:
        sp = spotipy.Spotify(auth=token_info['access_token'])

def play_playlist(playlist_uri, retry_count=3, delay=5):
    global sp
    refresh_token_if_needed()
    if not sp:
        raise Exception("Spotify client is not initialized")

    for attempt in range(retry_count):
        try:
            if playlist_uri.startswith("spotify:playlist:") or playlist_uri.startswith("spotify:album:") or playlist_uri.startswith("spotify:artist:"):
                sp.start_playback(context_uri=playlist_uri)
            else:
                sp.start_playback(uris=[playlist_uri])

            logging.info(f"Started playback for {playlist_uri}")
            break
        except (ConnectionError, urllib3.exceptions.ProtocolError, urllib3.exceptions.MaxRetryError, spotipy.exceptions.SpotifyException) as e:
            logging.error(f"Failed to start playback: {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(delay * (2 ** attempt))
            else:
                logging.error("Max retry attempts reached. Playback failed.")
                raise

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

@app.get("/search-podcast")
def search_podcast(query: str):
    refresh_token_if_needed()
    if not sp:
        raise HTTPException(status_code=500, detail="Spotify client is not initialized")

    try:
        search_results = sp.search(q=query, type="show", limit=5)
        podcasts = search_results.get('shows', {}).get('items', [])
        if not podcasts:
            return {"message": "No podcasts found for the query."}

        podcast_list = [{
            "name": podcast['name'],
            "description": podcast['description'],
            "url": podcast['external_urls']['spotify']
        } for podcast in podcasts]

        return {"podcasts": podcast_list}

    except spotipy.exceptions.SpotifyException as e:
        logging.error(f"Spotify API error: {str(e)}")
        raise HTTPException(status_code=500, detail="Spotify API error")

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
    initialize_spotify_client()
    scheduler.start()
    scheduler.add_job(periodic_token_refresh, 'interval', minutes=45)
