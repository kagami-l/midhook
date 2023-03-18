import os
from dotenv import load_dotenv


load_dotenv()

class FeishuConfig:
    SECRET = os.getenv("FEISHU_SECRET")
    HOOK = os.getenv("FEISHU_HOOK")
