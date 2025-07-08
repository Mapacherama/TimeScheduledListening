from datetime import datetime
from fastapi import Request, HTTPException
from scheduled_playback import refresh_token_if_needed, sp_oauth
import logging
from spotify_client import save_token_info, load_token_info
import spotipy
import os

async def login():
    logging.info("Login endpoint accessed.")
    token_info = refresh_token_if_needed()
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
    
    # Log all query parameters for debugging
    logging.info(f"All query params: {dict(request.query_params)}")
    
    code = request.query_params.get('code')
    error = request.query_params.get('error')
    state = request.query_params.get('state')
    
    logging.info(f"Code: {code}")
    logging.info(f"Error: {error}")
    logging.info(f"State: {state}")

    # Handle Spotify authorization errors
    if error:
        logging.error(f"Spotify returned error: {error}")
        raise HTTPException(status_code=400, detail=f"Spotify authorization error: {error}")

    if not code:
        logging.error("Authorization failed: No code received.")
        raise HTTPException(status_code=400, detail="Authorization failed or denied.")

    try:
        # Get access token from Spotify
        logging.info("Requesting access token from Spotify...")
        token_info = sp_oauth.get_access_token(code)
        
        if not token_info:
            logging.error("Received empty token info from Spotify")
            raise HTTPException(status_code=500, detail="Failed to get token from Spotify")
        
        logging.info(f"Received token info: {token_info.keys()}")
        
        # Add expiration timestamp
        token_info["expires_at"] = datetime.now().timestamp() + token_info["expires_in"]
        
        # Save token to JSON file
        logging.info("Saving token information to file...")
        save_token_info(token_info)
        
        # Verify file was created
        if os.path.exists("token_info.json"):
            logging.info("✅ token_info.json file created successfully")
        else:
            logging.error("❌ token_info.json file was not created")
            raise HTTPException(status_code=500, detail="Failed to save token file")
        
        # Load and verify the saved token
        saved_token = load_token_info()
        if saved_token:
            logging.info("✅ Token loaded from file successfully")
        else:
            logging.error("❌ Failed to load token from file")
            raise HTTPException(status_code=500, detail="Failed to load saved token")
        
        # Test the token by creating a Spotify client
        try:
            sp = spotipy.Spotify(auth=token_info["access_token"])
            user_info = sp.current_user()
            logging.info(f"✅ User authenticated successfully: {user_info.get('display_name', 'Unknown')}")
        except Exception as e:
            logging.error(f"❌ Failed to authenticate with Spotify: {e}")
            raise HTTPException(status_code=500, detail="Failed to authenticate with Spotify")
        
        return {
            "message": "Authentication successful",
            "user_info": user_info,
            "token_saved": True,
            "file_created": os.path.exists("token_info.json")
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logging.error(f"Unexpected error in callback: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")