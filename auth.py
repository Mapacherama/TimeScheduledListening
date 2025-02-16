from datetime import datetime
from fastapi import Request, HTTPException
from scheduled_playback import refresh_token_if_needed, sp_oauth
import logging
from spotify_client import save_token_info
import spotipy

async def login():
    logging.info("Login endpoint accessed.")
    token_info =  refresh_token_if_needed()
    if token_info:
        logging.info("Token information found. User is already authenticated.")
        return {"message": "Already authenticated", "token_info": token_info}
    
    auth_url = sp_oauth.get_authorize_url()
    logging.info(f"Auth URL generated: {auth_url}")
    return {"auth_url": auth_url}

async def callback(request: Request):
    """
    Callback route for handling Spotify OAuth.
    Saves token info and auto-refreshes when needed.
    """
    logging.info("Callback endpoint accessed.")
    code = request.query_params.get('code')

    if not code:
        logging.error("Authorization failed: No code received.")
        raise HTTPException(status_code=400, detail="Authorization failed or denied.")

    token_info = sp_oauth.get_access_token(code)
    token_info["expires_at"] = datetime.now().timestamp() + token_info["expires_in"]

    save_token_info(token_info)
    logging.info("Token information saved.")

    token_info = refresh_token_if_needed()  # Ensure fresh token

    sp = spotipy.Spotify(auth=token_info["access_token"])
    user_info = sp.current_user()
    logging.info(f"User authenticated: {user_info}")
    
    return {"user_info": user_info}