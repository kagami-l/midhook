import json
import uuid
from datetime import datetime, timedelta

import httpx

from midhook.config import LarkConfig


class Sender:
    app_id = LarkConfig.App_ID
    app_secret = LarkConfig.App_Secret

    _tenant_access_token = None
    _token_expires_at: datetime = None

    def _get_token(self):
        if self._tenant_access_token and self._token_expires_at > datetime.now():
            return self._tenant_access_token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        headers = {"Content-Type": "application/json; charset=utf-8"}
        data = {"app_id": self.app_id, "app_secret": self.app_secret}

        response = httpx.post(url, headers=headers, json=data)
        res = response.json()

        self._tenant_access_token = res["tenant_access_token"]
        expire = int(res["expire"]) - 30  # 30s for safety
        self._token_expires_at = datetime.now() + timedelta(seconds=expire)

        return self._tenant_access_token


class MessageSender(Sender):
    def _get_url(self):
        return "https://open.feishu.cn/open-apis/im/v1/messages"

    def send(self, content: str, receive_id: str, receive_id_type: str = "chat_id"):
        with httpx.Client() as client:
            url = self._get_url()
            token = self._get_token()
            headers = {"Content-Type": "string", "Authorization": f"Bearer {token}"}

            params = {"receive_id_type": receive_id_type}
            data = {
                "content": json.dumps({"text": content}),
                "receive_id": receive_id,
                "msg_type": "text",
                # "uuid": uuid.uuid4().hex,
            }
            response = client.post(url, headers=headers, params=params, json=data)

            res = response.json()


class ReplySender(Sender):
    def _get_url(self, message_id):
        return f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"

    def send_reply(self, message_id, content):
        with httpx.Client() as client:
            url = self._get_url(message_id)
            token = self._get_token()
            headers = {"Content-Type": "string", "Authorization": f"Bearer {token}"}

            data = {
                "content": json.dumps({"text": content}),
                "msg_type": "text",
                # "uuid": uuid.uuid4().hex,
            }
            response = client.post(url, headers=headers, json=data)
            res = response.json()
