import typing

import aiosqlite

from . import config

_session: aiosqlite.Connection | None = None


class DatabaseNotConnectedError(Exception):
    pass


async def connect():
    global _session

    if not _session:
        _session = await aiosqlite.connect(config.database.url)


async def disconnect():
    global _session

    if _session:
        await _session.close()
        _session = None


def _get_session() -> aiosqlite.Connection:
    global _session

    if not _session:
        raise DatabaseNotConnectedError

    return _session


async def migrate():
    async with _get_session() as session:
        await session.execute("""
            CREATE TABLE IF NOT EXISTS stickersets (
                chat_id         INTEGER PRIMARY KEY,
                stickerset_name TEXT
            )
        """)
        await session.commit()


async def execute(
    query: str,
    parameters: typing.Iterable[typing.Any] | None = None,
) -> aiosqlite.Cursor:
    session = _get_session()
    return session.execute(query, parameters)
