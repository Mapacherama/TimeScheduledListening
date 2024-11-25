from fastapi import Request, HTTPException
from scheduled_playback import sp_oauth
import logging
from spotify_client import load_token_info, save_token_info
import spotipy

async def login():
    logging.info("Login endpoint accessed.")
    token_info = load_token_info()
    if token_info:
        logging.info("Token information found. User is already authenticated.")
        return {"message": "Already authenticated", "token_info": token_info}
    
    auth_url = sp_oauth.get_authorize_url()
    logging.info(f"Auth URL generated: {auth_url}")
    return {"auth_url": auth_url}

async def callback(request: Request):
    logging.info("Callback endpoint accessed.")
    code = request.query_params.get('code')
    if not code:
        logging.error("Authorization failed: No code received.")
        raise HTTPException(status_code=400, detail="Authorization failed or denied.")
    
    token_info = sp_oauth.get_access_token(code)
    save_token_info(token_info)
    logging.info("Token information saved.")
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    user_info = sp.current_user()
    logging.info(f"User authenticated: {user_info}")
    return {"user_info": user_info}