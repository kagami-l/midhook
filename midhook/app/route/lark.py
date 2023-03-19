from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from midhook.app.route.model import BaseResponse

from midhook.webhooks.lark.security import decrypt_body, verify_signature
from midhook.webhooks.lark.receiver import receiver
from midhook.config import LarkConfig

from typing import Optional

import json
import hashlib

# def gen_signature(timestamp, nonce, encrypt_key):


#     bytes_b1 = (timestamp + nonce + encrypt_key).encode('utf-8')
#     bytes_b = bytes_b1 + body
#     h = hashlib.sha256(bytes_b)
#     signature = h.hexdigest()

async def from_lark(req: Request, 
                    x_lark_request_nonce:Optional[str] = Header(None),
                    x_lark_request_timestamp:Optional[str] = Header(None),
                    x_lark_signature:Optional[str] = Header(None),
                    ):

    data = await req.body()
    body = json.loads(data)

    if not body.get("encrypt"):
        raise HTTPException(detail="Not an encrypt request", status_code=401)
    
    if x_lark_request_timestamp and x_lark_request_nonce and x_lark_signature:
        if not verify_signature(data, x_lark_request_timestamp, x_lark_request_nonce,  x_lark_signature, LarkConfig.EncryptKey):
            raise HTTPException(detail="Invalid signature", status_code=401)

    return

router = APIRouter(dependencies=[Depends(from_lark)])


@router.post("/test_lark")
async def lark_event(req: Request):

    encrypted = await req.json()
    body = decrypt_body(encrypted["encrypt"], LarkConfig.EncryptKey)

    if "challenge" in body:
        # verify lark config
        return {"challenge": body["challenge"]}

    # TODO:
    # 应用收到 HTTP POST 请求后，需要在 3 秒内以 HTTP 200 状态码响应该请求。
    # 否则飞书开放平台认为本次推送失败，
    # 并以 15秒、5分钟、1小时、6小时 的间隔重新推送事件，
    # 最多重试 4 次。
    header, event = receiver.parse_payload(body)
    result = receiver.handle_event(header, event)


    return BaseResponse(result=result)


