
from midhook.webhook.lark.sender import Sender
import httpx

class GetBotInfo(Sender):

    def _get_url(self):
        return "https://open.feishu.cn/open-apis/bot/v3/info"

    def get(self):
        url = self._get_url()
        token = self._get_token()
        headers = {"Content-Type": "string", "Authorization": f"Bearer {token}"}

        res = httpx.get(url, headers=headers)
        return res.json()


if __name__ == "__main__":
    bot_info = GetBotInfo()
    print(bot_info.get())