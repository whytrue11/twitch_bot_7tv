import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

SEVEN_TV_SET_ID = os.getenv("SEVEN_TV_SET_ID")
SEVEN_TV_TOKEN = os.getenv("SEVEN_TV_TOKEN")


class ActiveEmote:
    def __init__(self, id, alias):
        self.id = id
        self.alias = alias
        self.start_time = time.time()


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
    print(f"Request to add 7tv emote: {payload}")
    print(f"Response to add 7tv emote: {response.text}")
    if response.text.__contains__("BAD_REQUEST"):
        print("Error to add 7tv emote")
        return False
    return True


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
    print(f"Response to remove 7tv emote: {response.text}")
    if response.text.__contains__("BAD_REQUEST"):
        print("Error to remove 7tv emote")
        return False
    return True
