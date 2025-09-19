from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    MONGO_DB_NAME: str = "plant_app"

    OTP_EXPIRE_MINUTES: int = 10
    RESET_PASSWORD_TOKEN_EXPIRY_MINUTES: int

    class Config:
        env_file = ".env"

settings = Settings()
