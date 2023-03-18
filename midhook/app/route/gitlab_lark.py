
from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter()


class Response(BaseModel):
    result: str

# @router.get("/gitlab_lark")
@router.post("/test_hook", response_model=Response)
def gitlab_lark(req: Request):
    print(req)

    return Response(result="okok")
    