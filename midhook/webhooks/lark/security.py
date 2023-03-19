import hashlib
import base64
from Crypto.Cipher import AES
import json
from typing import Dict

class  AESCipher(object):
    def __init__(self, key):
        self.bs = AES.block_size
        self.key=hashlib.sha256(AESCipher.str_to_bytes(key)).digest()
    @staticmethod
    def str_to_bytes(data):
        u_type = type(b"".decode('utf8'))
        if isinstance(data, u_type):
            return data.encode('utf8')
        return data
    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]
    def decrypt(self, enc):
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return  self._unpad(cipher.decrypt(enc[AES.block_size:]))
    def decrypt_string(self, enc):
        enc = base64.b64decode(enc)
        return  self.decrypt(enc).decode('utf8')


def decrypt_body(cipher_text: str, encrypt_key: str) -> Dict:
    """
    Return plain text
    """
    cipher = AESCipher(encrypt_key)
    content = cipher.decrypt_string(cipher_text)
    return json.loads(content)


def verify_signature(body: bytes, timestamp, nonce, signature, encrypt_key) -> bool:
    bytes_b1 = (timestamp + nonce + encrypt_key).encode('utf-8')
    bytes_b = bytes_b1 + body
    h = hashlib.sha256(bytes_b)
    return h.hexdigest() == signature

