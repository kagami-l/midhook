import os
import pickle
from typing import Any, List, Tuple

import lmdb

from midhook.config import GLBotConfig


class BaseDB:
    def __init__(self, data_dir: str) -> None:
        os.makedirs(data_dir, exist_ok=True)
        self._db_dir = data_dir
        self._env = lmdb.open(self._db_dir, subdir=True, max_dbs=1)

    @property
    def db_file(self) -> str:
        return self._db_file

    @classmethod
    def _key_to_bytes(self, key: str) -> bytes:
        return key.encode()

    @classmethod
    def _value_to_bytes(self, value: Any) -> bytes:
        try:
            return pickle.dumps(value)
        except Exception:
            raise Exception(f"Failed to pickle value: {value}")

    @classmethod
    def _key_from_bytes(self, key: bytes) -> str:
        return key.decode()

    @classmethod
    def _value_from_bytes(self, value: bytes) -> Any:
        try:
            return pickle.loads(value)
        except Exception:
            raise Exception(f"Failed to unpickle value: {value}")

    def put(self, key: str, value: Any):
        key_b = self._key_to_bytes(key)
        val_b = self._value_to_bytes(value)

        with self._env.begin(write=True) as txn:
            txn.put(key_b, val_b)

    def get(self, key: str, default: Any = None) -> Any:
        key_b = self._key_to_bytes(key)
        with self._env.begin() as txn:
            val_b = txn.get(key_b, None)
            if val_b is None:
                return default

            value = self._value_from_bytes(val_b)
            value = default if value is None else value
            return value

    def keys_with_prefix(self, prefix: str):
        prefix_b = self._key_to_bytes(prefix)

        with self._env.begin() as txn:
            cursor = txn.cursor()
            cursor.set_range(prefix_b)

            for key, value in cursor:
                if not key.startswith(prefix_b):
                    return
                yield self._key_from_bytes(key)

    def delete(self, key: str):
        key_b = self._key_to_bytes(key)
        with self._env.begin(write=True) as txn:
            txn.delete(key_b)

    def drop(self):
        with self._env.begin(write=True) as txn:
            db = self._env.open_db()
            txn.drop(db)
        self._env.sync(True)

    def iterate(self, prefix: str = None):
        with self._env.begin() as txn:
            cursor = txn.cursor()

            if prefix is not None:
                prefix_b = self._key_to_bytes(prefix)
                cursor.set_range(prefix_b)

            for key, value in cursor:
                if not key.startswith(prefix_b):
                    return
                yield self._key_from_bytes(key), self._value_from_bytes(value)


class BotData(BaseDB):
    # mapping of gitlab project id to lark chat ids
    _project_chat_prefix = "PROJ-CHAT_"
    # mapping of gitlab user id to lark user id & name
    _user_account_prefix = "USER-ACCT_"

    def __init__(self) -> None:
        db_file = GLBotConfig.data_dir
        super().__init__(db_file)

    def _proj_key(self, project_id: str) -> str:
        return f"{self._project_chat_prefix}{project_id}"

    def _user_key(self, user_id: str) -> str:
        return f"{self._user_account_prefix}{user_id}"

    def set_project_to_chat(self, project_id: str, chat_id: str):
        key = self._proj_key(project_id)

        chat_ids = self.get(key, [])
        if chat_id not in chat_ids:
            chat_ids.append(chat_id)

        self.put(key, chat_ids)

    def get_chats_of_project(self, project_id: str) -> List[str]:
        key = self._proj_key(project_id)
        return self.get(key, [])

    def remove_project_from_chat(self, project_id: str, chat_id: str):
        key = self._proj_key(project_id)

        chat_ids = self.get(key, [])
        if chat_id in chat_ids:
            chat_ids.remove(chat_id)

        self.put(key, chat_ids)

    def remove_all_projects_chats(self):
        keys = self.keys_with_prefix(self._project_chat_prefix)
        for key in keys:
            self.delete(key)

    def get_chat_projects(self, chat_id: str) -> List[str]:
        projects = set()
        for key, value in self.iterate(self._project_chat_prefix):
            if chat_id in value:
                projects.add(key.replace(self._project_chat_prefix, ""))
        return projects

    def set_user_account(self, user_id: str, lark_id: str, lark_name: str):
        key = self._user_key(user_id)

        self.put(key, (lark_id, lark_name))

    def get_lark_user_from_gitlab_user(
        self, user_ids: List[str]
    ) -> List[Tuple[str, str]]:
        values = []
        for user_id in user_ids:
            key = self._user_key(user_id)
            val = self.get(key, ("", f"gitlab_user_{user_id}"))
            values.append(val)
        return values

    def get_all_user_accounts(self) -> List[Tuple[str, str, str]]:
        # gitlab_user_id, lark_user_id, lark_user_name
        accounts = []
        for key, value in self.iterate(self._user_account_prefix):
            gitlab_user_id = key.replace(self._user_account_prefix, "")
            lark_user_id, lark_user_name = value
            accounts.append((gitlab_user_id, lark_user_id, lark_user_name))
        return accounts

    def remove_lark_user(self, lark_user_id: str):
        for key, value in self.iterate(self._user_account_prefix):
            if value[0] == lark_user_id:
                self.delete(key)
                break


bot_data = BotData()
