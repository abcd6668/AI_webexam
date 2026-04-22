from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    SECRET_KEY: str = "change-me"
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    DATABASE_URL: str = "sqlite:///./exam.db"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480


settings = Settings()
