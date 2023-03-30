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

    bot = GLBot()

    result = bot.peek_message(message)

    return result


@receiver.register(EventType.Other)
def unsupported_event_handler(event: Event):
    pass
