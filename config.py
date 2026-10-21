import os
import requests
import dotenv
import sys
import obsws_python as obs

dotenv.load_dotenv()

WIDGET_WS_PORT = int(os.environ.get('WIDGET_WS_PORT', "3004"))
BOT_USER_ID = os.environ['BOT_USER_ID']
BOT_TOKEN = os.environ['BOT_TOKEN']
BROADCASTER_TOKEN = os.environ["BROADCASTER_TOKEN"]
CLIENT_ID = os.environ['CLIENT_ID']
CLIENT_SECRET = os.environ['CLIENT_SECRET']
CLIENT_TOKEN = os.environ['CLIENT_TOKEN']
NVIDIA_KEY = os.environ['NVIDIA_KEY']
GROQ_KEY = os.environ['GROQ_KEY']
OPENROUTER_KEY = os.environ['OPENROUTER_KEY']
BROADCASTER_USER_ID = os.environ['BROADCASTER_USER_ID']
SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
TYPESAFE_KEY = os.environ['TYPESAFE_KEY']


try:
    OBS_WS_PASSWORD = os.environ['OBS_WS_PASSWORD']
    OBS_CL = obs.ReqClient(host='localhost', port=4455, password=OBS_WS_PASSWORD)
except (ConnectionRefusedError, TimeoutError):
    OBS_WS_PASSWORD = None
    OBS_CL = None
EVENTSUB_WEBSOCKET_URL = 'wss://eventsub.wss.twitch.tv/ws'
BOT_HEADERS = {
    'Authorization': 'Bearer ' + BOT_TOKEN,
    'Client-Id': CLIENT_ID,
    'Content-Type': 'application/json',
}
BROADCASTER_HEADERS = {
    'Authorization': 'Bearer ' + BROADCASTER_TOKEN,
    'Client-Id': CLIENT_ID,
    'Content-Type': 'application/json',
}

r = requests.post('https://id.twitch.tv/oauth2/token', params={
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'grant_type': 'client_credentials',
})
if r.status_code != 200:
    print('Failed to mint app access token. API call returned status code', r.status_code, file=sys.stderr)
    print(r.json(), file=sys.stderr)
    sys.exit(1)
_app_token = r.json()['access_token']

APP_HEADERS = {
        'Authorization': 'Bearer ' + _app_token,
        'Client-Id': CLIENT_ID,
        'Content-Type': 'application/json',
    }