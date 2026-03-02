from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    anthropic_api_key: str
    anthropic_model: str = "claude-sonnet-4-6"
    max_file_size_mb: int = 10
    allowed_extensions: list[str] = [".pdf", ".docx"]
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_port: int = 8501
    scenarios_dir: str = "data/scenarios"

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


def get_settings() -> Settings:
    return Settings()
