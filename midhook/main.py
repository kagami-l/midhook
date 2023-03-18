
from midhook.config import FeishuConfig
from midhook.webhooks.feishu import Sender

def main():
    feishu = Sender(FeishuConfig.HOOK, FeishuConfig.SECRET)
    feishu.send_text("a message from gfbot")


if __name__ == "__main__":
    main()
