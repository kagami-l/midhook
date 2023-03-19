from pydantic import BaseModel
from collections import defaultdict
from typing import Callable, Type, List, Tuple
from abc import ABC, abstractmethod
from midhook.bridge.notification import NotificationType, NotiMessageMaker, _at_user
from midhook.webhooks.lark.sender import MessageSender
from midhook.bridge.storage import bot_data

# # TODO: 持久化bot的设置
# BOT_DATA = {
#     # 记录项目更新与需要通知的群聊
#     "gitlab_proj_id_to_lark_chat_ids": defaultdict(set),
#     # 记录gitlab用户与lark用户的映射
#     # gitlab user id -> (lark user id, lark name)
#     "user_id_gitlab_to_lark": {},
# }


# def set_project_to_chat(project_id: str, chat_id: str):
#     BOT_DATA["gitlab_proj_id_to_lark_chat_ids"][project_id].add(chat_id)


# def bot_data.get_chats_of_project(project_id: str) -> List[str]:
#     return BOT_DATA["gitlab_proj_id_to_lark_chat_ids"].get(project_id, [])


# def remove_project_to_chat(project_id: str, chat_id: str):
#     BOT_DATA["gitlab_proj_id_to_lark_chat_ids"][project_id].discard(chat_id)


# def clear_project_chat():
#     BOT_DATA["gitlab_proj_id_to_lark_chat_ids"].clear()


# def get_chat_projects(chat_id: str) -> List[str]:
#     res = set()
#     for proj, chats in BOT_DATA["gitlab_proj_id_to_lark_chat_ids"].items():
#         if chat_id in chats:
#             res.add(proj)

#     return list(res)


# def set_gitlab_user_to_lark_user(
#     gitlab_user_id: str, lark_user_id: str, lark_user_name: str
# ):
#     BOT_DATA["user_id_gitlab_to_lark"][gitlab_user_id] = (lark_user_id, lark_user_name)


# def get_lark_user_from_gitlab_user_id(gitlab_user_id: str) -> Tuple[str, str]:
#     user_id, user_name = BOT_DATA["user_id_gitlab_to_lark"].get(
#         gitlab_user_id, ("", f"gitlab_user_{gitlab_user_id}")
#     )
#     return user_id, user_name

class GLBotNotACommand(Exception):
    pass


class GLBotInvalidCommand(Exception):
    pass


class Command:
    cmd: str
    help: str

    @abstractmethod
    def execute(self, message, arg_list):
        pass


class SetProject(Command):
    cmd = "#set_proj"
    help = "#set_proj <project_id>, 设置在当前群聊中需要通知的gitlab项目"

    def execute(self, message, arg_list):
        project_id = arg_list[0]
        chat_id = message.chat_id
        bot_data.set_project_to_chat(project_id, chat_id)

        return "已设置"


class ListProject(Command):
    cmd = "#ls_proj"
    help = "#ls_proj, 列出当前群聊中会进行通知的gitlab项目"

    def execute(self, message, arg_list):
        chat_id = message.chat_id
        projects = bot_data.get_chat_projects(chat_id)

        return ", ".join(projects) or "未设置需通知的项目"


class RemoveProject(Command):
    cmd = "#rm_proj"
    help = "#rm_proj <project_id>, 移除在当前群聊中需要通知的项目"

    def execute(self, message, arg_list):
        project_id = arg_list[0]
        chat_id = message.chat_id
        bot_data.remove_project_from_chat(project_id, chat_id)

        return "已移除"


class RemoveAllNotification(Command):
    cmd = "#rm_all_notification"
    help = "#rm_all_notification, ！移除所有群聊中的所有项目通知"

    def execute(self, message, arg_list):
        bot_data.remove_all_projects_chats()

        return "解除所有项目与所有群聊的通知"


class SetUser(Command):
    cmd = "#set_user"
    help = "#set_user @<lark_user> <gitlab_user_id>, 关联gitlab用户id与lark用户id"

    def execute(self, message, arg_list):
        lark_user_id = None
        lark_user_name = ""
        lark_user = arg_list[0]
        for m in message.mentions:
            if m.key == lark_user:
                lark_user_id = m.id.user_id
                lark_user_name = m.name
                break
        assert lark_user_id

        gitlab_user_id = arg_list[1]

        bot_data.set_user_account(gitlab_user_id, lark_user_id, lark_user_name)

        return "已设置"


class RemoveUser(Command):
    cmd = "#rm_user"
    help = "#rm_user @<lark_user>, 移除可被通知的lark用户"

    def execute(self, message, arg_list):
        lark_user_id = None
        lark_user = arg_list[0]
        for m in message.mentions:
            if m.key == lark_user:
                lark_user_id = m.id.user_id
                break
        assert lark_user_id

        bot_data.remove_lark_user(lark_user_id)
        return "已移除"


class ListUser(Command):
    cmd = "#ls_user"
    help = "#ls_user, 列出所有可被通知的lark用户与其对应的gitlab用户id"

    def execute(self, message, arg_list) -> List[str]:
        res = []
        for g_id, l_id, l_name in bot_data.get_all_user_accounts():
            res.append(f"{l_name}({l_id}) -> {g_id}")

        return "\n".join(res) or "未设置用户关联"


class RemoveAll(Command):
    cmd = "#rm_all"
    help = "#rm_all, 清空所有设置"

    def execute(self, message, arg_list):
        bot_data.drop()
        return "已清空所有设置"

class Help(Command):
    cmd = "#help"
    help = "#help, 列出所有命令"

    def execute(self, message, arg_list):
        pass


def notify_mr_update_reviewers(project_id, mr_url, reviewer_ids):
    lark_reviewers: List[Tuple[str, str]] = bot_data.get_lark_user_from_gitlab_user(
        reviewer_ids
    )

    usr_str = " ".join((_at_user(r[0], r[1]) for r in lark_reviewers))
    content = f"以下MR的Reviewers更新为\n {usr_str}\n请适时Review\n{mr_url}"

    chat_ids = bot_data.get_chats_of_project(project_id)

    m_sender = MessageSender()
    for chat_id in chat_ids:
        m_sender.send(content, chat_id)

    return "Sent notifications"


def notify_mr_add_comment(project_id, mr_url, commenter_id, assignee_ids, reviewer_ids):
    # AT the assignees and reviewers of the MR except the commenter
    at_user_ids = set(assignee_ids + reviewer_ids)
    at_user_ids.discard(commenter_id)
    commenter = bot_data.get_lark_user_from_gitlab_user([commenter_id])[0]

    lark_users: List[Tuple[str, str]] = bot_data.get_lark_user_from_gitlab_user(
        at_user_ids
    )
    at_str = " ".join((_at_user(r[0], r[1]) for r in lark_users))

    content = f"{commenter[1]}评论了以下MR，请相关同学注意查看\n{at_str}\n{mr_url}"

    chat_ids = bot_data.get_chats_of_project(project_id)

    m_sender = MessageSender()
    for chat_id in chat_ids:
        m_sender.send(content, chat_id)

    return "Sent notifications"


def notify_mr_merged(project_id, mr_url, assignee_ids, reviewer_ids):
    lark_users: List[Tuple[str, str]] = bot_data.get_lark_user_from_gitlab_user(
        assignee_ids + reviewer_ids
    )

    usr_str = " ".join((_at_user(r[0], r[1]) for r in lark_users))
    content = f"以下MR已合并\n{usr_str} Good Job (๑•̀ᴗ•́)b☆ \n{mr_url}"

    chat_ids = bot_data.get_chats_of_project(project_id)

    m_sender = MessageSender()
    for chat_id in chat_ids:
        m_sender.send(content, chat_id)

    return "Sent notifications"


def nofity_mr_approved(project_id, mr_url, approver_id, assignee_ids):
    approver = bot_data.get_lark_user_from_gitlab_user([approver_id])[0]

    assignees: List[Tuple[str, str]] = bot_data.get_lark_user_from_gitlab_user(
        assignee_ids
    )

    usr_str = " ".join((_at_user(r[0], r[1]) for r in assignees))
    content = f"{approver[1]} Approve了你的MR {usr_str}\n请注意查看\n{mr_url}"

    chat_ids = bot_data.get_chats_of_project(project_id)

    m_sender = MessageSender()
    for chat_id in chat_ids:
        m_sender.send(content, chat_id)

    return "Sent notifications"


class GLBot:
    _commands = {}
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

    def __init__(self) -> None:
        pass

    def __call__(self, *args, **kwargs):
        return self.handler(*args, **kwargs)

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
        except Exception as e:
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
