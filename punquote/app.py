import logging

import mode
import pyrogram
import pyrogram.filters
import pyrogram.handlers

from . import config
from . import handlers


def get_bot() -> pyrogram.Client:
    bot = pyrogram.Client(
        name=config.telegram.session_name,
        api_id=config.telegram.api_id,
        api_hash=config.telegram.api_hash,
        bot_token=config.telegram.bot_token,
    )

    bot.add_handler(pyrogram.handlers.MessageHandler(
        handlers.quote_handler,
        pyrogram.filters.command(["q"]),
    ))

    for name, logger in logging.root.manager.loggerDict.items():
        if name.startswith("pyrogram") and isinstance(logger, logging.Logger):
            logger.setLevel(logging.WARNING)

    return bot


class PunquoteService(mode.Service):
    bot: pyrogram.Client | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot = get_bot()

    async def on_start(self) -> None:
        await self.bot.start()
        self._log_mundane("Started")

    async def on_stop(self) -> None:
        await self.bot.stop()
