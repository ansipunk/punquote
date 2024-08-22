import base64
import contextlib
import io
import json

import httpx
import pyrogram
import pyrogram.filters
import pyrogram.types

from .. import config


class QuotlyServerError(Exception):
    def __init__(self, *args, error_code: int, error_message: str, **kwargs):
        super().__init__(*args, **kwargs)
        self.error_code = error_code
        self.error_message = error_message


def _parse_command_arguments(command: str) -> tuple[int, bool, bool]:
    preserve_replies = False
    preserve_media = False
    message_count = 0

    arguments = command.split(" ")

    for argument in arguments:
        if argument == "r":
            preserve_replies = True
        elif argument == "m":
            preserve_media = True
        else:
            with contextlib.suppress(ValueError):
                message_count = int(argument)

    return message_count, preserve_replies, preserve_media


def _get_start_and_end_message_ids(
    quoted_message_id: int,
    message_count: int,
) -> tuple[int, int]:
    message_reverse = False

    if message_count == 0:
        message_count = 1
    elif message_count < 0:
        message_reverse = True
        message_count = abs(message_count)

    if message_count > 10:
        message_count = 10

    if message_reverse:
        message_start_id = quoted_message_id - (message_count - 1)
        message_end_id = quoted_message_id
    else:
        message_start_id = quoted_message_id
        message_end_id = quoted_message_id + (message_count - 1)

    return message_start_id, message_end_id


def _prepare_message_author_for_quotly_api(author: pyrogram.types.User) -> dict:
    name = author.first_name
    if author.last_name:
        name = f"{name} {author.last_name}"

    prepared_author = {
        "id": 1,
        "name": name,
    }

    if author.photo:
        prepared_author["photo"] = {
            "small_file_id": author.photo.small_file_id,
            "small_file_unique_id": author.photo.small_photo_unique_id,
            "big_file_id": author.photo.big_file_id,
            "big_file_unique_id": author.photo.big_photo_unique_id,
        }

    return prepared_author


def _prepare_message_media_for_quotly_api(
    message: pyrogram.types.Message,
    *,
    preserve_media: bool,
) -> tuple[str | None, dict | None]:
    media = None
    media_type = None

    if (
        (
            message.sticker
            and not message.sticker.is_animated
            and not message.sticker.is_video
        ) or preserve_media
    ):
        content = None

        if message.sticker:
            content = message.sticker
            media_type = "sticker"
        if message.photo:
            content = message.photo
        elif message.video and message.video.thumbs:
            content = message.video.thumbs[0]
        elif message.animation and message.animation.thumbs:
            content = message.animation.thumbs[0]

        if content:
            media = [{
                "file_id": content.file_id,
                "file_size": content.file_size,
                "height": content.height,
                "width": content.width,
            }]
            media_type = media_type if media_type else "photo"

    return media_type, media


def _prepare_message_for_quotly_api(
    message: pyrogram.types.Message,
    *,
    preserve_media: bool,
) -> dict | None:
    author = _prepare_message_author_for_quotly_api(message.from_user)
    media_type, media = _prepare_message_media_for_quotly_api(
        message,
        preserve_media=preserve_media,
    )

    text = None
    if message.text:
        text = message.text

    if not text and not media:
        return None

    prepared_message = {
        "chatId": 1,
        "avatar": "photo" in author,
        "from": author,
    }

    if text:
        prepared_message["text"] = text

    if media and media_type:
        prepared_message["media"] = media
        prepared_message["mediaType"] = media_type

    if message.reply_to_message:
        prepared_message["replyMessage"] = _prepare_message_media_for_quotly_api(
            message,
            preserve_media=preserve_media,
        )

    return prepared_message


async def _get_base64_sticker_from_quotly_api(
    messages: list[pyrogram.types.Message],
    *,
    preserve_media: bool,
) -> str | None:
    messages_to_quote = []

    for message in messages:
        message_to_quote = _prepare_message_for_quotly_api(
            message,
            preserve_media=preserve_media,
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
        "messages": messages_to_quote,
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            config.quotly.url,
            json=request_body,
            params={"botToken": config.telegram.bot_token},
            headers={"Content-Type": "application/json"},
        )

    try:
        response_body = response.json()
    except json.JSONDecodeError:
        error_message = (
            "API is down"
            if "cloudflare" in response.text
            else response.text
        )

        raise QuotlyServerError(
            error_code=response.status_code,
            error_message=error_message,
        )

    if not response_body["ok"]:
        raise QuotlyServerError(
            error_code=response_body["error"]["code"],
            error_message=response_body["error"]["message"],
        )

    return response_body["result"]["image"]


async def quote_handler(
    client: pyrogram.Client,
    message: pyrogram.types.Message,
):
    if not message.reply_to_message_id:
        await client.send_message(
            chat_id=message.chat.id,
            text="Command must be sent as a reply to a message",
            reply_to_message_id=message.id,
        )
        return

    message_count, preserve_replies, preserve_media = _parse_command_arguments(
        command=message.text,
    )

    message_start_id, message_end_id = _get_start_and_end_message_ids(
        quoted_message_id=message.reply_to_message_id,
        message_count=message_count,
    )

    messages_to_quote = await client.get_messages(
        chat_id=message.chat.id,
        message_ids=range(message_start_id, message_end_id + 1),
        replies=1 if preserve_replies else 0,
    )

    if not messages_to_quote:
        return

    try:
        sticker_base64 = await _get_base64_sticker_from_quotly_api(
            messages_to_quote,
            preserve_media=preserve_media,
        )
    except QuotlyServerError as e:
        await client.send_message(
            chat_id=message.chat.id,
            text=f"Quotly server error. Code {e.error_code}: {e.error_message}",
            reply_to_message_id=message.id,
        )
        raise e
    except Exception as e:
        await client.send_message(
            chat_id=message.chat.id,
            text=f"Failed to generate quote: {e}",
            reply_to_message_id=message.id,
        )
        raise e

    sticker_bytes = base64.b64decode(sticker_base64)
    sticker = io.BytesIO(sticker_bytes)
    sticker.name = "sticker.webp"

    await client.send_sticker(
        chat_id=message.chat.id,
        sticker=sticker,
        reply_to_message_id=message.id,
    )
