import asyncio
import datetime
import json
import sys
import time
from pathlib import Path

import requests
from config import BOT_USER_ID, BROADCASTER_HEADERS, BROADCASTER_USER_ID


class ChatLog:
    def __init__(self):
        self.log = {'chats': []}
        try:
            self.log = json.loads(Path('log_data/chat_log.json').read_text(encoding='utf-8'))

        except (OSError, json.JSONDecodeError) as err:
            print('Failed to load chat log, starting with an empty log.', err, file=sys.stderr)
            Path('log_data/chat_log.json').write_text(json.dumps(self.log, indent=4), encoding='utf-8')



    def save_chat_log(self):
        try:
            Path('log_data/chat_log.json').write_text(json.dumps(self.log, indent=4), encoding='utf-8')
            print('sucessfully saved chat log')
        except (OSError, TypeError) as err:
            print(err, file=sys.stderr)



    def add_to_chat_log(self, chatter_name, message_text, message_id, user_id, replyobj):
        now = datetime.datetime.now(tz=datetime.timezone.utc)
        self.log['chats'].append({
            'chatid': message_id,
            'userid': user_id,
            'chatter': chatter_name,
            'content': message_text,
            'time': now.strftime('%d/%m/%Y %H:%M:%S'),
            'reply': replyobj
        })


    def check_chatter_message_count(self, userid):
        return sum(1 for chat in self.log['chats'] if chat.get('userid') == userid)


    def check_word_count(self, word, userid=None):
        search = str(word).lower()
        count = 0
        for chat in self.log['chats']:
            content = str(chat['content']).lower()
            name_matches = (userid is None and chat.get('userid') != BOT_USER_ID) or chat.get('userid') == userid
            if search in content and name_matches:
                count += content.count(search)
        return count


    def recent_chat_log(self, userid = None, max_chars=40000):
        chats = self.log['chats']
        results_list = []
        length = 0
        for i in range(len(chats) - 1, -1, -1):

            if i == 0:
                continue

            if userid != None and chats[i].get("userid") != userid:
                continue

            if length >= max_chars:
                break

            if chats[i].get("userid") != BOT_USER_ID:
                entry = {"role": "user", "content": f"{chats[i]["chatter"]}: {chats[i]["content"]}"}

            else:
                entry = {"role": "assistant", "content": f"{chats[i]["content"]}"}

            length += len(json.dumps(entry))
            results_list.insert(0, entry)
        return results_list




class TimeLog:
    def __init__(self):
        self.streaming = False
        try:
            self.time_log = json.loads(Path('log_data/time_log.json').read_text(encoding='utf-8'))
        except (OSError, json.JSONDecodeError):
            sys.exit(1)

        self.llm_cooldown_log = {} #cooldown works by subtracting current time from time stored in cooldown log

    async def update_user_llm_cooldown(self, userid):
        self.llm_cooldown_log[userid] = time.monotonic()

    async def get_user_llm_cooldown(self, userid):
        return self.llm_cooldown_log.get(userid, 0)

    async def set_streaming(self, isLive: bool):
        self.streaming = isLive

    async def log_watch_time(self):
        if self.streaming:
            try:
                resp = await asyncio.to_thread(
                    requests.get,
                    f'https://api.twitch.tv/helix/chat/chatters?broadcaster_id={BROADCASTER_USER_ID}&moderator_id={BROADCASTER_USER_ID}',
                    headers=BROADCASTER_HEADERS,
                )
            except requests.exceptions.RequestException as err:
                print('logWatchTime fetch failed:', err, file=sys.stderr)
                return
            if resp.status_code != 200:
                print('Bad request :(', resp.json(), file=sys.stderr)
                return

            for chatter in resp.json()['data']:
                uid = chatter["user_id"]
                self.time_log[uid] = self.time_log.get(uid, 0) + 1
            Path('log_data/time_log.json').write_text(json.dumps(self.time_log), encoding='utf-8')
        else:
            return

    def check_watch_time(self, uid):
        try:
            time = self.time_log[uid]
            return [time // 60, time % 60]
        except KeyError:
            return None
