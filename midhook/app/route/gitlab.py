from fastapi import APIRouter, Depends, Header, HTTPException, Request

from midhook.app.route.model import BaseResponse
from midhook.config import GitlabConfig
from midhook.webhooks.gitlab.receiver import WebhookEvent, receiver


def from_gitlab(
    x_gitlab_token: str = Header(...),
    x_gitlab_event: str = Header(...),
):
    """ """
    if x_gitlab_token != GitlabConfig.SECRET:
        raise HTTPException(detail="Not allowed", status_code=401)


router = APIRouter(dependencies=[Depends(from_gitlab)])


@router.post("/gitlab_hook", response_model=BaseResponse)
async def gitlab_lark(req: Request):
    headers = req.headers
    event = receiver.parse_event(headers)
    body = await req.json()

    res = receiver.handle_event(event, body)

    return BaseResponse(result=res)
