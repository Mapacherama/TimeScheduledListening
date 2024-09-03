import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Spotify Authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id="98c8b3c52bd948e4b14fe06e2df5f61b", 
    client_secret="987bba6c6528417c82d683e8e1609522",  
    redirect_uri="http://localhost:8888/callback",  
    scope="user-read-playback-state,user-modify-playback-state"
))
