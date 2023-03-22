from enum import Enum
from typing import Callable, Dict, List, Tuple


class NotificationType(Enum):
    MRUpdateReviewers = "update_reviewers"
    MRAddComment = "merge_request_add_coment"
    MRApproved = "merge_request_approved"
    MRMerged = "merge_request_merged"


def _at_user(user_id, user_name):
    if user_id:
        return f'<at user_id="{user_id}">{user_name}</at>'

    return f"@{user_name}"


def update_reviewers(mr_url: str, reviewers: List[Tuple[str, str]]) -> str:
    usr_str = " ".join((_at_user(r[0], r[1]) for r in reviewers))
    s = f"以下Merge Request的Reviewers更新为 {usr_str}\n请适时Review\n{mr_url}"
    return s


NotiMessageMaker: Dict[NotificationType, Callable] = {
    # NotificationType.MRReviewers :update_reviewers,
    # NotificationType.MergeReqeustComment :update_reviewers,
    # NotificationType.MergeReqeustApproved :update_reviewers,
    # NotificationType.MergeReqeustMerged :update_reviewers,
}
