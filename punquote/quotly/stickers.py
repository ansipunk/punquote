import aiohttp
import orjson
import pyrogram.types

from .. import config
from .messages import prepare_message


class QuotlyServerError(Exception):
    def __init__(self, *args, error_code: int, error_message: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_code = error_code
        self.error_message = error_message


async def generate_sticker(
    messages: list[pyrogram.types.Message],
    *,
    preserve_media: bool,
) -> str | None:
    messages_to_quote = []

    for message in messages:
        message_to_quote = prepare_message(
            message, preserve_media=preserve_media,
        )

        if message_to_quote:
            messages_to_quote.append(message_to_quote)

    if not messages_to_quote:
        return None

    request_body = {
        "type": "quote",
        "format": "webp",
        "width": 512,
        "height": 512,
        "scale": 2,
        "messages": messages_to_quote,
    }

    async with aiohttp.ClientSession() as client:  # noqa: SIM117
        async with client.post(
            config.quotly.url,
            data=orjson.dumps(request_body),
            headers={"Content-Type": "application/json"},
            params={"botToken": config.telegram.bot_token},
        ) as response:
            response_status = response.status
            response_body = await response.read()

    try:
        response_body = orjson.loads(response_body)
    except orjson.JSONDecodeError:
        response_body = response_body.decode("utf-8")

    if isinstance(response_body, str):
        error_message = (
            "API is down"
            if "cloudflare" in response_body
            else response_body
        )

        raise QuotlyServerError(
            error_code=response_status,
            error_message=error_message,
        )

    if not response_body["ok"]:
        raise QuotlyServerError(
            error_code=response_body["error"]["code"],
            error_message=response_body["error"]["message"],
        )

    return response_body["result"]["image"]
