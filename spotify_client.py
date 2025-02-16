import os
import json
import logging
import time
import spotipy
from scheduled_playback import sp_oauth

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

token_store = {}
TOKEN_FILE_PATH = "token_info.json"

def save_token_info(token_info):
    logging.info("📝 Attempting to save token information.")

    # Check if token_info is empty or None
    if not token_info:
        logging.error("❌ save_token_info() received an empty token. Not saving!")
        return

    token_store['token_info'] = token_info
    try:
        with open(TOKEN_FILE_PATH, 'w') as f:
            json.dump(token_info, f)
        logging.info("✅ Token information saved successfully.")
    except Exception as e:
        logging.error(f"❌ Error writing token file: {e}")

def load_token_info():
    logging.info("Attempting to load token information.")
    if 'token_info' in token_store:
        logging.info("Token information found in memory.")
        return token_store['token_info']
    if os.path.exists(TOKEN_FILE_PATH):
        try:
            with open(TOKEN_FILE_PATH, 'r') as f:
                token_info = json.load(f)
                token_store['token_info'] = token_info
                logging.info("Token information loaded from file.")
                return token_info
        except json.JSONDecodeError:
            logging.error("Invalid token file format. Re-authentication is required.")
            return None
    logging.warning("No token information found.")
    return None

def clear_token_info():
    """
    Clears the stored Spotify authentication token file and resets memory.
    """
    global token_store

    if os.path.exists(TOKEN_FILE_PATH):
        os.remove(TOKEN_FILE_PATH)
        logging.info("Spotify token file cleared.")

    token_store.clear()
    logging.info("In-memory token store cleared.")

        
def initialize_spotify_client():
    """Initialize the Spotify client with token persistence."""
    global sp

    # Load token from file
    token_info = load_token_info()

    # Check if token exists and is still valid
    if token_info:
        sp_oauth.token_info = token_info
        logging.info("Using loaded token information.")
    else:
        logging.info("No valid token found. Requesting a new token.")
    
    # Initialize Spotify client
    sp = spotipy.Spotify(auth_manager=sp_oauth)
    save_token_info(sp.auth_manager.get_cached_token())
    logging.info("Spotify client initialized successfully.")

def refresh_token_if_needed():
    """Refresh Spotify token if it's expired or missing."""
    global sp

    token_info = load_token_info()  # Load from JSON file
    if not token_info:
        logging.warning("No token info found. User must log in.")
        return None  # Force login

    expires_at = token_info.get("expires_at", 0)
    refresh_token = token_info.get("refresh_token")

    if not refresh_token:
        logging.error("No refresh token available. User must re-authenticate.")
        clear_token_info()  # Delete invalid token
        return None  # Force login

    # Check if token is expired
    if expires_at > time.time():
        logging.info("Token is still valid.")
        return token_info  # No need to refresh

    logging.info("Access token expired. Attempting refresh...")

    # Refresh the token
    try:
        refreshed_token = sp_oauth.refresh_access_token(refresh_token)
        refreshed_token["expires_at"] = time.time() + refreshed_token["expires_in"]

        save_token_info(refreshed_token)  # Save updated token
        logging.info("Token refreshed and saved successfully.")
        return refreshed_token

    except Exception as e:
        logging.error(f"Token refresh failed: {e}")
        clear_token_info()  # Reset token storage
        return None  # Force login


