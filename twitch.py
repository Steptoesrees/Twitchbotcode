import asyncio
import sys

import requests
from config import (
    BOT_HEADERS,
    BOT_USER_ID,
    BROADCASTER_HEADERS,
    BROADCASTER_TOKEN,
    BROADCASTER_USER_ID,
    APP_HEADERS
)



def get_auth():
    r = requests.get('https://id.twitch.tv/oauth2/validate',
                     headers={'Authorization': 'OAuth ' + BROADCASTER_TOKEN})
    if r.status_code != 200:
        print('Token is not valid. /oauth2/validate returned status code', r.status_code, file=sys.stderr)
        print(r.json(), file=sys.stderr)
        sys.exit(1)




async def send_chat_message(chat_message, parent_id=None, retry=False):
    if not parent_id:
        jSON = {'broadcaster_id': BROADCASTER_USER_ID, 'sender_id': BOT_USER_ID, 'message': chat_message}
    else:
        jSON = {'broadcaster_id': BROADCASTER_USER_ID, 'sender_id': BOT_USER_ID, 'message': chat_message, "reply_parent_message_id": parent_id}

    resp = await asyncio.to_thread(
        requests.post, 'https://api.twitch.tv/helix/chat/messages',
        headers=APP_HEADERS,
        json=jSON,
    )

    if resp.status_code == 400:
        print('Failed to send chat message', resp.json(), file=sys.stderr)
        if not retry:
            await send_chat_message('yoooo, my message was too long mb chat', retry=True)
    elif resp.status_code != 200:
        print('Failed to send chat message', resp.json(), file=sys.stderr)
    else:
        print('Sent chat message: ' + chat_message)



async def register_eventsub_listeners(websocket_session_id):
    subscriptions = ('channel.chat.message',
                    'channel.channel_points_custom_reward_redemption.add',
                    'stream.online',
                    'stream.offline')
    for sub_type in subscriptions:

        resp = await asyncio.to_thread(
            requests.post, 'https://api.twitch.tv/helix/eventsub/subscriptions',
            headers=BROADCASTER_HEADERS,
            json={
                'type': sub_type,
                'version': '1',
                'condition': {
                    'broadcaster_user_id': BROADCASTER_USER_ID,
                    'user_id': BROADCASTER_USER_ID,
                    'reward_id': '',
                },
                'transport': {'method': 'websocket', 'session_id': websocket_session_id},
            },
        )
        if resp.status_code != 202:
            print(f'Failed to subscribe to {sub_type}. API call returned status code', resp.status_code, file=sys.stderr)
            print(resp.json(), file=sys.stderr)
            sys.exit(1)
        print(f"Subscribed to {sub_type} [{resp.json()['data'][0]['id']}]")


async def check_if_live():
    resp = await asyncio.to_thread(
        requests.get, 'https://api.twitch.tv/helix/streams',
        headers=BOT_HEADERS,
        params={'user_id': BROADCASTER_USER_ID},
    )
    resp = resp.json()
    return resp.get("data") != []


async def get_power_users(): #moderators n stuff
    resp = await asyncio.to_thread(
        requests.get, 'https://api.twitch.tv/helix/moderation/moderators',
        headers=BROADCASTER_HEADERS,
        params={'broadcaster_id': BROADCASTER_USER_ID},
    )
    resp = resp.json()
    return resp.get("data")


async def if_moderator(user_id):
    if user_id == BROADCASTER_USER_ID:
        return True
    data = await get_power_users()
    for user in data:
        if user['user_id'] == user_id:
            print("user is mod")
            return True
    print("user is not mod")
    return False


async def update_redemption(reward_id, redeem_id, status: str):
    if status not in ['FULFILLED', 'CANCELED']:
        return
    resp = await asyncio.to_thread(
        requests.patch, 'https://api.twitch.tv/helix/channel_points/custom_rewards/redemptions',
        headers=BROADCASTER_HEADERS,
        params={'id': redeem_id,'broadcaster_id': BROADCASTER_USER_ID, 'reward_id': reward_id},
        json={'status': status},
    )
    if resp.status_code != 200:
        print(f'Failed to update redemption for reward {reward_id}. API call returned status code', resp.status_code, file=sys.stderr)
        print(resp.json(), file=sys.stderr)
        sys.exit(1)
    print(f'Updated redemption for reward {reward_id} to status {status}')


async def get_userid(name):
    resp = await asyncio.to_thread(
            requests.get, 'https://api.twitch.tv/helix/users',
            headers=BOT_HEADERS,
            params={'login': name},
        )
    resp = resp.json()
    return resp["data"][0]["id"]

async def delete_message(msg_id):
    resp = await asyncio.to_thread(
            requests.delete, 'https://api.twitch.tv/helix/moderation/chat',
            headers=BROADCASTER_HEADERS,
            params={'message_id': msg_id,'broadcaster_id': BROADCASTER_USER_ID, 'moderator_id': BROADCASTER_USER_ID},
        )
    if resp.status_code != 200:
        print("failed to delete message")

if __name__ == "__main__":
    asyncio.run(check_if_live())
