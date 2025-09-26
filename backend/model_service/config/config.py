from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGO_URI: str
    MONGO_DB_NAME: str
    
    NUM_CLASSES: int

    class Config:
        env_file = ".env"

settings = Settings()
