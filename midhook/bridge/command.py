from abc import ABC, abstractmethod
from typing import List

from midhook.bridge.storage import bot_data


class GLBotNotACommand(Exception):
    pass


class GLBotInvalidCommand(Exception):
    pass


class Command(ABC):
    cmd: str
    help: str

    @abstractmethod
    def execute(self, message, arg_list) -> str:
        pass


class Help(Command):
    cmd = "#help"
    help = "#help, 列出所有命令"

    def execute(self, message, arg_list):
        pass


class Hello(Command):
    cmd = "#hi"
    help = "#hi, say hi"

    def execute(self, message, arg_list):
        return "Hello, there!"


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
