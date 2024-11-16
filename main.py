from sched import scheduler
from fastapi import FastAPI, Request, HTTPException, Query
from uvicorn import run
from scheduled_playback import (
    save_token_info,
    load_token_info,
    initialize_spotify_client,
    refresh_token_if_needed,
    play_playlist,
    sp_oauth
)
import logging
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import spotipy

app = FastAPI()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.get("/login")
def login():
    logging.info("Login endpoint accessed.")
    token_info = load_token_info()
    if token_info:
        logging.info("Token information found. User is already authenticated.")
        return {"message": "Already authenticated", "token_info": token_info}
    
    auth_url = sp_oauth.get_authorize_url()
    logging.info(f"Auth URL generated: {auth_url}")
    return {"auth_url": auth_url}

@app.get("/callback")
def callback(request: Request):
    logging.info("Callback endpoint accessed.")
    code = request.query_params.get('code')
    if not code:
        logging.error("Authorization failed: No code received.")
        raise HTTPException(status_code=400, detail="Authorization failed or denied.")
    
    token_info = sp_oauth.get_access_token(code)
    save_token_info(token_info)
    logging.info("Token information saved.")
    
    user_info = sp_oauth.current_user()
    logging.info(f"User authenticated: {user_info}")
    return {"user_info": user_info}

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
    global sp
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

@app.on_event("startup")
def startup_event():
    initialize_spotify_client()

@app.on_event("shutdown")
async def shutdown_event():
    logging.info("Shutdown event triggered.")
    scheduler.shutdown(wait=False)

if __name__ == "__main__":
    run(app, host="0.0.0.0", port=8000, reload=True)
