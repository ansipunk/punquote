import pyrogram.types

CHAT_TYPES = {
    pyrogram.enums.ChatType.PRIVATE: "private",
    pyrogram.enums.ChatType.BOT: "bot",
    pyrogram.enums.ChatType.GROUP: "group",
    pyrogram.enums.ChatType.SUPERGROUP: "supergroup",
    pyrogram.enums.ChatType.CHANNEL: "channel",
}

ENTITY_TYPES = {
    pyrogram.enums.MessageEntityType.MENTION: "mention",
    pyrogram.enums.MessageEntityType.HASHTAG: "hashtag",
    pyrogram.enums.MessageEntityType.CASHTAG: "cashtag",
    pyrogram.enums.MessageEntityType.BOT_COMMAND: "bot_command",
    pyrogram.enums.MessageEntityType.URL: "url",
    pyrogram.enums.MessageEntityType.EMAIL: "email",
    pyrogram.enums.MessageEntityType.PHONE_NUMBER: "phone_number",
    pyrogram.enums.MessageEntityType.BOLD: "bold",
    pyrogram.enums.MessageEntityType.ITALIC: "italic",
    pyrogram.enums.MessageEntityType.UNDERLINE: "underline",
    pyrogram.enums.MessageEntityType.STRIKETHROUGH: "strikethrough",
    pyrogram.enums.MessageEntityType.SPOILER: "spoiler",
    pyrogram.enums.MessageEntityType.CODE: "code",
    pyrogram.enums.MessageEntityType.PRE: "pre",
    pyrogram.enums.MessageEntityType.BLOCKQUOTE: "blockquote",
    pyrogram.enums.MessageEntityType.TEXT_LINK: "text_link",
    pyrogram.enums.MessageEntityType.TEXT_MENTION: "text_mention",
    pyrogram.enums.MessageEntityType.BANK_CARD: "bank_card",
    pyrogram.enums.MessageEntityType.CUSTOM_EMOJI: "custom_emoji",
    pyrogram.enums.MessageEntityType.UNKNOWN: "unknown",
}


def _prepare_author(message: pyrogram.types.Message) -> dict:
    if message.forward_sender_name:
        return {
            "id": 1,
            "name": message.forward_sender_name,
            "type": "private",
        }

    prepared_author = {}

    if message.forward_from:
        author = message.forward_from
    elif message.forward_from_chat:
        author = message.forward_from_chat
        prepared_author["type"] = CHAT_TYPES[message.forward_from_chat.type]
    else:
        author = message.from_user

    if "type" not in prepared_author:
        prepared_author["type"] = "bot" if author.is_bot else "private"

    name = author.first_name
    if author.last_name:
        name = f"{name} {author.last_name}"

    prepared_author["id"] = author.id
    prepared_author["name"] = name

    if author.photo:
        prepared_author["photo"] = {
            "small_file_id": author.photo.small_file_id,
            "small_file_unique_id": author.photo.small_photo_unique_id,
            "big_file_id": author.photo.big_file_id,
            "big_file_unique_id": author.photo.big_photo_unique_id,
        }

    return prepared_author


def _prepare_media(
    message: pyrogram.types.Message,
    *,
    preserve_media: bool,
) -> tuple[str | None, dict | None]:
    media = None
    media_type = None

    if message.sticker or preserve_media:
        content = None

        if message.sticker:
            sticker = message.sticker

            if not sticker.is_animated and not sticker.is_video:
                content = sticker
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


def _prepare_entities(
    entities: list[pyrogram.types.MessageEntity] | None,
) -> list[dict] | None:
    if not entities:
        return None

    return [
        {
            "type": ENTITY_TYPES[entity.type],
            "offset": entity.offset,
            "length": entity.length,
            "url": entity.url,
            "language": entity.language,
            "custom_emoji_id": entity.custom_emoji_id,
        }
        for entity in entities if entity
    ]


def prepare_message(
    message: pyrogram.types.Message,
    *,
    preserve_media: bool,
) -> dict | None:
    if not message or not message.from_user:
        return None

    author = _prepare_author(message)
    media_type, media = _prepare_media(message, preserve_media=preserve_media)

    text = None
    if message.text:
        text = message.text

    if not text and not media:
        return None

    prepared_message = {
        "chatId": message.chat.id,
        "avatar": True,
        "from": author,
        "name": author["name"],
    }

    if text:
        prepared_message["text"] = text
        prepared_message["entities"] = _prepare_entities(
            message.entities,
        )

    if message.caption:
        prepared_message["text"] = message.caption
        prepared_message["entities"] = _prepare_entities(
            message.caption_entities,
        )

    if media and media_type:
        prepared_message["media"] = media
        prepared_message["mediaType"] = media_type

    if message.reply_to_message:
        prepared_message["replyMessage"] = prepare_message(
            message.reply_to_message,
            preserve_media=preserve_media,
        )

    return prepared_message
