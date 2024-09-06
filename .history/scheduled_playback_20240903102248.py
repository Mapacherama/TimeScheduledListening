import spotipy
from spotipy.oauth2 import SpotifyOAuth
import schedule
import time

# Spotify Authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="98c8b3c52bd948e4b14fe06e2df5f61b", 
    client_secret="987bba6c6528417c82d683e8e1609522",  
    redirect_uri="http://localhost:8888/callback",  
    scope="user-read-playback-state,user-modify-playback-state"
))

def play_spotify_playlist(playlist_uri):
    # Get the user's available devices
    devices = sp.devices()
    if devices['devices']:
        device_id = devices['devices'][0]['id']
        sp.start_playback(device_id=device_id, context_uri=playlist_uri)
    else:
        print("No active devices found.")

def play_spotify_track(track_uri):
    devices = sp.devices()
    if devices['devices']:
        device_id = devices['devices'][0]['id']
        sp.start_playback(device_id=device_id, uris=[track_uri])
    else:
        print("No active devices found.")

# Example of scheduling a playlist to play at 7 AM every day
schedule.every().day.at("07:00").do(play_spotify_playlist, playlist_uri="spotify:playlist:your_playlist_uri")

# Example of scheduling a specific track to play at 8 PM every day
schedule.every().day.at("20:00").do(play_spotify_track, track_uri="spotify:track:your_track_uri")


