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
    open_ai_model: str
    embedding_model: str
    embedding_dim: int
    gallery_dir: str
    thumbnail_dir: str
    access_token_expire_minutes: int = 720  # 12 hours default

    class Config:
        env_file = ".env"


Setting = ConfigSettings()