import os

from dotenv import load_dotenv

load_dotenv()


class LarkConfig:
    EncryptKey = os.getenv("LARK_ENCRYPT_KEY")
    Verification = os.getenv("LARK_VERIFICATION")
    App_ID = os.getenv("LARK_APP_ID")
    App_Secret = os.getenv("LARK_APP_SECRET")


class GitlabConfig:
    Secret = os.getenv("GITLAB_SECRET")


class GLBotConfig:
    data_dir = "./data/gl_bot"
