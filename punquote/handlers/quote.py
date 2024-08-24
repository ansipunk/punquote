import base64
import contextlib
import io

import pyrogram
import pyrogram.enums
import pyrogram.types

from .. import quotly


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


def cancel_chat_action(func):
    async def wrapped(client, message):
        try:
            await func(client, message)
        except Exception:
            await message.reply_chat_action(pyrogram.enums.ChatAction.CANCEL)
            raise

    return wrapped


@cancel_chat_action
async def quote_handler(
    client: pyrogram.Client,
    message: pyrogram.types.Message,
):
    if not message.reply_to_message_id:
        await message.reply("Command must be sent as a reply to a message")
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

    await message.reply_chat_action(pyrogram.enums.ChatAction.CHOOSE_STICKER)

    try:
        sticker_base64 = await quotly.generate_sticker(
            messages_to_quote,
            preserve_media=preserve_media,
        )
    except quotly.QuotlyServerError as e:
        await message.reply(
            f"Quotly server error. Code {e.error_code}: {e.error_message}",
        )
        raise e
    except Exception as e:
        await message.reply(f"Failed to generate quote: {e}")
        raise e

    if not sticker_base64:
        return

    sticker_bytes = base64.b64decode(sticker_base64)
    sticker = io.BytesIO(sticker_bytes)
    sticker.name = "sticker.webp"
    await message.reply_sticker(sticker)
