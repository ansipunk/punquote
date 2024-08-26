import pydantic_settings


class DatabaseConfig(pydantic_settings.BaseSettings):
    url: str = ":memory:"

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_prefix="PQ_DATABASE_",
        extra="ignore",
    )


class QuotlyConfig(pydantic_settings.BaseSettings):
    url: str = "https://bot.lyo.su/quote/generate"

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_prefix="PQ_QUOTLY_",
        extra="ignore",
    )


class TelegramConfig(pydantic_settings.BaseSettings):
    session_name: str = "punquote_bot"
    bot_token: str
    api_id: int
    api_hash: str

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_prefix="PQ_TELEGRAM_",
        extra="ignore",
    )


database = DatabaseConfig()
quotly = QuotlyConfig()
telegram = TelegramConfig()
