from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MONGO_URI: str
    MONGO_DB_NAME: str

    OTP_EXPIRE_MINUTES: int = 10
    RESET_PASSWORD_TOKEN_EXPIRY_MINUTES: int
    PREDICTION_EXPIRY_HOURS: int

    ACCESS_SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 3

    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    RESEND_OTP_LIMIT: int = 2

    MAIL_USER: str
    MAIL_PASS: str

    BACKEND_DB_URL: str

    BACKEND_MODEL_URL: str

    FRONTEND_URL: str
    OTP_TOKEN_EXPIRE_MINUTES: int

    class Config:
        env_file = ".env"


settings = Settings()
