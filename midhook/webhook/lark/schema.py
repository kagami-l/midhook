import json
from enum import Enum
from typing import Callable, Dict, List

from pydantic import BaseModel, Extra, validator


class EventType(Enum):
    # Currently only support receiving message
    ReceiveMsg = "im.message.receive_v1"
    Other = "Other"


class LarkBase(BaseModel):
    class Config:
        extra = Extra.allow


class Header(LarkBase):
    event_type: EventType

    @validator("event_type", pre=True)
    def convert_type(cls, value):
        event = EventType.Other
        try:
            event = EventType(value)
        except Exception:
            pass
        return event


class Event(LarkBase):
    pass


class MentionIDs(LarkBase):
    user_id: str
    union_id: str
    open_id: str


class Mention(LarkBase):
    name: str
    key: str
    id: MentionIDs


class Message(LarkBase):
    chat_id: str
    chat_type: str
    content: Dict
    message_type: str
    message_id: str
    mentions: List[Mention] = []

    @validator("content", pre=True)
    def load_content(cls, value):
        return json.loads(value)


class MsgEvent(Event):
    message: Message


class Payload(LarkBase):
    header: Header
    event: Event


EventHandler = Callable[[Event], str]
