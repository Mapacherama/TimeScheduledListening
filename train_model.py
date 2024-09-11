import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
from pycaret.classification import setup, compare_models, create_model, tune_model, evaluate_model

# Setup Spotify OAuth
sp_oauth = SpotifyOAuth(client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                        scope="user-library-read")

sp = spotipy.Spotify(auth_manager=sp_oauth)

def get_heavy_metal_tracks(artist_name, limit=5):
    results = sp.search(q=f'artist:{artist_name}', type='track', limit=limit)
    track_ids = [track['id'] for track in results['tracks']['items']]
    return track_ids

def get_audio_features(track_ids):
    features = sp.audio_features(tracks=track_ids)
    X = []
    for feature in features:
        if feature:
            X.append([feature['tempo'], feature['energy'], feature['valence'], feature['loudness']])
    return np.array(X)

# Example: Collect heavy metal tracks
track_ids = []
for artist in ["Slayer", "Pantera", "Iron Maiden", "After the Burial", "100 Demons"]:
    track_ids += get_heavy_metal_tracks(artist, limit=5)

X_train = get_audio_features(track_ids)
y_train = np.ones(len(X_train))  # Label all heavy metal tracks as workout (1)

# Convert to a pandas DataFrame
import pandas as pd
data = pd.DataFrame(X_train, columns=["tempo", "energy", "danceability", "valence"])
data['label'] = y_train

# Use PyCaret for binary classification
# Initialize PyCaret classification setup
clf = setup(data=data, target='label', silent=True, verbose=False)

# Compare models and choose the best one
best_model = compare_models()

# Train the best model
trained_model = create_model(best_model)

# Optionally, tune the model
tuned_model = tune_model(trained_model)

# Evaluate the model
evaluate_model(tuned_model)
