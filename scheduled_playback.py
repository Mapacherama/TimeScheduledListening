from spotipy.oauth2 import SpotifyOAuth
import spotipy
import os
import logging
from requests.exceptions import ConnectionError
import urllib3
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-modify-playback-state"
)

sp = None 

def initialize_spotify_client():
    """Initialize the Spotify client."""
    global sp
    sp = spotipy.Spotify(auth_manager=sp_oauth)
    logging.info("Spotify client initialized successfully.")

def refresh_token_if_needed():
    """Refresh Spotify token if it's expired."""
    global sp
    if not sp:
        raise Exception("Spotify client is not initialized.")
    sp.auth_manager.refresh_access_token()

def play_playlist(playlist_uri, retry_count=3, delay=5):
    """Play a Spotify playlist or URI."""
    global sp
    refresh_token_if_needed()
    if not sp:
        raise Exception("Spotify client is not initialized.")

    for attempt in range(retry_count):
        try:
            if playlist_uri.startswith(("spotify:playlist:", "spotify:album:", "spotify:artist:")):
                sp.start_playback(context_uri=playlist_uri)
            else:
                sp.start_playback(uris=[playlist_uri])

            logging.info(f"Started playback for {playlist_uri}")
            break
        except (ConnectionError, urllib3.exceptions.ProtocolError, 
                urllib3.exceptions.MaxRetryError, spotipy.exceptions.SpotifyException) as e:
            logging.error(f"Failed to start playback: {str(e)}")
            if attempt < retry_count - 1:
                time.sleep(delay * (2 ** attempt))
            else:
                logging.error("Max retry attempts reached. Playback failed.")
                raise