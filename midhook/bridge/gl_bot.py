from typing import Callable, Dict, List, Tuple, Type


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


class GLBot:
    _commands: Dict[str, Command] = {}
    _notifiers = {}

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

    def process(self, message):
        """
        Process commands received from lark chat
        """
        text = message.content.get("text", None)
        mentions = message.mentions

        cmd, arg_list = self._validate_input(text, mentions)
        cmd_cls = self._commands[cmd]

        if cmd_cls == Help:
            doc = [f"{c_cls.help}" for c_cls in self._commands.values()]
            return "\n".join(doc)

        try:
            res = cmd_cls().execute(message, arg_list)
        except Exception:
            raise GLBotInvalidCommand("Invalid command")

        return res

    def _validate_input(self, text, mentions) -> Tuple[str, List[str]]:
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
