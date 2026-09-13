from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from starlette.status import HTTP_401_UNAUTHORIZED
from spotipy.exceptions import SpotifyException

from app.api.routes import api_router
from app.core.config import settings
import spotipy
from spotipy.oauth2 import SpotifyOAuth

import redis
import secrets
import json
import random
import time

COOKIE = "session_id"

SCOPES = " ".join([
    "playlist-read-private",
    "playlist-read-collaborative",
    "user-read-playback-state",
    "user-modify-playback-state",
])

app = FastAPI(title="Better Shuffle API")
r = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    decode_responses=True,
)
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


def save_session(token_info: dict) -> str:
    session_id = secrets.token_urlsafe(32)
    r.set(name=f"session:{session_id}", ex=SESSION_TTL_SECONDS, value=json.dumps(token_info))
    return session_id

def load_session(session_id: str) -> dict | None:
    raw = r.get(f"session:{session_id}")
    return json.loads(raw) if raw else None

def check_session(request: Request) -> spotipy.Spotify:
    session_id = request.cookies.get(COOKIE) 
    token_info = load_session(session_id)
    if not token_info:
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED)
    return spotipy.Spotify(auth=token_info["access_token"])

@app.get("/")
def root(request: Request):
    session_id = request.cookies.get(COOKIE)
    token_info = load_session(session_id)
    if not token_info:
        return RedirectResponse(f"{settings.frontend_url}/Login")
    return RedirectResponse("f{settings.frontend_url}/Dashboard")



@app.get("/api/auth")
def auth():
    url = oauth.get_authorize_url()
    return RedirectResponse(url)

@app.get("/callback")
def callback(code: str):
    token_info = oauth.get_access_token(code, check_cache=False)
    session_id = save_session(token_info)
    resp = RedirectResponse(url=f"{settings.frontend_url}/Dashboard")
    resp.set_cookie(COOKIE, session_id, httponly=True, samesite="lax", max_age=SESSION_TTL_SECONDS)
    return resp

@app.get("/api/list-playlists")
def list_playlists(request: Request):
    sp = check_session(request)
    cursor = sp.current_user_playlists(limit=50)
    playlists = []
    while cursor:
        playlists.extend(cursor['items'])
        cursor = sp.next(cursor)

    return playlists

MAX_PLAY_URIS = 50


def playlist_track_uris(sp: spotipy.Spotify, playlist_id: str) -> list[str]:
    """Collect playable track URIs from a playlist the user owns."""
    try:
        results = sp.playlist_items(
            playlist_id,
            market="from_token",
            additional_types=("track",),
        )
    except SpotifyException as exc:
        if exc.http_status == 403:
            raise HTTPException(
                status_code=403,
                detail="Can't read this playlist. Spotify only allows shuffling playlists you own.",
            ) from exc
        raise HTTPException(status_code=exc.http_status or 502, detail=exc.reason or str(exc)) from exc

    uris: list[str] = []
    while results:
        for row in results.get("items") or []:
            track = row.get("item") or row.get("track")
            if not track or track.get("is_local") or track.get("type") != "track":
                continue
            if track.get("is_playable") is False:
                continue
            uri = track.get("uri")
            if uri and uri.startswith("spotify:track:"):
                uris.append(uri)
        results = sp.next(results) if results.get("next") else None
    return uris


def resolve_device_id(sp: spotipy.Spotify) -> str:
    playback = sp.current_playback()
    if playback and playback.get("device") and playback["device"].get("id"):
        return playback["device"]["id"]

    devices = (sp.devices() or {}).get("devices") or []
    if not devices:
        raise HTTPException(
            status_code=400,
            detail="No Spotify device found. Open Spotify on your computer or phone, play something, then try again.",
        )
    active = next((device for device in devices if device.get("is_active")), None)
    device = active or devices[0]
    if not active:
        sp.transfer_playback(device["id"], force_play=False)
        time.sleep(0.5)
    return device["id"]


@app.post("/api/playlists/{playlist_id}/shuffle")
def shuffle(playlist_id: str, request: Request):
    sp = check_session(request)
    tracks = playlist_track_uris(sp, playlist_id)
    if not tracks:
        raise HTTPException(status_code=400, detail="No playable tracks in this playlist.")

    random.shuffle(tracks)
    resolve_device_id(sp)

    # `start_playback(uris=[...])` replaces the playlist with a raw track
    # collection. On the Windows desktop client that flushes audio and leaves
    # the player stuck (nothing playing, resume/skip/transfer all disallowed).
    # Playing the playlist context at a shuffled offset keeps Connect alive.
    try:
        sp.start_playback(
            context_uri=f"spotify:playlist:{playlist_id}",
            offset={"uri": tracks},
            position_ms=0,
        )
        time.sleep(0.3)
        for uri in tracks[1:MAX_PLAY_URIS]:
            sp.add_to_queue(uri)
    except SpotifyException as exc:
        raise HTTPException(status_code=exc.http_status or 502, detail=exc.reason or str(exc)) from exc

    return {"ok": True, "playing": tracks[0], "queued": min(len(tracks), MAX_PLAY_URIS)}
