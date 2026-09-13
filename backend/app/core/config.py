from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://127.0.0.1:5173"

    client_id: str
    client_secret: str
    redirect_uri: str = "http://127.0.0.1:8000/callback"

    frontend_url: str = "http://127.0.0.1:5173"
    redis_host: str = "localhost"
    redis_port: int = 6379


    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
