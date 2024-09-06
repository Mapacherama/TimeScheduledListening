from fastapi import FastAPI, Request, HTTPException, Query
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import os
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import pytz  # for timezone handling

app = FastAPI()

sp_oauth = SpotifyOAuth(client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                        scope="user-modify-playback-state")

token_info = None
sp = None

scheduler = BackgroundScheduler()
scheduler.start()

# Define the time zone
timezone = pytz.timezone('Europe/London')  # Change this to your desired time zone

@app.get("/login")
def login():
    auth_url = sp_oauth.get_authorize_url()
    return {"auth_url": auth_url}

@app.get("/callback")
def callback(request: Request):
    global token_info, sp
    code = request.query_params.get('code')
    
    if not code:
        raise HTTPException(status_code=400, detail="Authorization failed or denied.")
    
    token_info = sp_oauth.get_access_token(code)
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    user_info = sp.current_user()
    
    return {"user_info": user_info}

def play_playlist(playlist_uri):
    global sp
    if sp:
        sp.start_playback(context_uri=playlist_uri)
    else:
        print("Spotify client is not initialized")


@app.get("/schedule-playlist")
def schedule_playlist(playlist_uri: str, play_time: str = Query(..., regex="^([0-9]{2}):([0-9]{2})$")):
    """
    Schedule a playlist to start playing at a specified time (HH:MM format).
    """
    try:
        now = datetime.now(timezone)
        play_time_obj = datetime.strptime(play_time, "%H:%M").replace(
            year=now.year, month=now.month, day=now.day, tzinfo=timezone
        )
        
        if play_time_obj < now:
            play_time_obj = play_time_obj.replace(day=now.day + 1)
        
        scheduler.add_job(play_playlist, 'date', run_date=play_time_obj, args=[playlist_uri])
        
        return {
            "message": f"Playlist {playlist_uri} scheduled to play at {play_time_obj.strftime('%Y-%m-%d %H:%M:%S')}"
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()
