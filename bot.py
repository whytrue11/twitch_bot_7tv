import asyncio
import os
import random
import time

from dotenv import load_dotenv
from twitchAPI.chat import Chat, EventData, ChatMessage, ChatCommand
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope, ChatEvent

from sevenTV import add_7tv_emote, ActiveEmote, remove_7tv_emote

load_dotenv()

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")
USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT]
EXPIRE_EMOTE_TIME_IN_SECONDS = 20.0

# region 7tv
seven_tv_emotes_pool = [
    "01GX9BDHSR000DACH8GVDFE60G",  # taa
    "01J0ZYSN700003YPW34K535MQD",  # dura
    "01HNTK4C40000FG935RNS75ZEV",  # Durak66
    "01GRZ9G7GG000F4NDY99DZYBY4",  # Villager
    "01J399FVVR00046F97SBJG388M",  # ore
    "01FNFE2MT80001BCZZ99DVFRZY",  # POOPYPOP
    "01G7HBWGZ8000DJJQKZ99T0A2Y",  # xd
    "01FZJGSGJ8000872XQ7VQHCNRZ"  # XyliGun
]

active_emotes = []

def get_radom_7tv_emote_id():
    emote_id = None
    if seven_tv_emotes_pool:  # Если список не пустой
        emote_id = random.choice(seven_tv_emotes_pool)
        seven_tv_emotes_pool.remove(emote_id)
    return emote_id


def activate_7tv_emote(emote_alias: str, emote_id: str):
    if not add_7tv_emote(emote_alias, emote_id):
        return False
    active_emotes.append(ActiveEmote(emote_id, emote_alias))
    return True


def deactivate_7tv_emote(emote: ActiveEmote):
    if not remove_7tv_emote(emote.id):
        return
    active_emotes.remove(emote)


async def check_emote_expiry():
    """Проверяем и удаляем просроченные смайлы"""
    while True:
        print("Scheduled check expired emotions")
        current_time = time.time()
        emotes_to_remove = []

        # Находим смайлы, у которых истекло время
        for emote in active_emotes:
            if current_time >= emote.start_time + EXPIRE_EMOTE_TIME_IN_SECONDS:
                emotes_to_remove.append(emote)

        # Удаляем их
        for emote in emotes_to_remove:
            deactivate_7tv_emote(emote)
        await asyncio.sleep(EXPIRE_EMOTE_TIME_IN_SECONDS)

# endregion


# this will be called when the event READY is triggered, which will be on bot start
async def on_ready(ready_event: EventData):
    print('Bot is ready for work, joining channels')
    # join our target channel, if you want to join multiple, either call join for each individually
    # or even better pass a list of channels as the argument
    await ready_event.chat.join_room(TARGET_CHANNEL)
    # you can do other bot initialization things in here


# this will be called whenever a message in a channel was send by either the bot OR another user
async def on_message(msg: ChatMessage):
    print(f'{msg.user.name} said: "{msg.text}"')


# this will be called whenever the !reply command is issued
async def test_command(cmd: ChatCommand):
    emote_id = get_radom_7tv_emote_id()
    if emote_id is None:
        await cmd.reply(f"[я бот] все смайлики уже заняты, попробуйте чуть позже")
        return
    elif len(cmd.parameter) == 0 or cmd.parameter == "\U000e0000":
        emote_alias = cmd.user.name
    else:
        emote_alias = cmd.parameter

    if activate_7tv_emote(emote_alias, emote_id):
        await cmd.reply(f"[я бот] добавлен смайлик {emote_alias}")
    else:
        await cmd.reply(f"[я бот] ошибка при добавлении смайлика {emote_alias}")


# this is where we set up the bot
async def run():
    # set up twitch api instance and add user authentication with some scopes
    twitch = await Twitch(APP_ID, APP_SECRET)
    auth = UserAuthenticator(twitch, USER_SCOPE)
    token, refresh_token = await auth.authenticate()
    await twitch.set_user_authentication(token, USER_SCOPE, refresh_token)

    # create chat instance
    chat = await Chat(twitch)

    # register the handlers for the events you want

    # listen to when the bot is done starting up and ready to join channels
    chat.register_event(ChatEvent.READY, on_ready)
    # listen to chat messages
    chat.register_event(ChatEvent.MESSAGE, on_message)
    # you can directly register commands and their handlers, this will register the !reply command
    chat.register_command('7tv', test_command)
    # we are done with our setup, lets start this bot up!
    chat.start()

    expiry_task = asyncio.create_task(check_emote_expiry())

    # Create a future that we'll wait for
    loop = asyncio.get_event_loop()
    stop_future = loop.create_future()
    # Run input in executor (separate thread)
    def check_input():
        input('press ENTER to stop\n')
        loop.call_soon_threadsafe(stop_future.set_result, None)

    await loop.run_in_executor(None, check_input)
    # lets run till we press enter in the console
    try:
        await stop_future
    finally:
        expiry_task.cancel()
        try:
            await expiry_task
        except asyncio.CancelledError:
            pass

        # cleanup emotes and close connections
        for emote in active_emotes:
            deactivate_7tv_emote(emote)
        chat.stop()
        await twitch.close()


# lets run our setup
asyncio.run(run())
