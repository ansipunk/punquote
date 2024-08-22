import pydantic_settings


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
        env_prefix="PQ_",
        extra="ignore",
    )


quotly = QuotlyConfig()
telegram = TelegramConfig()
