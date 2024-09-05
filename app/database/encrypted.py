import os

from cryptography.fernet import Fernet
from dotenv import load_dotenv
from sqlalchemy import TypeDecorator, String

load_dotenv()

key = os.getenv("DATABASE_ENCRYPTION_KEY")

if key:
    cipher_suite = Fernet(key)


class EncryptedType(TypeDecorator):
    impl = String

    def process_bind_param(self, value, dialect):
        if value is not None:
            value = value.encode("utf-8")
            encrypted_value = cipher_suite.encrypt(value)
            return encrypted_value.decode("utf-8")
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = value.encode("utf-8")
            decrypted_value = cipher_suite.decrypt(value)
            return decrypted_value.decode("utf-8")
        return value
