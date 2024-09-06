from fastapi import FastAPI, Request, HTTPException, Query
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime

# Initialize the app
app = FastAPI()

# Initialize APScheduler
scheduler = BackgroundScheduler()

# Setup Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                        scope="user-modify-playback-state")

# In-memory token storage
token_store = {}

def save_token_info(token_info):
    token_store['token_info'] = token_info

def load_token_info():
    return token_store.get('token_info')

token_info = None
sp = None

@app.get("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return {"auth_url": auth_url}

@app.get("/callback")
def callback(request: Request):
    global sp
    code = request.query_params.get('code')
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization failed or denied.")
    
    token_info = sp_oauth.get_access_token(code)
    save_token_info(token_info)  # Save token info in memory
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_info = sp.current_user()
    
    return {"user_info": user_info}

def refresh_token_if_needed():
    global sp
    token_info = load_token_info()  # Load token info from memory
    
    if token_info is None:
        raise Exception("Token info is not initialized. Please authenticate first.")
    
    if sp_oauth.is_token_expired(token_info):
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        save_token_info(token_info)  # Save the refreshed token
        sp = spotipy.Spotify(auth=token_info['access_token'])

def play_playlist(playlist_uri):
    global sp
    try:
        # Refresh token if needed
        refresh_token_if_needed()

        if sp:
            sp.start_playback(context_uri=playlist_uri)
            print(f"Started playback for {playlist_uri}")
        else:
            print("Spotify client is not initialized")
    except Exception as e:
        print(f"Error in play_playlist: {e}")

@app.get("/schedule-playlist")
def schedule_playlist(playlist_uri: str, play_time: str = Query(..., regex="^([0-9]{2}):([0-9]{2})$")):
    """
    Schedule a playlist to start playing at a specified time (HH:MM format).
    """
    try:
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
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Ensure the scheduler shuts down properly on application exit
@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

# Start the scheduler when the app starts
@app.on_event("startup")
def startup_event():
    scheduler.start()
