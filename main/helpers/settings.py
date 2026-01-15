import os
from dotenv import load_dotenv
from main.helpers.enums.dot_env import DotEnvEnum


class Settings:
    @staticmethod
    def get(hash: DotEnvEnum) -> str:
        load_dotenv()
        return os.getenv(hash.value.upper(), "")
