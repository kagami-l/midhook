from typing import Callable, Dict

from midhook.bridge.gl_bot import GLBot
from midhook.bridge.notification import NotificationType
from midhook.webhook.gitlab.schema import (
    Comment,
    CommentTarget,
    Event,
    EventHandler,
    MergeRequest,
    MergeRequestChanges,
    Payload,
)


class Receiver:
    def __init__(self) -> None:
        self._handlers: Dict[Event, EventHandler] = {}

    @classmethod
    def parse_event(cls, headers) -> Event:
        """
        Parse the event type from the headers.
        """
        try:
            event = Event(headers["x-gitlab-event"])
        except ValueError:
            event = Event.Other
        return event

    def register(self, event_type: Event) -> Callable:
        def decorator(func: Callable):
            self._handlers[event_type] = func
            return func

        return decorator

    def handle_event(self, event: Event, body: dict) -> str:
        event_handler = self._handlers.get(event, None)
        if not event_handler:
            return "Ignore this event"

        payload = Payload.parse_obj(body)
        return event_handler(payload)


receiver = Receiver()


@receiver.register(Event.MergeRequest)
def mr_event_handler(payload: Payload):
    """
    Currently we only care about
    - action: approved / merge / update of reviewers
    - merge request changes: reviewers
    """

    res = "Unsupported event"
    merge_request = MergeRequest.parse_obj(payload.object_attributes)
    project = payload.project

    if merge_request.action == "update":
        changes = MergeRequestChanges.parse_obj(payload.changes)
        if changes.reviewers:
            bot = GLBot()

            res = bot.forward(
                NotificationType.MRUpdateReviewers,
                project.id,
                merge_request,
            )
    if merge_request.action == "merge":
        bot = GLBot()
        res = bot.forward(
            NotificationType.MRMerged,
            project.id,
            merge_request,
        )

    if merge_request.action == "approved":
        bot = GLBot()
        res = bot.forward(
            NotificationType.MRApproved,
            project.id,
            merge_request,
            payload.user.id,
        )

    return res


@receiver.register(Event.Comment)
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
        merge_request,
        payload.user.id,
    )

    return res
