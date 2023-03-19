import base64
import datetime
import hashlib
import hmac

import httpx
from pydantic import BaseModel


class FContent(BaseModel):
    text: str


class FRequest(BaseModel):
    timestamp: int
    sign: str
    content: FContent
    msg_type: str = "text"


class Sender:
    def __init__(self, hook, sec) -> None:
        self.hook = hook
        self.sec = sec

    def gen_sign(self, timestamp):
        # Concatenate timestamp and secret
        string_to_sign = f"{timestamp}\n{self.sec}"
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
        ).digest()

        # Encode the result with Base64
        sign = base64.b64encode(hmac_code).decode("utf-8")

        return sign

    def send_text(self, text):
        timestamp = int(datetime.datetime.now().timestamp())
        sign = self.gen_sign(timestamp)

        content = FContent(text=text)
        request = FRequest(
            timestamp=timestamp, sign=sign, content=content, msg_type="text"
        )

        r = httpx.post(self.hook, data=request.json())

