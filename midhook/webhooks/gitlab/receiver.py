from pydantic import BaseModel, Extra, validator
from enum import Enum
from typing import List, Optional, Dict, Tuple, Callable
from midhook.bridge.gitlab_lark import GLBot
from midhook.bridge.notification import NotificationType


class WebhookEvent(Enum):
    # Currently only support 2 events
    Comment = "Note Hook"
    MergeRequest = "Merge Request Hook"
    Other = "Other"


class GitlabBase(BaseModel):
    class Config:
        extra = Extra.allow


class User(GitlabBase):
    id: str
    name: str
    email: str


class Project(GitlabBase):
    id: str
    name: str
    url: str


class Repository(GitlabBase):
    name: str
    url: str


class User(GitlabBase):
    id: str
    name: str
    username: str


class MergeRequestChanges(GitlabBase):
    reviewers: Optional[List[User]]

    @validator("reviewers", pre=True)
    def only_current_reviewers(cls, value):
        return [User.parse_obj(usr) for usr in value.get("current", [])]


class MergeRequest(GitlabBase):
    author_id: str
    iid: str
    title: str
    url: str
    target_project_id: str
    assignee_ids: Optional[List[str]]
    reviewer_ids: Optional[List[str]]
    action: Optional[str]
    detailed_merge_status: Optional[str]


class Payload(GitlabBase):
    project: Project
    user: Optional[User]
    object_attributes: Optional[Dict]
    changes: Optional[Dict]


class CommentTarget(Enum):
    commit = "Commit"
    merge_request = "MergeRequest"
    issue = "Issue"
    snippet = "Snippet"


class Comment(GitlabBase):
    author_id: str
    note: str
    noteable_type: str


EventHandler = Callable[[WebhookEvent], str]


class Receiver:
    def __init__(self) -> None:
        self._handlers: Dict[WebhookEvent, EventHandler] = {}

    @classmethod
    def parse_event(cls, headers) -> WebhookEvent:
        """
        Parse the event type from the headers.
        """
        try:
            event = WebhookEvent(headers["x-gitlab-event"])
        except ValueError:
            event = WebhookEvent.Other
        return event

    def register(self, event_type: WebhookEvent) -> Callable:
        def decorator(func: Callable):
            self._handlers[event_type] = func
            return func

        return decorator

    def handle_event(self, event: WebhookEvent, body: dict) -> str:
        event_handler = self._handlers.get(event, None)
        if not event_handler:
            return "Ignore this event"

        payload = Payload.parse_obj(body)
        return event_handler(payload)


receiver = Receiver()


@receiver.register(WebhookEvent.MergeRequest)
def mr_event_handler(payload: Payload):
    """
    Currently we only care about
    - action: approved / merge / update of reviewers
    - merge request changes: reviewers
    """

    res = "Unsupported event"
    merge_request = MergeRequest.parse_obj(payload.object_attributes)
    project = payload.project
    if merge_request.action in ["approval", "approved", "merge"]:
        pass

    if merge_request.action == "update":
        changes = MergeRequestChanges.parse_obj(payload.changes)
        if changes.reviewers:
            bot = GLBot()

            res = bot.forward(
                NotificationType.MRUpdateReviewers,
                project.id,
                merge_request.url,
                merge_request.reviewer_ids,
            )
    if merge_request.action == "merge":
        bot = GLBot()
        res = bot.forward(
            NotificationType.MRMerged,
            project.id,
            merge_request.url,
            merge_request.assignee_ids,
            merge_request.reviewer_ids,
        )

    if merge_request.action == "approved":
        bot = GLBot()
        res = bot.forward(
            NotificationType.MRApproved,
            project.id,
            merge_request.url,
            payload.user.id,
            merge_request.assignee_ids or [merge_request.author_id],
        )

    return res


@receiver.register(WebhookEvent.Comment)
def comment_handler(payload: Payload):
    """
    Currently we only care about comment on a merge request with reviewers.
    """
    res = "Unsupported comment event"

    comment = Comment.parse_obj(payload.object_attributes)

    if comment.noteable_type != CommentTarget.merge_request.value:
        # not a comment on a merge request
        return res

    merge_request = MergeRequest.parse_obj(payload.merge_request)
    if not merge_request.reviewer_ids:
        # not a merge request with reviewers
        return "No reviewers"

    bot = GLBot()
    res = bot.forward(
        NotificationType.MRAddComment,
        merge_request.target_project_id,
        merge_request.url,
        payload.user.id,
        merge_request.assignee_ids,
        merge_request.reviewer_ids,
    )

    return res
