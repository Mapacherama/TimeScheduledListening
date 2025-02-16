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
    logging.info("Attempting to save token information.")
    token_store['token_info'] = token_info
    with open(TOKEN_FILE_PATH, 'w') as f:
        json.dump(token_info, f)
    logging.info("Token information saved successfully.")

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
    Clears the stored Spotify authentication token file to force re-authentication.
    """
    if os.path.exists(TOKEN_FILE_PATH):
        os.remove(TOKEN_FILE_PATH)
        print("Spotify token file cleared.")
    else:
        print("No token file found.")
        
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
    """Refresh Spotify token if it's expired."""
    global sp

    if not sp:
        raise Exception("Spotify client is not initialized.")

    access_token_info = sp.auth_manager.get_access_token(as_dict=True)

    # Refresh only if expired
    if access_token_info['expires_at'] < time.time():
        refreshed_token = sp.auth_manager.refresh_access_token(access_token_info['refresh_token'])
        save_token_info(refreshed_token)  # Save the refreshed token
        logging.info("Token refreshed and saved.")


