import schedule
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Set up your Spotify credentials using environment variables
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                                               client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                                               redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                                               scope="user-modify-playback-state"))

def play_spotify_playlist(playlist_uri):
    # Get the user's current device
    devices = sp.devices()
    if devices['devices']:
        device_id = devices['devices'][0]['id']
        
        # Start playing the playlist
        sp.start_playback(device_id=device_id, context_uri=playlist_uri)
        print(f"Playing playlist: {playlist_uri}")
    else:
        print("No active device found. Please start Spotify on your device.")

# Correct the playlist URI format
playlist_uri = "spotify:playlist:04nZz4vvtnc24gDhQdg8Vd"

# Schedule the task
schedule.every().day.at("15:10").do(play_spotify_playlist, playlist_uri=playlist_uri)

# Run the scheduler
while True:
    schedule.run_pending()
    time.sleep(20)
