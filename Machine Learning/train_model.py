import numpy as np
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset

# Spotify OAuth setup
sp_oauth = SpotifyOAuth(client_id=os.getenv("SPOTIPY_CLIENT_ID"),
                        client_secret=os.getenv("SPOTIPY_CLIENT_SECRET"),
                        redirect_uri=os.getenv("SPOTIPY_REDIRECT_URI"),
                        scope="user-library-read")

sp = spotipy.Spotify(auth_manager=sp_oauth)

def get_heavy_metal_tracks(artist_name, limit=5):
    try:
        results = sp.search(q=f'artist:{artist_name}', type='track', limit=limit)
        print(f"Fetching tracks for artist: {artist_name}")
        track_ids = [track['id'] for track in results['tracks']['items']]
        return track_ids
    except Exception as e:
        print(f"Failed to fetch tracks for {artist_name}: {str(e)}")
        return []

def get_audio_features(track_ids):
    try:
        print("Fetching audio features.")
        features = sp.audio_features(tracks=track_ids)
        X = []
        for feature in features:
            if feature:
                X.append([feature['tempo'], feature['energy'], feature['valence'], feature['loudness']])
        return np.array(X)
    except Exception as e:
        print(f"Failed to fetch audio features: {str(e)}")
        return np.array([])

# Collect heavy metal tracks
track_ids = []
artists = ["Slayer", "Pantera", "Iron Maiden", "After the Burial", "100 Demons"]
for artist in artists:
    track_ids += get_heavy_metal_tracks(artist, limit=5)

X_train = get_audio_features(track_ids)
y_train = np.ones(len(X_train))  # Label all heavy metal tracks as workout (1)

# Neural Network Model
class Net(nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.fc1 = nn.Linear(4, 64)  # 4 features
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, 1)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()
        
    def forward(self, x):
        x = self.relu(self.fc1(x))
        x = self.relu(self.fc2(x))
        x = self.sigmoid(self.fc3(x))
        return x

# Instantiate model, loss function, and optimizer
model = Net()
criterion = nn.BCELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

# Training loop
def train_model(epochs, dataloader):
    model.train()
    total_batches = len(dataloader)
    for epoch in range(epochs):
        for i, (data, target) in enumerate(dataloader):
            optimizer.zero_grad()
            output = model(data)
            loss = criterion(output.squeeze(), target)
            loss.backward()
            optimizer.step()
            if i % 5 == 0:  # Print every 5 batches
                print(f'Epoch {epoch+1}/{epochs}, Batch {i+1}/{total_batches}, Loss: {loss.item():.4f}')
        print(f'Epoch {epoch+1} complete.')

# Evaluate the model
def evaluate_model(dataloader):
    model.eval()
    correct = 0
    total = len(dataloader.dataset)
    with torch.no_grad():
        for data, target in dataloader:
            output = model(data)
            predicted = output.round()  # Apply threshold at 0.5
            correct += (predicted.squeeze() == target).sum().item()
    accuracy = 100 * correct / total
    print(f'Accuracy: {accuracy:.2f}%')

if __name__ == '__main__':
    if X_train.size == 0:
        print("No data available for training. Check data retrieval functions.")
    else:
        # Convert data to PyTorch tensors
        X_tensor = torch.tensor(X_train, dtype=torch.float32)
        y_tensor = torch.tensor(y_train, dtype=torch.float32)

        # Create a DataLoader
        dataset = TensorDataset(X_tensor, y_tensor)
        dataloader = DataLoader(dataset, batch_size=16, shuffle=True)

        if len(dataloader) == 0:
            print("DataLoader is empty. Check batch size and data availability.")
        else:
            train_model(10, dataloader)
            evaluate_model(dataloader)
