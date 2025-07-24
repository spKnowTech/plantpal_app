# App configuration
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
load_dotenv()


class ConfigSettings(BaseSettings):
    db_hostname: str
    db_port: str
    db_password: str
    db_name: str
    db_username: str
    secret_key: str
    algorithm: str
    open_ai_key: str
    access_token_expire_minutes: int

    class Config:
        env_file = ".env"


Setting = ConfigSettings()