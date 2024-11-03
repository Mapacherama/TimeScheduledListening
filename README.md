# TimeScheduledListening

Automated playback of media based on schedules using the Spotify API.

## Features
- **User Authentication**: Users can log in to their Spotify account and authenticate the application.
- **Schedule Playback**: Users can schedule playlists or albums to play at specific times.
- **Search Podcasts**: Users can search for podcasts by query and retrieve relevant results.
- **Token Management**: Automatically refreshes access tokens to maintain user sessions.

## Requirements
- Python 3.x
- FastAPI
- Spotipy
- APScheduler
- Requests

## Setup
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd TimeScheduledListening
   ```

2. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your Spotify API credentials:
   - Create a `.env` file in the root directory and add your Spotify credentials:
     ```
     SPOTIPY_CLIENT_ID=<your-client-id>
     SPOTIPY_CLIENT_SECRET=<your-client-secret>
     SPOTIPY_REDIRECT_URI=<your-redirect-uri>
     ```

4. Run the application:
   ```bash
   uvicorn scheduled_playback:app --reload
   ```

## API Endpoints
- **Login**: `GET /login` - Initiates the login process and returns the authentication URL.
- **Callback**: `GET /callback` - Handles the callback from Spotify after user authentication.
- **Schedule Playlist**: `GET /schedule-playlist?playlist_uri=<uri>&play_time=<HH:MM>` - Schedules a playlist to play at the specified time.
- **Search Podcast**: `GET /search-podcast?query=<search-term>` - Searches for podcasts based on the provided query.

## License
This project is licensed under the MIT License.