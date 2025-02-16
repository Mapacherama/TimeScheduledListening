from datetime import datetime
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import os
import logging
from requests.exceptions import ConnectionError
import urllib3
import time
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

sp_oauth = SpotifyOAuth(
    client_id=os.getenv("SPOTIPY_CLIENT_ID"),
    client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
    redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
    scope="user-modify-playback-state user-read-playback-state user-read-currently-playing"
)

print(os.getenv("SPOTIPY_CLIENT_ID"))
print(os.getenv("SPOTIPY_CLIENT_SECRET"))
print(os.getenv("SPOTIPY_REDIRECT_URI"))

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
    
    access_token_info = sp.auth_manager.get_access_token(as_dict=True)

    # Check and refresh the token
    if 'expires_at' in access_token_info and access_token_info['expires_at'] < time.time():
        logging.info("Access token expired. Refreshing token...")
        new_token_info = sp.auth_manager.refresh_access_token(access_token_info['refresh_token'])
        logging.info("Access token refreshed successfully.")
    else:
        logging.info("Access token is still valid.")

def play_playlist(playlist_uri, retry_count=3, delay=5):
    global sp

    if not sp:
        initialize_spotify_client() 

    refresh_token_if_needed()
    if not isinstance(sp, spotipy.Spotify):
        raise Exception("Spotify client is not initialized.")

    if not playlist_uri or not isinstance(playlist_uri, str):
        raise ValueError("Invalid playlist URI provided.")

    devices = None
    for attempt in range(retry_count):
        try:
            devices = sp.devices()
            if devices['devices']:
                break
            else:
                raise Exception("No active Spotify devices available for playback.")
        except requests.exceptions.ConnectionError as e:
            logging.error(f"Connection error: {e}. Attempt {attempt + 1} of {retry_count}.")
            if attempt < retry_count - 1:
                time.sleep(delay)
            else:
                logging.error("Max retries reached. Unable to fetch devices.")
                raise
        except Exception as e:
            logging.error(f"Unexpected error while fetching devices: {e}")
            raise

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

def get_spotify_playlists(mood: str, limit: int = 5):
    """
    Fetches Spotify playlists based on the provided mood.

    Args:
        - mood (str): The mood/category (e.g., 'focus', 'workout', 'chill').
        - limit (int): Number of playlists to fetch.

    Returns:
        - List of playlist dictionaries with 'name', 'uri', and 'url'.
    """
    token_info = refresh_token_if_needed()  # Ensure we have a fresh token
    if not token_info:
        raise Exception("Spotify authentication required. Please log in.")

    token = token_info["access_token"]

    url = f"https://api.spotify.com/v1/browse/categories/{mood.lower()}/playlists"
    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(url, headers=headers, params={"limit": limit})

    if response.status_code == 200:
        playlists = response.json().get("playlists", {}).get("items", [])
        if not playlists:
            logging.warning(f"No playlists found for mood: {mood}. Trying fallback categories.")
            return get_spotify_playlists("chill")  # Fallback to a general mood

        return [{"name": p["name"], "uri": p["uri"], "url": p["external_urls"]["spotify"]} for p in playlists]

    logging.error(f"Failed to fetch Spotify playlists: {response.text}")
    raise Exception(f"Spotify API error: {response.status_code} - {response.text}")

def get_time_based_mood():
    """
    Returns a recommended mood based on the current time of day.
    """
    hour = datetime.now().hour

    if 6 <= hour < 12:
        return "energy boost"  # Morning vibes ☀️
    elif 12 <= hour < 18:
        return "focus"  # Work & study time 🎯
    elif 18 <= hour < 22:
        return "chill"  # Wind-down & relax 🌆
    else:
        return "sleep"  # Night-time calming music 😴 
