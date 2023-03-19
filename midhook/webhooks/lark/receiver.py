from typing import Dict, Callable
from pydantic import BaseModel, Extra, validator, root_validator
from enum import Enum
from typing import List, Optional, Dict, Tuple
import json

from midhook.bridge.gitlab_lark import GLBot, GLBotInvalidCommand, GLBotNotACommand
from midhook.webhooks.lark.sender import ReplySender



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
        except:
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


class Receiver:
    def __init__(self) -> None:
        self._handlers: Dict[EventType, EventHandler] = {}

    @classmethod
    def parse_payload(cls, body: Dict):
        payload = Payload.parse_obj(body)

        return payload.header, payload.event

    def register(self, event_type: EventType) -> Callable:
        def decorator(func: Callable):
            self._handlers[event_type] = func
            return func

        return decorator

    def handle_event(self, header: Header, event: Event):
        event_handler = self._handlers.get(header.event_type, None)
        if not event_handler:
            return "Don't care"

        return event_handler(event)


receiver = Receiver()


@receiver.register(EventType.ReceiveMsg)
def message_receive_handler(event: Event) -> str:
    msg_event = MsgEvent.parse_obj(event)
    message = msg_event.message
    content = message.content
    text = message.content.get("text", None)
    
    sender = ReplySender()
    if not text or len(message.mentions) < 1:
        sender.send_reply(message.message_id, "Talk is cheap, give me your command.")

    bot = GLBot()

    result = None
    try:
        result = bot.process(message)
    except Exception as e:
        sender.send_reply(message.message_id, str(e))

    if result is not None:
        sender.send_reply(message.message_id, result)
    return "OK"


@receiver.register(EventType.Other)
def unsupported_event_handler(event: Event):
    pass
