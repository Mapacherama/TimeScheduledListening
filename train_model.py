import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

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
            X.append([feature['tempo'], feature['energy'], feature['danceability'], feature['valence']])
    return np.array(X)

# Example: Collect heavy metal tracks
track_ids = []
for artist in ["Slayer", "Pantera", "Iron Maiden", "After the Burial", "100 Demons"]:
    track_ids += get_heavy_metal_tracks(artist, limit=5)

X_train = get_audio_features(track_ids)
y_train = np.ones(len(X_train))  # Label all heavy metal tracks as workout (1)

# Define a simple neural network model in TensorFlow
model = models.Sequential()
model.add(layers.Dense(32, activation='relu', input_shape=(4,)))
model.add(layers.Dense(1, activation='sigmoid'))

# Compile the model
model.compile(optimizer=optimizers.Adam(lr=0.001), loss='binary_crossentropy')

# Train the model
model.fit(X_train, y_train, epochs=10)
