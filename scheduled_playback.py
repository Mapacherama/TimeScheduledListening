from fastapi import FastAPI, Request, HTTPException
from spotipy.oauth2 import SpotifyOAuth
import spotipy
import os

app = FastAPI()

# Initialize Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                        scope="user-modify-playback-state")

@app.get("/login")
def login():
    # Redirect the user to the Spotify authorization URL
    auth_url = sp_oauth.get_authorize_url()
    return {"auth_url": auth_url}

@app.get("/callback")
def callback(request: Request):
    # Get the authorization code from the query parameters
    code = request.query_params.get('code')
    
    # If no code is returned, raise an exception
    if not code:
        raise HTTPException(status_code=400, detail="Authorization failed or denied.")
    
    # Get the access token using the authorization code
    token_info = sp_oauth.get_access_token(code)
    
    # Store or use the token information (access token, refresh token, etc.)
    access_token = token_info['access_token']
    
    # You can use the token to create a Spotipy client instance
    sp = spotipy.Spotify(auth=access_token)
    
    # Example usage: Get current user info
    user_info = sp.current_user()
    
    return {"user_info": user_info}
