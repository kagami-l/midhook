from enum import Enum
from typing import List, Tuple

from midhook.bridge.storage import bot_data
from midhook.webhook.lark.sender import MessageSender


class NotificationType(Enum):
    MRUpdateReviewers = "update_reviewers"
    MRAddComment = "merge_request_add_coment"
    MRApproved = "merge_request_approved"
    MRMerged = "merge_request_merged"


def _at_user(user_id, user_name):
    if user_id:
        return f'<at user_id="{user_id}">{user_name}</at>'

    return f"@{user_name}"


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

    content = f"{commenter[1]}评论了以下MR，请相关同事注意查看\n{at_str}\n{mr_url}"

    chat_ids = bot_data.get_chats_of_project(project_id)

    m_sender = MessageSender()
    for chat_id in chat_ids:
        m_sender.send(content, chat_id)

    return "Sent notifications"


def notify_mr_merged(project_id, mr_url, assignee_ids, reviewer_ids):
    lark_users: List[Tuple[str, str]] = bot_data.get_lark_user_from_gitlab_user(
        set(assignee_ids + reviewer_ids)
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
