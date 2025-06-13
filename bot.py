import asyncio

from twitchAPI.chat import Chat, EventData, ChatMessage, ChatCommand
from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.helper import first
from twitchAPI.oauth import UserAuthenticator
from twitchAPI.object.eventsub import ChannelPointsCustomRewardRedemptionAddEvent
from twitchAPI.twitch import Twitch
from twitchAPI.type import AuthScope, ChatEvent
import os
from dotenv import load_dotenv

load_dotenv()

APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
#USER_SCOPE = [AuthScope.CHAT_READ, AuthScope.CHAT_EDIT, AuthScope.CHANNEL_READ_REDEMPTIONS]
USER_SCOPE = AuthScope.__members__.values()
TARGET_CHANNEL = os.getenv("TARGET_CHANNEL")
BOT_NAME = os.getenv("BOT_NAME")
SEVEN_TV_SET_ID = os.getenv("SEVEN_TV_SET_ID")
SEVEN_TV_TOKEN = os.getenv("SEVEN_TV_TOKEN")


# region 7tv
import requests


def add_7tv_emote(emote_alias: str, emote_id: str):
    """
    Добавляет эмоут в набор на 7TV

    Параметры:
    - emote_alias: псевдоним эмоута (например, "кисс")
    - emote_id: ID эмоута (например, "01F5VW2TKR0003RCV2Z6JBHCST")
    - set_id: ID набора эмоутов (например, "01JXB28M4B0BN5ZFZKDHTFH8BM")
    """
    url = "https://api.7tv.app/v4/gql"
    headers = {
        "Authorization": f"Bearer {SEVEN_TV_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "operationName": "AddEmoteToSet",
        "query": """mutation AddEmoteToSet($setId: Id!, $emote: EmoteSetEmoteId!) {
            emoteSets {
                emoteSet(id: $setId) {
                    addEmote(id: $emote) {
                        id
                        __typename
                    }
                    __typename
                }
                __typename
            }
        }""",
        "variables": {
            "emote": {
                "alias": emote_alias,
                "emoteId": emote_id
            },
            "setId": SEVEN_TV_SET_ID
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print("Error to add 7tv emote")


def remove_7tv_emote(emote_id: str):
    """
    Удаляет эмоут из набора на 7TV

    Параметры:
    - emote_id: ID эмоута (например, "01F5VW2TKR0003RCV2Z6JBHCST")
    - set_id: ID набора эмоутов (например, "01JXB28M4B0BN5ZFZKDHTFH8BM")
    """
    url = "https://api.7tv.app/v4/gql"
    headers = {
        "Authorization": f"Bearer {SEVEN_TV_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "operationName": "RemoveEmoteFromSet",
        "query": """mutation RemoveEmoteFromSet($setId: Id!, $emote: EmoteSetEmoteId!) {
            emoteSets {
                emoteSet(id: $setId) {
                    removeEmote(id: $emote) {
                        id
                        __typename
                    }
                    __typename
                }
                __typename
            }
        }""",
        "variables": {
            "emote": {
                "emoteId": emote_id
            },
            "setId": SEVEN_TV_SET_ID
        }
    }

    response = requests.post(url, json=payload, headers=headers)
    if response.status_code != 200:
        print("Error to remove 7tv emote")
#endregion

# this will be called when the event READY is triggered, which will be on bot start
async def on_ready(ready_event: EventData):
    print('Bot is ready for work, joining channels')
    # join our target channel, if you want to join multiple, either call join for each individually
    # or even better pass a list of channels as the argument
    await ready_event.chat.join_room(TARGET_CHANNEL)
    # you can do other bot initialization things in here


# this will be called whenever a message in a channel was send by either the bot OR another user
async def on_message(msg: ChatMessage):
    print(f'in {msg.room.name}, {msg.user.name} said: {msg.text}')


# this will be called whenever the !reply command is issued
async def test_command(cmd: ChatCommand):
    if len(cmd.parameter) == 0:
        await cmd.reply('you did not tell me what to reply with')
    else:
        await cmd.reply(f'{cmd.user.name}: {cmd.parameter}')


async def on_channel_points_reward(reward: ChannelPointsCustomRewardRedemptionAddEvent):
    if reward.event.id == "7tv emote":
        print("7tv activated")
    print(f"New reward redeemed by {reward.event.user_name}!")
    print(f"Reward: {reward.event.id}")
    print(f"User input: {reward.event.message.text}")


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
    chat.register_command('reply', test_command)
    # we are done with our setup, lets start this bot up!
    chat.start()

    target_channel_user = await first(twitch.get_users(logins=TARGET_CHANNEL))
    print(f"User: {target_channel_user.login}, id: {target_channel_user.id}")
    bot_user = await first(twitch.get_users(logins=BOT_NAME))
    print(f"User: {bot_user.login}, id: {bot_user.id}")
    # rewards
    eventsub = EventSubWebsocket(twitch)
    eventsub.start()
    await eventsub.listen_channel_points_custom_reward_redemption_add(target_channel_user.id, on_channel_points_reward)
    #await event_sub.listen_channel_points_automatic_reward_redemption_add_v2(target_channel_user.id, on_channel_points_reward)

    # lets run till we press enter in the console
    try:
        input('press ENTER to stop\n')
    finally:
        # now we can close the chat bot and the twitch api client
        chat.stop()
        await eventsub.stop()
        await twitch.close()


# lets run our setup
asyncio.run(run())
