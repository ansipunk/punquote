import pyrogram
import pyrogram.filters
import pyrogram.handlers

from . import config
from . import handlers


def get_bot() -> pyrogram.Client:
    app = pyrogram.Client(
        name=config.telegram.session_name,
        api_id=config.telegram.api_id,
        api_hash=config.telegram.api_hash,
        bot_token=config.telegram.bot_token,
    )

    app.add_handler(pyrogram.handlers.MessageHandler(
        handlers.quote_handler,
        pyrogram.filters.command(["q"]),
    ))

    return app
