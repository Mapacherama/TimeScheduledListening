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

import os
import logging
from spotify_client import load_token_info, save_token_info, clear_token_info
import requests
from scheduled_playback import sp_oauth

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

def refresh_token_if_needed():
    """
    Refreshes the Spotify access token if it's expired.
    If the refresh token is invalid, forces user to log in again.
    """
    token_info = load_token_info()
    
    if not token_info:
        logging.warning("No token info found. User must log in.")
        return None

    expires_at = token_info.get("expires_at", 0)
    refresh_token = token_info.get("refresh_token")
    
    if not refresh_token:
        logging.error("No refresh token available. User must re-authenticate.")
        clear_token_info()
        return None

    # Check if token is expired (with 60 second buffer)
    if time.time() < (expires_at - 60):
        logging.info("Token is still valid.")
        return token_info

    logging.info("Access token expired. Refreshing...")

    try:
        # Use the OAuth manager's built-in refresh method
        new_token_info = sp_oauth.refresh_access_token(refresh_token)
        new_token_info["expires_at"] = time.time() + new_token_info["expires_in"]
        
        # Preserve the original refresh token if not provided in response
        if "refresh_token" not in new_token_info:
            new_token_info["refresh_token"] = refresh_token
            
        save_token_info(new_token_info)
        logging.info("Token refreshed successfully.")
        return new_token_info

    except Exception as e:
        logging.error(f"Token refresh failed: {e}")
        
        # Check if it's a revoked token error
        if "invalid_grant" in str(e) or "revoked" in str(e):
            logging.error("Refresh token revoked. Clearing stored tokens.")
            clear_token_info()
            return None
        
        # For other errors, return the old token and let the caller handle it
        logging.warning("Using existing token despite refresh failure.")
        return token_info

def play_playlist(playlist_uri, retry_count=3, delay=5):
    global sp

    if not sp:
        initialize_spotify_client() 

    # Check token before proceeding
    token_info = refresh_token_if_needed()
    if not token_info:
        logging.error("No valid token available. User must re-authenticate.")
        raise Exception("Authentication required. Please visit /login to authenticate.")
    
    # Reinitialize client with fresh token
    try:
        sp = spotipy.Spotify(auth=token_info["access_token"])
    except Exception as e:
        logging.error(f"Failed to initialize Spotify client: {e}")
        raise Exception("Failed to initialize Spotify client. Please re-authenticate.")

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
        except spotipy.exceptions.SpotifyException as e:
            if "invalid_grant" in str(e) or "revoked" in str(e):
                logging.error("Token revoked during device fetch. User must re-authenticate.")
                clear_token_info()
                raise Exception("Authentication expired. Please visit /login to re-authenticate.")
            else:
                logging.error(f"Spotify API error while fetching devices: {e}")
                if attempt < retry_count - 1:
                    time.sleep(delay)
                else:
                    raise
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
        except spotipy.exceptions.SpotifyException as e:
            if "invalid_grant" in str(e) or "revoked" in str(e):
                logging.error("Token revoked during playback. User must re-authenticate.")
                clear_token_info()
                raise Exception("Authentication expired. Please visit /login to re-authenticate.")
            else:
                logging.error(f"Spotify API error during playback: {e}")
                if attempt < retry_count - 1:
                    time.sleep(delay * (2 ** attempt))
                else:
                    raise
        except (ConnectionError, urllib3.exceptions.ProtocolError, 
                urllib3.exceptions.MaxRetryError) as e:
            logging.error(f"Failed to start playback (Attempt {attempt + 1}/{retry_count}): {str(e)}")
            if attempt < retry_count - 1:
                logging.warning(f"Retrying in {delay * (2 ** attempt)} seconds...")
                time.sleep(delay * (2 ** attempt))
            else:
                logging.error("Max retries reached. Playback failed.")
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
