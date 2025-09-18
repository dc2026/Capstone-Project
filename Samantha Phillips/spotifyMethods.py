
from dataclasses import dataclass
from flask import session
from spotipy import Spotify, SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler



client_id = 'abd8b0ef243840ce839ec126112f25c8'
client_secret = '2a490c637a5749adaa48c7cc12172cbb'

redirect_uri = 'http://127.0.0.1:5000/callback'
scope = 'playlist-read-private,streaming'

cache_handler = FlaskSessionCacheHandler(session)
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)

sp_client = Spotify(auth_manager=sp_oauth)

@dataclass
class Song():
    title: str
    album: str
    artist: str
    spotify_id: str


def search(query):
    results = sp_client.search(query, limit=15)

    songs = []
    for track in results["tracks"]["items"]: # type: ignore
        song = Song(
            title=track.get('name', 'NULL'),
            album=track.get('album', 'NULL album').get('name'),
            artist=track.get('artists', 'NULL')[0].get('name', 'NULL'),
            spotify_id=track.get('id', '')
        )

    songs.append(song) # type: ignore

    return songs


