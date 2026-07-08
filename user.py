from os.path import exists

from pyrogram import Client, enums

if exists("./config.py"):
    from config import LOGGER, Config
else:
    from sample_config import LOGGER, Config


class User(Client):
    def __init__(self):
        super().__init__(
            Config.TG_USER_SESSION_NAME,
            api_hash=Config.API_HASH,
            api_id=Config.APP_ID,
            workers=8,
            session_string=Config.TG_USER_SESSION_STRING
        )
        self.LOGGER = LOGGER

    async def start(self, *args, **kwargs):
        await super().start(*args, **kwargs)
        usr_bot_me = await self.get_me()
        self.set_parse_mode(enums.ParseMode.HTML)

        # Populate Pyrogram's peer cache for every chat/channel this account
        # is a member of. Without this, incoming updates for channels the
        # client hasn't resolved yet raise "Peer id invalid" errors because
        # resolve_peer() can only look up peers already in the local cache.
        async for _ in self.get_dialogs():
            pass

        self.LOGGER(__name__).info(
            f"User {usr_bot_me.first_name} (@{usr_bot_me.username})  started!"
        )
        return self, usr_bot_me.id

    async def stop(self, *args):
        await super().stop()
        self.LOGGER(__name__).info("User stopped. Bye.")
