from fastapi import HTTPException
import logging
import spotipy

def search_podcast(sp, refresh_token_if_needed, query: str):
    refresh_token_if_needed()
    if not sp:
        raise HTTPException(status_code=500, detail="Spotify client is not initialized")

    try:
        search_results = sp.search(q=query, type="show", limit=5)
        podcasts = search_results.get('shows', {}).get('items', [])
        if not podcasts:
            return {"message": "No podcasts found for the query."}

        podcast_list = [{
            "name": podcast['name'],
            "description": podcast['description'],
            "url": podcast['external_urls']['spotify']
        } for podcast in podcasts]

        return {"podcasts": podcast_list}

    except spotipy.exceptions.SpotifyException as e:
        logging.error(f"Spotify API error: {str(e)}")
        raise HTTPException(status_code=500, detail="Spotify API error")