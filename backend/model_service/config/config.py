from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    NUM_CLASSES: int

    class Config:
        env_file = ".env"

settings = Settings()
