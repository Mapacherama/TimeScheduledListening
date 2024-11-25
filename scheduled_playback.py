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
    
    # Get the current access token
    access_token_info = sp.auth_manager.get_access_token(as_dict=True)
    
    # Check if the access token is expired
    if access_token_info['expires_at'] < time.time():
        # Refresh the access token
        sp.auth_manager.refresh_access_token(access_token_info['refresh_token'])

def play_playlist(playlist_uri, retry_count=3, delay=5):
    global sp

    if not sp:
        initialize_spotify_client() 

    refresh_token_if_needed()
    if not isinstance(sp, spotipy.Spotify):
        raise Exception("Spotify client is not initialized.")

    if not playlist_uri or not isinstance(playlist_uri, str):
        raise ValueError("Invalid playlist URI provided.")

    devices = sp.devices()
    if not devices['devices']:
        raise Exception("No active Spotify devices available for playback.")

    for attempt in range(retry_count):
        try:
            if playlist_uri.startswith(("spotify:playlist:", "spotify:album:", "spotify:artist:")):
                sp.start_playback(context_uri=playlist_uri)
            else:
                sp.start_playback(uris=[playlist_uri])

            logging.info(f"Started playback for {playlist_uri}")
            return
        except (ConnectionError, urllib3.exceptions.ProtocolError, 
                urllib3.exceptions.MaxRetryError, spotipy.exceptions.SpotifyException) as e:
            logging.error(f"Failed to start playback (Attempt {attempt + 1}/{retry_count}): {str(e)}")
            if attempt < retry_count - 1:
                logging.warning(f"Retrying in {delay * (2 ** attempt)} seconds...")
                time.sleep(delay * (2 ** attempt))
            else:
                logging.error("Max retry attempts reached. Playback failed.")
                raise
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            raise
