from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from app.api.routes import api_router
from app.core.config import settings
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import redis

SCOPES = " ".join([
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-read-playback-state",
    "user-modify-playback-state",
])

app = FastAPI(title="Better Shuffle API")
r = redis.Redis(host="localhost", port=6379, decode_responses=True)
SESSION_TTL_SECONDS = 60 * 60 * 24 * 7  

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

oauth = SpotifyOAuth(
    client_id=settings.client_id,
    client_secret=settings.client_secret,
    redirect_uri=settings.redirect_uri,
    scope=SCOPES,
)

sp = spotipy.Spotify(auth_manager=oauth)

@app.get("/")
def root():
    return {"message": "running"}

@app.get("/api/auth")
def auth():
    url = oauth.get_authorize_url()
    return RedirectResponse(url)

@app.get("/callback")
def callback(code: str):
    token_info = oauth.get_access_token(code)
    redirect = RedirectResponse()
    return RedirectResponse(url="http://localhost:5173/Dashboard")

@app.get("/api/list-playlists")
def list_playlists():
    cursor = sp.current_user_playlists(limit=50)
    playlists = []
    while cursor:
        playlists.extend(cursor['items'])
        cursor = sp.next(cursor)

    print(playlists[0].keys())
    print(len(playlists))

    return {"message": "Better Shuffle API"}

@app.get("/play-random-song")
def play_random_song():
    return {"message": "Better Shuffle API"}