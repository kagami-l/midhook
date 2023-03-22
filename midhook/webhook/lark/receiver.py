from typing import Callable, Dict

from midhook.bridge.gl_bot import GLBot
from midhook.webhook.lark.schema import (
    Event,
    EventHandler,
    EventType,
    Header,
    MsgEvent,
    Payload,
)
from midhook.webhook.lark.sender import ReplySender


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
    text = message.content.get("text", None)

    sender = ReplySender()
    if not text or len(message.mentions) < 1:
        sender.send(message.message_id, "Talk is cheap, give me your command.")

    bot = GLBot()

    result = None
    try:
        result = bot.process(message)
    except Exception as e:
        sender.send(message.message_id, str(e))

    if result is not None:
        sender.send(message.message_id, result)
    return "OK"


@receiver.register(EventType.Other)
def unsupported_event_handler(event: Event):
    pass
