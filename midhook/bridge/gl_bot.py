from typing import Callable, Dict, List, Tuple, Type

from loguru import logger

from midhook.bridge.command import (
    Command,
    GLBotInvalidCommand,
    GLBotNotACommand,
    Hello,
    Help,
    ListProject,
    ListUser,
    RemoveAll,
    RemoveAllNotification,
    RemoveProject,
    RemoveUser,
    SetProject,
    SetUser,
)
from midhook.bridge.notification import (
    NotificationType,
    nofity_mr_approved,
    notify_mr_add_comment,
    notify_mr_merged,
    notify_mr_update_reviewers,
)
from midhook.config import GLBotConfig
from midhook.webhook.lark.schema import Message
from midhook.webhook.lark.sender import ReplySender


class GLBot:
    _commands: Dict[str, Command] = {}
    _notifiers = {}

    @property
    def name(self):
        return GLBotConfig.bot_name

    @property
    def open_id(self):
        return GLBotConfig.open_id

    @classmethod
    def register_command(cls, cmd_cls: Type[Command]):
        cls._commands[cmd_cls.cmd] = cmd_cls

    @classmethod
    def register_notifier(cls, noti_type: NotificationType, notifier: Callable):
        cls._notifiers[noti_type] = notifier

    @classmethod
    def get_notifier(cls, noti_type: NotificationType):
        return cls._notifiers.get(noti_type, None)

    def forward(self, noti_type: NotificationType, project_id: str, *args):
        notifier = self.get_notifier(noti_type)
        if not notifier:
            return f"No Notifier for {noti_type}"

        res = notifier(project_id, *args)

        return res

    def peek_message(self, message: Message) -> str:
        """
        Peek message to see how to process it
        """
        if not self._is_at_me(message):
            logger.info(f"Not at me, ignore message: {message.message_id}")
            return "Do not care"

        sender = ReplySender()
        text = message.content.get("text", None)
        if not text:
            sender.send(message.message_id, "Talk is cheap, give me your command.")
            return "Replied"

        try:
            result = self._process(message)
            if result is not None:
                sender.send(message.message_id, result)

        except Exception as e:
            logger.info(e)
            sender.send(message.message_id, str(e))

        return "Processed"

    def _is_at_me(self, message: Message):
        for mention in message.mentions:
            if mention.name == self.name and mention.id.open_id == self.open_id:
                return True

        return False

    def _process(self, message):
        """
        Process commands received from lark chat
        """
        text = message.content.get("text", None)
        mentions = message.mentions

        cmd, arg_list = self._validate_command(text, mentions)
        cmd_cls = self._commands[cmd]

        if cmd_cls == Help:
            doc = [f"{c_cls.help}" for c_cls in self._commands.values()]
            return "\n".join(doc)

        try:
            res = cmd_cls().execute(message, arg_list)
            return res
        except Exception as e:
            logger.info(e)
            raise GLBotInvalidCommand("Invalid command")

    def _validate_command(self, text, mentions) -> Tuple[str, List[str]]:
        lst = text.strip().split(" ")

        if (
            len(lst) < 2
            or lst[0] != "@_user_1"
            or not lst[1].startswith("#")
            or lst[1] not in self._commands
        ):
            raise GLBotNotACommand("Not a command")

        return lst[1], lst[2:]


GLBot.register_command(Help)
GLBot.register_command(Hello)
GLBot.register_command(SetProject)
GLBot.register_command(ListProject)
GLBot.register_command(RemoveProject)
GLBot.register_command(RemoveAllNotification)
GLBot.register_command(SetUser)
GLBot.register_command(RemoveUser)
GLBot.register_command(ListUser)
GLBot.register_command(RemoveAll)

GLBot.register_notifier(NotificationType.MRUpdateReviewers, notify_mr_update_reviewers)
GLBot.register_notifier(NotificationType.MRAddComment, notify_mr_add_comment)
GLBot.register_notifier(NotificationType.MRMerged, notify_mr_merged)
GLBot.register_notifier(NotificationType.MRApproved, nofity_mr_approved)
