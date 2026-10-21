import asyncio
import json
import sys
import time
from typing import Any

import logs
import requests
import spotify
import twitch
import vrchatosc
import websockets
from config import BOT_USER_ID, EVENTSUB_WEBSOCKET_URL, WIDGET_WS_PORT
from llm import Llm
from tasks import TaskList
from widget import websocket_server
import jev_vetting

CHAT_LOG = logs.ChatLog()
TIME_LOG = logs.TimeLog()
WIDGET_SERVER = websocket_server()
CW_TASK_MANAGER = TaskList(WIDGET_SERVER)
LLM = Llm(CHAT_LOG, TIME_LOG)
HIDDEN_COMMANDS = ("botoerees", "ratemychatsevil", "setpersona")
commands = {}
_tasks = set()

# Decorator stuff

def command(*names):
    def register(func):
        for name in names:
            commands[name] = func
        return func
    return register


# ---------- commands ----------
@command('help')
async def cmd_help(msg_id, **_):
    helpstr = ""
    for item in commands:
        if item not in HIDDEN_COMMANDS:
            helpstr += f"{item} | "
    await twitch.send_chat_message(f'Here is a list of all commands: {helpstr}', parent_id=msg_id)

@command('newtask')
async def cmd_newtask(name, params, msg_id, **_):
    if not params:
        return await twitch.send_chat_message("To create a task, you must give it a name, example: '!newtask Homework'", parent_id=msg_id)
    await CW_TASK_MANAGER.add_task(name, ' '.join(params), msg_id)

@command('deltask')
async def cmd_deltask(name, params, msg_id, **_):
    if not params:
        return await twitch.send_chat_message("To delete a task, you must specify the name, example: '!deltask Homework'", parent_id=msg_id)
    await CW_TASK_MANAGER.delete_task(name, ' '.join(params), msg_id)

@command('fintask')
async def cmd_fintask(name, params, msg_id, **_):
    if not params:
        return await twitch.send_chat_message("To finish a task, you must specify the name, example: '!fintask Homework'", parent_id=msg_id)
    await CW_TASK_MANAGER.complete_task(name, ' '.join(params), msg_id)

@command('discord')
async def cmd_discord(name, msg_id, **_):
    await twitch.send_chat_message('Discord link: https://discord.gg/9NT38ndXZN', parent_id=msg_id)

@command('lurk')
async def cmd_lurk(name, msg_id, **_):
    await twitch.send_chat_message('Thanks for coming! I hope you have a good time here in the stream I greatly appreciate your attendance :3', parent_id=msg_id)

@command('taskhelp')
async def cmd_taskhelp(name, msg_id, **_):
    await twitch.send_chat_message('''TaskList commands are:
			| !newtask - to create a new task
			| !deltask - to delete a task
			| !fintask - to complete a task ''', parent_id=msg_id)


@command('meow')
async def cmd_meow(msg_id, **_):
    await twitch.send_chat_message(f':3 has been said {CHAT_LOG.check_word_count(":3")} times', parent_id=msg_id)


@command('rawr')
async def cmd_rawr(msg_id, **_):
    await twitch.send_chat_message(f'rawr XD has been said {CHAT_LOG.check_word_count("rawr xd")} times', parent_id=msg_id)

@command('messagecount')
async def cmd_messagecount(name, userid, msg_id, **_):
    await twitch.send_chat_message(f'Your message count is: {CHAT_LOG.check_chatter_message_count(userid)}', parent_id=msg_id)


@command('wordcount')
async def cmd_wordcount(name, params, msg_id, **_):
    if not params:
        return await twitch.send_chat_message("to check for words, you need to add the word, e.g. '!wordcount hello'", parent_id=msg_id)
    phrase = ' '.join(params)
    count = CHAT_LOG.check_word_count(phrase)
    if count > 0:
        await twitch.send_chat_message(f'[{phrase}] Has been said [{count}] times!', parent_id=msg_id)
    else:
        await twitch.send_chat_message(f'[{phrase}] Has not been said EVER :(', parent_id=msg_id)

@command('mywordcount')
async def cmd_mywordcount(name, params, userid, msg_id, **_):
    if not params:
        return await twitch.send_chat_message("to check for words, you need to add the word, e.g. '!mywordcount hello'", parent_id=msg_id)
    phrase = ' '.join(params)
    count = CHAT_LOG.check_word_count(phrase, userid)
    if count > 0:
        await twitch.send_chat_message(f'you have said [{phrase}] [{count}] times!', parent_id=msg_id)
    else:
        await twitch.send_chat_message(f'[{phrase}] You have never said THIS :(', parent_id=msg_id)

@command('wands')
async def cmd_wands(name, msg_id, **_):
    await twitch.send_chat_message('Steps current wands can be seen at: https://onlywands.com/streamer/steptoerees', parent_id=msg_id)

@command('watchtime')
async def cmd_watchtime(name, params, userid, msg_id, **_):
    if not params:
        watch_time = TIME_LOG.check_watch_time(userid)
        if watch_time is None:
            return await twitch.send_chat_message('You have either watched for < 1 minute, the bot has broken, or you arent real', parent_id=msg_id)
        hours, mins = watch_time
        if hours == 0:
            await twitch.send_chat_message(f'you have watched steps streams for {mins} minutes', parent_id=msg_id)
        elif mins == 0:
            await twitch.send_chat_message(f'you have watched steps streams for {hours} hours', parent_id=msg_id)
        else:
            await twitch.send_chat_message(f'you have watched steps streams for {hours} hours and {mins} minutes', parent_id=msg_id)
    else:
        alternate_user = params[0][1:]
        newuserid = await twitch.get_userid(alternate_user)
        watch_time = TIME_LOG.check_watch_time(newuserid)
        print(alternate_user, "|", newuserid)
        if watch_time is None:
            return await twitch.send_chat_message(f'{alternate_user} hase either watched for < 1 minute, the bot has broken, or you arent real', parent_id=msg_id)
        hours, mins = watch_time
        if hours == 0:
            await twitch.send_chat_message(f'{alternate_user} has watched steps streams for {mins} minutes', parent_id=msg_id)
        elif mins == 0:
            await twitch.send_chat_message(f'{alternate_user} has watched steps streams for {hours} hours', parent_id=msg_id)
        else:
            await twitch.send_chat_message(f'{alternate_user} has watched steps streams for {hours} hours and {mins} minutes', parent_id=msg_id)

@command('btw', 'botoerees')
async def cmd_btw(name, params, msg_id, userid, reply_obj=None, **_):
    if not params:
        return await twitch.send_chat_message('ts is a goofy ahh command, ask a question or say smth after !btw', parent_id=msg_id)

    base_cooldown = 60
    last_call = await TIME_LOG.get_user_llm_cooldown(userid)
    if last_call != 0:
        time_since = (time.monotonic() - last_call)
        time_left = base_cooldown - time_since
        if time_left > 0:
            return await twitch.send_chat_message(f'You are on btw cooldown. Please wait {time_left:.0f} seconds before using this command again.', parent_id=msg_id)
    await TIME_LOG.update_user_llm_cooldown(userid)

    phrase = ' '.join(params)

    response = await LLM.twitch_reply(name, phrase, reply_obj, userid)

    await twitch.send_chat_message(response, parent_id=msg_id)

@command('ratemychats')
async def cmd_rate_chatter(name, userid, msg_id, EVIL=False, **_):
    response = await LLM.rate_chatter(name, userid, EVIL=EVIL)

    await twitch.send_chat_message(f'{response}', parent_id=msg_id)
    await asyncio.sleep(3)
    await twitch.send_chat_message("""P.S. This command is entirely for fun and does not represent how step thinks of
    you nor does it objectively represent quality, again, this is a silly
    command and should not be taken seriously.""", parent_id=msg_id)

@command('ratemychatsevil')
async def cmd_rate_chatter_evil(name, userid, msg_id, EVIL=True, **_):
    await cmd_rate_chatter(name, userid, msg_id, EVIL=True)

@command('currentsong')
async def cmd_current_song(msg_id, **_):
    song_name,artist = await spotify.get_current_song()
    if song_name != None:
        await twitch.send_chat_message(f'The current song is: {song_name} by {artist}', parent_id=msg_id)
    else:
        await twitch.send_chat_message('There is no song playing on spotify rn', parent_id=msg_id)

@command('currentpersona')
async def cmd_current_persona(msg_id, **_):
    current_persona = await LLM.get_current_persona()
    await twitch.send_chat_message(f'Current persona: {current_persona}', parent_id=msg_id)

@command('setpersona')
async def cmd_set_persona(msg_id, userid, params, **_):
    if not await twitch.if_moderator(userid):
        return
    if not params:
            return await twitch.send_chat_message('Add a persona nerd', parent_id=msg_id)
    persona = await LLM.set_persona(params[0])
    if persona:
        await twitch.send_chat_message(f'Persona set to: {params[0]}', parent_id=msg_id)
    else:
        await twitch.send_chat_message(f'Failed to set persona: {params[0]}', parent_id=msg_id)



def parse_command(msg):
    txt = msg.strip()
    if "@botoerees" in txt:
        parts = txt[1:].split()
        if not parts:
            return None
        parts[0] = "botoerees"
        return parts[0].lower(), parts[1:]
    if not (txt.startswith('!') ):
        return None
    parts = txt[1:].split()
    if not parts:
        return None
    return parts[0].lower(), parts[1:]

# ---------- Handle Redeems -----------

async def song_request(songid, event_id, reward_id):
    success = False
    try:
        track_info: Any = await spotify.saftey_check(songid)
        warnings = track_info[0]
        name = track_info[1]
        artist = track_info[2]
        songid = track_info[3]
        match warnings:
            case "explicit":
                await twitch.send_chat_message("Sorry, songs tagged explicit are denied")
            case "long":
                await twitch.send_chat_message("Sorry, songs over 6 minutes are denied")
            case "Bad Request":
                await twitch.send_chat_message("Sorry, thats an invalid song ID")
            case "banned_song":
                await twitch.send_chat_message("Sorry, that song is banned")
            case "extremely_banned_song":
                await twitch.send_chat_message("This song is so incredibly banned, that i have a specific error message for it. never request this again.")
                success = True
            case "banned_artist":
                await twitch.send_chat_message("Sorry, that song is banned")
            case "THIS IS NOT GOOD":
                await twitch.send_chat_message("Uh oh, the bot is having some trouble")
            case _:
                await spotify.add_req_to_queue(songid)
                await twitch.send_chat_message(f"{name} by {artist} added to queue!")
                success = True
    except Exception as err:  # noqa: BLE001
        print(err)
        await twitch.send_chat_message("Something went Wrong")
    if success:
        await twitch.update_redemption(reward_id, event_id, 'FULFILLED')
    else:
        await twitch.update_redemption(reward_id ,event_id, 'CANCELED')



# ---------- eventsub client ----------

async def handle_event(data, vrcclient):
    msg_type = data['metadata']['message_type']
    if msg_type == 'session_welcome':
        websocket_session_id = data['payload']['session']['id']
        live:bool = await twitch.check_if_live()
        await TIME_LOG.set_streaming(live)
        await twitch.register_eventsub_listeners(websocket_session_id)

    if msg_type == 'notification':
        match data['metadata']['subscription_type']:
            case 'channel.chat.message':
                    event = data['payload']['event']
                    await handle_message(event, vrcclient)

            case 'channel.channel_points_custom_reward_redemption.add':
                event = data['payload']['event']
                await handle_redeem(event)

            case 'stream.online':
                await TIME_LOG.set_streaming(True)

            case 'stream.offline':
                await twitch.send_chat_message("STREAM END")
                await TIME_LOG.set_streaming(False)


# ---------- event handlers -------------
#
#
async def handle_message(event, vrcclient):
    name = event['chatter_user_login']
    message = event['message']['text']
    msg_id = event['message_id']
    userid = event['chatter_user_id']
    reply_obj = event.get('reply')

    CHAT_LOG.add_to_chat_log(name, message, msg_id, userid, reply_obj)
    vrcclient.send_chatbox_message(f"{name}: {message}")
    print(reply_obj)
    print(f'CHR :{name}')
    print(f'MSG :{message}')

    if not await jev_vetting.vet_message(message):
        await twitch.delete_message(msg_id)
        return
    
    if userid == BOT_USER_ID:
        return

    if reply_obj and reply_obj['parent_user_id'] == BOT_USER_ID:
        t = asyncio.create_task(cmd_btw(name, message.split(), msg_id, userid, reply_obj))
        _tasks.add(t)
        t.add_done_callback(_tasks.discard)
    else:
        parsed = parse_command(message)
        if not parsed:
            return
        handler = commands.get(parsed[0])
        if not handler:
            return
        t = asyncio.create_task(handler(name=name, params=parsed[1], userid=userid, reply_obj = reply_obj, msg_id=msg_id))
        _tasks.add(t)
        t.add_done_callback(_tasks.discard)

async def handle_redeem(event):
    userid = event["user_id"]  # noqa: F841
    username = event["user_name"]  # noqa: F841
    event_id = event["id"]
    reward_id = event['reward']['id']
    userinput = event["user_input"]

    # IMPORTANT
    # WHEN ADDING MORE REDEEMS, SWITCH TO DICT LIKE COMMANDS
    if reward_id == "b881a595-7e61-4d20-93e1-b6f32ae771c4": # song request redeem ID
        await song_request(userinput, event_id, reward_id)

# ----------------------------------------------------


async def eventsub_client(vrcclient):
    while True:
        try:
            async with websockets.connect(EVENTSUB_WEBSOCKET_URL) as ws:
                print('WebSocket connection opened to ' + EVENTSUB_WEBSOCKET_URL)
                async for raw in ws:
                    try:
                        await handle_event(json.loads(raw), vrcclient)
                    except (json.JSONDecodeError, KeyError, requests.exceptions.RequestException) as err:
                        print('Error handling message:', err, file=sys.stderr)
        except (websockets.exceptions.WebSocketException, OSError) as err:
            print('WebSocket closed:', err, file=sys.stderr)
        await asyncio.sleep(5)


async def periodic(seconds, fn):
    while True:
        await asyncio.sleep(seconds)
        try:
            result = fn()
            if asyncio.iscoroutine(result):
                await result
        except (OSError, KeyError, ValueError) as err:
            print(err, file=sys.stderr)


async def main():
    twitch.get_auth()
    vrcclient = vrchatosc.Client()
    async with websockets.serve(WIDGET_SERVER.widget_connection, '127.0.0.1', WIDGET_WS_PORT):
        print(f'Widget WebSocket server listening on port {WIDGET_WS_PORT}')
        await asyncio.gather(
            eventsub_client(vrcclient),
            periodic(60, CHAT_LOG.save_chat_log),
            periodic(60, TIME_LOG.log_watch_time),
        )


if __name__ == '__main__':
    asyncio.run(main())
