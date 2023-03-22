from enum import Enum
from typing import Callable, Dict, List, Optional

from pydantic import BaseModel, Extra, validator


class Event(Enum):
    # Currently only support 2 events
    Comment = "Note Hook"
    MergeRequest = "Merge Request Hook"
    Other = "Other"


class GitlabBase(BaseModel):
    class Config:
        extra = Extra.allow


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


EventHandler = Callable[[Event], str]
