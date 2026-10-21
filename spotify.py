import asyncio
import re
from typing import Any

import requests
import spotipy
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from spotipy.oauth2 import SpotifyOAuth

SP = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                                               client_secret=SPOTIFY_CLIENT_SECRET,
                                               redirect_uri="http://127.0.0.1:3003",
                                               scope="user-read-playback-state user-modify-playback-state user-read-currently-playing"))

BANNED_SONGS = ()
EXTREMELY_BANNED_SONGS = ("0jsLL7tNPYkz3b1GaStq2S", )
BANNED_ARTISTS = ()


async def get_track_with_retry(url, attempts=3):
    for attempt in range(attempts):
        try:
            return await asyncio.to_thread(SP.track, url)
        except (requests.exceptions.ConnectionError,
                requests.exceptions.Timeout):
            if attempt == attempts - 1:
                raise
            await asyncio.sleep(0.5 * (2 ** attempt))

async def saftey_check(song_url):
    url = await sanitize_url(song_url)

    if url == "Bad Request":
        return "Bad Request", None, None
    try:
        track: Any = await get_track_with_retry(url)
        artist = track["artists"][0]["name"]
        if track["explicit"]:
            return "explicit", track["name"], None, None

        elif track["duration_ms"] > 360000:
            return "long", track["name"], None, None

        elif track["id"] in EXTREMELY_BANNED_SONGS:
            return "extremely_banned_song", track["name"], None, None

        elif track["id"] in BANNED_SONGS:
            return "banned_song", track["name"], None, None

        elif track["artists"][0]["id"] in BANNED_ARTISTS:
            return "banned_artist", track["name"], None, None

        return None, track["name"], artist, url

    except spotipy.exceptions.SpotifyException as err:
        print(err)
        return "Bad Request", None, None

    except requests.exceptions.RequestException as err:
        print(err)
        return "THIS IS NOT GOOD", None, None

async def sanitize_url(songurl: str):
    URI = re.compile(r'spotify:(?P<type>\w+):(?P<id>[0-9A-Za-z]{22})')
    URL = re.compile(r'(?:https?://)?open\.spotify\.com/(?:intl-\w\w/)?(?P<type>\w+)/(?P<id>[0-9A-Za-z]{22})')
    BARE = re.compile(r'^[0-9A-Za-z]{22}$')

    s_url = URI.search(songurl)
    if s_url and s_url.group("type") == "track":
        return s_url.group()

    s_url = URL.search(songurl)
    if s_url and s_url.group("type") == "track":
        return s_url.group()

    s_url = BARE.search(songurl)
    if s_url:
        return s_url.group()

    return "Bad Request"

async def add_req_to_queue(url):
    SP.add_to_queue(url)


async def get_current_song():
    try:
        result: Any = SP.current_user_playing_track()
        return result["item"]["name"], result["item"]["artists"][0]["name"]
    except Exception as err:
        print(err)  # noqa: E722
        return None, None
